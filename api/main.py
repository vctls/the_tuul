import json
import tempfile
from pathlib import Path
from typing import Optional

import structlog
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from pydantic import BaseModel

from . import settings
from . import logging as app_logging
from .karaoke import music_separation
from .helpers import youtube_helper, zip_helper, cloud_storage
from .vite_assets import vite_assets

# Configure logging
app_logging.setup()
logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(title="The Tuul API", debug=settings.DEBUG)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom middleware for SharedArrayBuffer headers
@app.middleware("http")
async def add_sharedarraybuffer_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    return response


# Static files and templates
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


# Pydantic models
class LogErrorRequest(BaseModel):
    message: Optional[str] = None
    stack: Optional[str] = None
    url: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None


class SeparationPollResponse(BaseModel):
    finishedTrackURL: str


def streamed_response(file_path: Path) -> StreamingResponse:
    """Return a streaming response for the given file path."""

    # Read the entire file into memory to avoid issues with temp file cleanup
    file_content = file_path.read_bytes()

    def streaming_content():
        # Stream the content in chunks
        chunk_size = 1024 * 1024  # 1MB chunks
        for i in range(0, len(file_content), chunk_size):
            yield file_content[i : i + chunk_size]

    return StreamingResponse(streaming_content(), media_type="application/zip")


def process_track_separation_background(
    cache_hash: str, model_name: str, song_content: bytes, song_filename: str
):
    """Background task to process track separation and upload to cache."""
    with tempfile.TemporaryDirectory() as song_files_dir:
        song_files_dir_path = Path(song_files_dir)

        # Save uploaded file
        song_file_path = song_files_dir_path / song_filename
        with song_file_path.open("wb") as f:
            f.write(song_content)

        accompaniment_path, vocal_path = music_separation.split_song(
            song_file_path, song_files_dir_path, model_name=model_name
        )
        zip_path = zip_helper.create_zip_file(
            song_files_dir_path / "split_song.zip",
            [(accompaniment_path, "accompaniment.wav"), (vocal_path, "vocals.wav")],
        )
        logger.info("background_zip_complete", path=zip_path, cache_hash=cache_hash)

        # Upload to cache
        blob_name = f"separated_tracks/{cache_hash}.zip"
        logger.info(
            "background_uploading_to_cache", cache_hash=cache_hash, blob_name=blob_name
        )
        cloud_storage.upload_to_cache(cache_hash, zip_path)


@app.get("/")
async def index(request: Request):
    """Serve the main application page."""
    context = {
        "request": request,
        "vite_hmr_client": Markup(vite_assets.render_hmr_client()),
        "vite_assets": Markup(vite_assets.render_tags("index.ts")),
    }
    return templates.TemplateResponse("index.html", context)


@app.post("/separate_track")
async def separate_track(
    background_tasks: BackgroundTasks,
    songFile: UploadFile = File(...),
    modelName: str = Form(...),
):
    """Return a zip containing vocal and accompaniment splits of songFile."""
    if not songFile or not modelName:
        raise HTTPException(
            status_code=400, detail="songFile and modelName are required"
        )

    # Read file content
    song_content = await songFile.read()

    logger.info(
        "separate_tracks",
        song_size=len(song_content),
        model_name=modelName,
    )

    # Check if we can fetch from cache
    if settings.SEPARATED_TRACKS_BUCKET:
        cache_hash = cloud_storage.get_cache_hash(modelName, song_content)
        blob_name = f"separated_tracks/{cache_hash}.zip"
        logger.info("checking_cache", cache_hash=cache_hash, blob_name=blob_name)

        # Try to fetch from cache
        cache_result = cloud_storage.fetch_from_cache(cache_hash)
        if cache_result:
            # Cache found (either placeholder or completed) - return URL for client polling
            logger.info(
                "cache_found_returning_url",
                cache_hash=cache_hash,
                blob_name=blob_name,
                poll_url=cache_result,
            )
            return SeparationPollResponse(finishedTrackURL=cache_result)

    # If no cache hit or caching is disabled, proceed with track separation
    if settings.SEPARATED_TRACKS_BUCKET:
        # Create placeholder and get public URL for polling
        cache_hash = cloud_storage.get_cache_hash(modelName, song_content)
        poll_url = cloud_storage.create_cache_placeholder(cache_hash)

        if poll_url:
            # Start background task to process separation
            background_tasks.add_task(
                process_track_separation_background,
                cache_hash,
                modelName,
                song_content,
                songFile.filename or "uploaded_song",
            )

            # Return URL immediately for client to poll
            logger.info("returning_poll_url", cache_hash=cache_hash, poll_url=poll_url)
            return SeparationPollResponse(finishedTrackURL=poll_url)
        else:
            logger.warning("failed_to_create_placeholder", cache_hash=cache_hash)
    else:
        # No caching - process synchronously
        with tempfile.TemporaryDirectory() as song_files_dir:
            song_files_dir_path = Path(song_files_dir)

            # Save uploaded file
            song_file_path = song_files_dir_path / (
                songFile.filename or "uploaded_song"
            )
            with song_file_path.open("wb") as f:
                f.write(song_content)

            accompaniment_path, vocal_path = music_separation.split_song(
                song_file_path, song_files_dir_path, model_name=modelName
            )
            zip_path = zip_helper.create_zip_file(
                song_files_dir_path / "split_song.zip",
                [(accompaniment_path, "accompaniment.wav"), (vocal_path, "vocals.wav")],
            )
            logger.info("zip_complete", path=zip_path)

            return streamed_response(zip_path)


@app.get("/download_video")
async def download_youtube_video(url: str = Query(...)):
    """Download a YouTube video as audio and video streams and return them as a zip."""
    logger.info("download_youtube_video", youtube_url=url)

    if not url:
        raise HTTPException(status_code=400, detail="No url provided.")

    with tempfile.TemporaryDirectory() as song_files_dir:
        song_files_dir_path = Path(song_files_dir)

        metadata, audio_path, video_path = youtube_helper.get_youtube_streams(
            url, song_files_dir_path
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


@app.post("/log_error")
async def log_error(error_data: LogErrorRequest):
    """Log client errors."""
    logger.error(
        f"Client error: {error_data.message or '<no message>'}",
        extra=error_data.model_dump(),
    )
    return {"success": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
