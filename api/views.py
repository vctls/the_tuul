import json
import tempfile
from pathlib import Path
import zipfile
import os

import structlog

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import StreamingHttpResponse
from django.core.files import File
from django.views.generic.base import TemplateView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework import status

from karaoke import music_separation
from helpers import youtube_helper, zip_helper, cloud_storage

logger = structlog.get_logger(__name__)


def streamed_response(file_path: Path) -> StreamingHttpResponse:
    """Return a streaming response for the given file path."""
    f = file_path.open("rb")

    def streaming_content():
        while True:
            data = f.read(1024 * 1024)
            if not data:
                break
            yield data

    return StreamingHttpResponse(streaming_content=streaming_content())


class Index(TemplateView):
    template_name = "index.html"


class SeparateTrack(APIView):
    def post(self, request: Request, format: str | None = None) -> Response:
        """Return a zip containing vocal and accompaniment splits of songFile"""
        song_file = request.data.get("songFile")
        model_name = request.data.get("modelName")
        logger.info(
            "separate_tracks",
            song_size=len(song_file),
            model_name=model_name,
        )

        # Check if we can fetch from cache
        if settings.SEPARATED_TRACKS_BUCKET:
            cache_hash = cloud_storage.get_cache_hash(model_name, song_file)
            logger.info("checking_cache", cache_hash=cache_hash)

            # Try to fetch from cache
            cached_zip_path = cloud_storage.fetch_from_cache(cache_hash)
            if cached_zip_path:
                logger.info(
                    "serving_from_cache", cache_hash=cache_hash, path=cached_zip_path
                )
                return streamed_response(cached_zip_path)

        # If no cache hit or caching is disabled, proceed with normal track separation
        with tempfile.TemporaryDirectory() as song_files_dir:
            song_files_dir_path = Path(song_files_dir)
            song_file_path = self.setup_song_files_dir(song_files_dir, song_file)
            accompaniment_path, vocal_path = music_separation.split_song(
                song_file_path, song_files_dir_path, model_name=model_name
            )
            zip_path = zip_helper.create_zip_file(
                song_files_dir_path / "split_song.zip",
                [(accompaniment_path, "accompaniment.wav"), (vocal_path, "vocals.wav")],
            )
            logger.info("zip_complete", path=zip_path)

            # Upload to cache if caching is enabled
            if settings.SEPARATED_TRACKS_BUCKET:
                cache_hash = cloud_storage.get_cache_hash(model_name, song_file)
                cloud_storage.upload_to_cache(cache_hash, zip_path)

            return streamed_response(zip_path)

    def setup_song_files_dir(self, files_dir: str, song_file: File) -> Path:
        """Copy song file to the temp dir.

        Return song file path.
        """
        fs = FileSystemStorage(files_dir)
        song_file_name = fs.save(song_file.name, content=song_file)
        return Path(fs.location, song_file_name)


class DownloadYouTubeVideo(APIView):
    """
    Download a YouTube video as audio and video streams and return them as a zip.
    """

    def get(self, request: Request, format: str | None = None) -> Response:
        """Return a zip containing vocal and accompaniment splits of songFile, and song metadata"""
        youtube_url = request.query_params.get("url")
        logger.info(
            "download_youtube_video",
            youtube_url=youtube_url,
            request=request.query_params,
        )
        if not youtube_url:
            return Response({"error": "No url provided."})
        with tempfile.TemporaryDirectory() as song_files_dir:
            song_files_dir_path = Path(song_files_dir)

            metadata, audio_path, video_path = youtube_helper.get_youtube_streams(
                youtube_url, song_files_dir_path
            )
            logger.info("metadata", metadata=metadata)
            (song_files_dir_path / "metadata.json").write_text(json.dumps(metadata))
            zip_path = zip_helper.create_zip_file(
                song_files_dir_path / "youtube_video.zip",
                [
                    (audio_path, "audio.mp4"),
                    (video_path, "video.mp4"),
                    (song_files_dir_path / "metadata.json", "metadata.json"),
                ],
            )

            logger.info("zip_complete", path=zip_path)
            return streamed_response(zip_path)


class LogError(APIView):
    """Log client errors"""

    def post(self, request: Request, format=None) -> Response:
        error_data = request.data
        logger.error(
            f"Client error: {error_data.get('message', '<no message>')}",
            extra=error_data,
        )
        return Response({"success": True}, status=status.HTTP_200_OK)
