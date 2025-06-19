import hashlib
import json
import tempfile
import time
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


def fetch_from_cache(cache_hash: str) -> Optional[Path] | dict:
    """
    Try to fetch a zip file from Google Cloud Storage based on the hash.
    Returns:
    - Path to downloaded file if actual cache found
    - dict with placeholder data if placeholder JSON found
    - None if not found at all
    """
    if not settings.SEPARATED_TRACKS_BUCKET:
        return None

    blob_name = f"separated_tracks/{cache_hash}.zip"

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.SEPARATED_TRACKS_BUCKET)
        blob = bucket.blob(blob_name)

        # Check if the blob exists
        if not blob.exists():
            logger.info("cache_miss", cache_hash=cache_hash, blob_name=blob_name)
            return None

        # Check content type to determine if it's a placeholder or actual cache
        blob.reload()
        if blob.content_type == "application/json":
            placeholder_content = blob.download_as_text()
            placeholder_data = json.loads(placeholder_content)
            logger.info(
                "cache_placeholder_found", cache_hash=cache_hash, blob_name=blob_name
            )
            return placeholder_data

        # Create a temporary file to download the content
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        temp_path = Path(temp_file.name)
        temp_file.close()

        # Download the blob to a temporary file
        blob.download_to_filename(temp_path)
        logger.info(
            "cache_hit", cache_hash=cache_hash, blob_name=blob_name, path=temp_path
        )
        return temp_path

    except NotFound:
        logger.info("cache_miss", cache_hash=cache_hash, blob_name=blob_name)
        return None
    except Exception as e:
        logger.error(
            "cache_fetch_error",
            cache_hash=cache_hash,
            blob_name=blob_name,
            error=str(e),
        )
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
        logger.info(
            "cache_upload_success",
            cache_hash=cache_hash,
            blob_name=blob_name,
            path=zip_path,
        )
        return True

    except Exception as e:
        logger.error(
            "cache_upload_error",
            cache_hash=cache_hash,
            blob_name=blob_name,
            error=str(e),
        )
        return False


def create_cache_placeholder(cache_hash: str) -> bool:
    """
    Create a placeholder JSON file in GCS to indicate processing has started.
    Uses the same filename as the final cache file.
    Returns True if successful, False otherwise.
    """
    if not settings.SEPARATED_TRACKS_BUCKET:
        return False

    blob_name = f"separated_tracks/{cache_hash}.zip"
    placeholder_data = {"startTime": int(time.time()), "status": "processing"}

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.SEPARATED_TRACKS_BUCKET)
        blob = bucket.blob(blob_name)

        blob.upload_from_string(
            json.dumps(placeholder_data), content_type="application/json"
        )
        logger.info(
            "cache_placeholder_created", cache_hash=cache_hash, blob_name=blob_name
        )
        return True

    except Exception as e:
        logger.error(
            "cache_placeholder_error",
            cache_hash=cache_hash,
            blob_name=blob_name,
            error=str(e),
        )
        return False


def wait_for_cache(
    cache_hash: str, timeout_seconds: int = 1200, poll_interval: int = 30
) -> Optional[Path]:
    """
    Wait for a cached file to become available by polling.
    Returns the cached file path if found within timeout, None otherwise.
    """
    if not settings.SEPARATED_TRACKS_BUCKET:
        return None

    blob_name = f"separated_tracks/{cache_hash}.zip"
    start_time = time.time()

    logger.info(
        "cache_wait_start",
        cache_hash=cache_hash,
        blob_name=blob_name,
        timeout_seconds=timeout_seconds,
    )

    while time.time() - start_time < timeout_seconds:
        # Try to fetch from cache - only return if it's an actual Path
        cache_result = fetch_from_cache(cache_hash)
        if isinstance(cache_result, Path):
            logger.info(
                "cache_wait_success",
                cache_hash=cache_hash,
                blob_name=blob_name,
                wait_time=time.time() - start_time,
            )
            return cache_result

        # Sleep before next poll
        time.sleep(poll_interval)

    logger.info(
        "cache_wait_timeout",
        cache_hash=cache_hash,
        blob_name=blob_name,
        timeout_seconds=timeout_seconds,
    )
    return None
