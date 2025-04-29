import json
import tempfile
from pathlib import Path
import zipfile

import structlog

from django.core.files.storage import FileSystemStorage
from django.http import StreamingHttpResponse
from django.core.files import File
from django.views.generic.base import TemplateView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework import status

from karaoke import music_separation
from helpers import youtube_helper

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
        with tempfile.TemporaryDirectory() as song_files_dir:
            song_files_dir_path = Path(song_files_dir)
            song_file_path = self.setup_song_files_dir(song_files_dir, song_file)
            accompaniment_path, vocal_path = music_separation.split_song(
                song_file_path, song_files_dir_path, model_name=model_name
            )
            zip_path = song_files_dir_path / "split_song.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(
                    accompaniment_path,
                    "accompaniment.wav",
                )
                zip_file.write(
                    vocal_path,
                    "vocals.wav",
                )

            logger.info("zip_complete", path=zip_path)
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
            zip_path = song_files_dir_path / "youtube_video.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(
                    audio_path,
                    "audio.mp4",
                )
                zip_file.write(
                    video_path,
                    "video.mp4",
                )
                zip_file.write(song_files_dir_path / "metadata.json", "metadata.json")

            logger.info("zip_complete", path=zip_path)
            return streamed_response(zip_path)


class LogError(APIView):
    """Log client errors"""

    def post(self, request: Request, format=None) -> Response:
        error_data = request.data
        logger.error("Client error", extra=error_data)
        return Response({"success": True}, status=status.HTTP_200_OK)
