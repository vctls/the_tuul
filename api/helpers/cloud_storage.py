import hashlib
import tempfile
from pathlib import Path
from typing import Optional

import structlog
from django.conf import settings
from django.core.files import File
from google.cloud import storage
from google.cloud.exceptions import NotFound

logger = structlog.get_logger(__name__)


def get_cache_hash(model_name: str, song_file: File) -> str:
    """
    Generate a hash from the model name and song file content.
    This hash is used as a key for caching separated tracks.
    """
    # Create a copy of the file in memory
    song_file.seek(0)
    file_data = song_file.read()
    song_file.seek(0)  # Reset the file pointer for future reads

    # Create a hash of the file content and model name
    hash_obj = hashlib.sha256()
    hash_obj.update(file_data)
    hash_obj.update(model_name.encode("utf-8"))
    return hash_obj.hexdigest()


def fetch_from_cache(cache_hash: str) -> Optional[Path]:
    """
    Try to fetch a zip file from Google Cloud Storage based on the hash.
    Returns the local path to the downloaded file if found, None otherwise.
    """
    if not settings.SEPARATED_TRACKS_BUCKET:
        return None

    blob_name = f"separated_tracks/{cache_hash}.zip"

    try:
        # Create a temporary file to download the content
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        temp_path = Path(temp_file.name)
        temp_file.close()

        # Download the file from GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.SEPARATED_TRACKS_BUCKET)
        blob = bucket.blob(blob_name)

        # Download the blob to a temporary file
        blob.download_to_filename(temp_path)
        logger.info("cache_hit", cache_hash=cache_hash, path=temp_path)
        return temp_path

    except NotFound:
        logger.info("cache_miss", cache_hash=cache_hash)
        return None
    except Exception as e:
        logger.error("cache_fetch_error", cache_hash=cache_hash, error=str(e))
        return None


def upload_to_cache(cache_hash: str, zip_path: Path) -> bool:
    """
    Upload the zip file to Google Cloud Storage using the hash as a key.
    Returns True if successful, False otherwise.
    """
    if not settings.SEPARATED_TRACKS_BUCKET:
        return False

    blob_name = f"separated_tracks/{cache_hash}.zip"

    try:
        # Upload the file to GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.SEPARATED_TRACKS_BUCKET)
        blob = bucket.blob(blob_name)

        blob.upload_from_filename(zip_path)
        logger.info("cache_upload_success", cache_hash=cache_hash, path=zip_path)
        return True

    except Exception as e:
        logger.error("cache_upload_error", cache_hash=cache_hash, error=str(e))
        return False
