import tempfile
from pathlib import Path
from unittest import mock
import os

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.helpers import cloud_storage


@pytest.fixture
def song_file():
    """Create a simple test audio file."""
    return ("test_song.mp3", b"test audio content", "audio/mpeg")


@pytest.fixture
def request_factory():
    """Create a request factory for testing."""
    return TestClient(app)


@mock.patch("api.karaoke.music_separation.split_song")
@mock.patch("api.helpers.cloud_storage.get_cache_hash")
@mock.patch("api.helpers.cloud_storage.fetch_from_cache")
@mock.patch("api.helpers.cloud_storage.upload_to_cache")
@mock.patch("api.helpers.zip_helper.create_zip_file")
def test_separate_track_with_cache_hit(
    mock_create_zip,
    mock_upload_to_cache,
    mock_fetch_from_cache,
    mock_get_cache_hash,
    mock_split_song,
    request_factory,
    song_file,
):
    """Test that the view returns cached file when available."""
    # Setup mocks
    mock_get_cache_hash.return_value = "test_hash"

    # Create a temporary file that will be our "cached" file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(b"cached zip content")

    mock_fetch_from_cache.return_value = temp_path

    # Create the request
    filename, content, content_type = song_file
    data = {"modelName": "test_model"}
    files = {"songFile": (filename, content, content_type)}

    # Test the view with cache enabled
    with mock.patch.dict(os.environ, {"SEPARATED_TRACKS_BUCKET": "test-bucket"}):
        url = "/separate_track"
        response = request_factory.post(url, data=data, files=files)

        # Assert that the cache was checked
        mock_get_cache_hash.assert_called_once()
        mock_fetch_from_cache.assert_called_once_with("test_hash")

        # Assert that the song was not split (cached version was used)
        mock_split_song.assert_not_called()
        mock_create_zip.assert_not_called()
        mock_upload_to_cache.assert_not_called()

        # Assert that the response is successful
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    # Clean up the temp file
    temp_path.unlink()


@mock.patch("api.karaoke.music_separation.split_song")
@mock.patch("api.helpers.cloud_storage.get_cache_hash")
@mock.patch("api.helpers.cloud_storage.fetch_from_cache")
@mock.patch("api.helpers.cloud_storage.upload_to_cache")
@mock.patch("api.helpers.cloud_storage.create_cache_placeholder")
@mock.patch("api.helpers.zip_helper.create_zip_file")
def test_separate_track_with_cache_miss(
    mock_create_zip,
    mock_create_placeholder,
    mock_upload_to_cache,
    mock_fetch_from_cache,
    mock_get_cache_hash: mock.Mock,
    mock_split_song,
    request_factory,
    song_file,
):
    """Test that the view processes the track and caches it when not in cache."""
    # Setup mocks
    mock_get_cache_hash.return_value = "test_hash"
    mock_fetch_from_cache.return_value = None  # Cache miss
    mock_create_placeholder.return_value = True

    # Mock the song splitting process
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        accomp_path = temp_dir_path / "accompaniment.wav"
        vocal_path = temp_dir_path / "vocals.wav"
        zip_path = temp_dir_path / "split_song.zip"

        # Create test files
        accomp_path.write_bytes(b"accompaniment content")
        vocal_path.write_bytes(b"vocals content")
        zip_path.write_bytes(b"zip content")

        mock_split_song.return_value = (accomp_path, vocal_path)
        mock_create_zip.return_value = zip_path

        # Create the request
        factory = request_factory
        filename, content, content_type = song_file
        data = {"modelName": "test_model"}
        files = {"songFile": (filename, content, content_type)}

        # Test the view with cache enabled
        with mock.patch.dict(os.environ, {"SEPARATED_TRACKS_BUCKET": "test-bucket"}):
            response = factory.post("/separate_track", data=data, files=files)

            # Assert that the cache was checked
            assert mock_get_cache_hash.call_count == 3  # cache check, placeholder, upload
            mock_fetch_from_cache.assert_called_once_with("test_hash")
            mock_create_placeholder.assert_called_once_with("test_hash")

            # Assert that the song was split and cached
            mock_split_song.assert_called_once()
            mock_create_zip.assert_called_once()
            mock_upload_to_cache.assert_called_once_with("test_hash", zip_path)

            # Assert that the response is successful
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"


@mock.patch("api.karaoke.music_separation.split_song")
@mock.patch("api.helpers.cloud_storage.get_cache_hash")
@mock.patch("api.helpers.cloud_storage.fetch_from_cache")
@mock.patch("api.helpers.cloud_storage.wait_for_cache")
@mock.patch("api.helpers.zip_helper.create_zip_file")
def test_separate_track_with_placeholder_found_success(
    mock_create_zip,
    mock_wait_for_cache,
    mock_fetch_from_cache,
    mock_get_cache_hash,
    mock_split_song,
    request_factory,
    song_file,
):
    """Test that the view waits for cache when placeholder is found and succeeds."""
    # Setup mocks
    mock_get_cache_hash.return_value = "test_hash"
    # Return placeholder dict
    mock_fetch_from_cache.return_value = {"startTime": 1234567890, "status": "processing"}
    
    # Create a temporary file that will be our "cached" file after waiting
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(b"cached zip content")
    
    mock_wait_for_cache.return_value = temp_path

    # Create the request
    filename, content, content_type = song_file
    data = {"modelName": "test_model"}
    files = {"songFile": (filename, content, content_type)}

    # Test the view with cache enabled
    with mock.patch.dict(os.environ, {"SEPARATED_TRACKS_BUCKET": "test-bucket"}):
        response = request_factory.post("/separate_track", data=data, files=files)

        # Assert that the cache was checked and wait was called
        mock_get_cache_hash.assert_called_once()
        mock_fetch_from_cache.assert_called_once_with("test_hash")
        mock_wait_for_cache.assert_called_once_with("test_hash")

        # Assert that the song was not split (cached version was used after wait)
        mock_split_song.assert_not_called()
        mock_create_zip.assert_not_called()

        # Assert that the response is successful
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    # Clean up the temp file
    temp_path.unlink()


@mock.patch("api.karaoke.music_separation.split_song")
@mock.patch("api.helpers.cloud_storage.get_cache_hash")
@mock.patch("api.helpers.cloud_storage.fetch_from_cache")
@mock.patch("api.helpers.cloud_storage.wait_for_cache")
@mock.patch("api.helpers.cloud_storage.create_cache_placeholder")
@mock.patch("api.helpers.cloud_storage.upload_to_cache")
@mock.patch("api.helpers.zip_helper.create_zip_file")
def test_separate_track_with_placeholder_found_timeout(
    mock_create_zip,
    mock_upload_to_cache,
    mock_create_placeholder,
    mock_wait_for_cache,
    mock_fetch_from_cache,
    mock_get_cache_hash,
    mock_split_song,
    request_factory,
    song_file,
):
    """Test that the view processes normally when placeholder wait times out."""
    # Setup mocks
    mock_get_cache_hash.return_value = "test_hash"
    # Return placeholder dict
    mock_fetch_from_cache.return_value = {"startTime": 1234567890, "status": "processing"}
    mock_wait_for_cache.return_value = None  # Timeout
    mock_create_placeholder.return_value = True

    # Mock the song splitting process
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        accomp_path = temp_dir_path / "accompaniment.wav"
        vocal_path = temp_dir_path / "vocals.wav"
        zip_path = temp_dir_path / "split_song.zip"

        # Create test files
        accomp_path.write_bytes(b"accompaniment content")
        vocal_path.write_bytes(b"vocals content")
        zip_path.write_bytes(b"zip content")

        mock_split_song.return_value = (accomp_path, vocal_path)
        mock_create_zip.return_value = zip_path

        # Create the request
        filename, content, content_type = song_file
        data = {"modelName": "test_model"}
        files = {"songFile": (filename, content, content_type)}

        # Test the view with cache enabled
        with mock.patch.dict(os.environ, {"SEPARATED_TRACKS_BUCKET": "test-bucket"}):
            response = request_factory.post("/separate_track", data=data, files=files)

            # Assert that the cache was checked and wait was called
            assert mock_get_cache_hash.call_count == 3  # initial check, placeholder creation, upload
            mock_fetch_from_cache.assert_called_once_with("test_hash")
            mock_wait_for_cache.assert_called_once_with("test_hash")
            mock_create_placeholder.assert_called_once_with("test_hash")

            # Assert that the song was split after timeout
            mock_split_song.assert_called_once()
            mock_create_zip.assert_called_once()
            mock_upload_to_cache.assert_called_once_with("test_hash", zip_path)

            # Assert that the response is successful
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"


@mock.patch("api.karaoke.music_separation.split_song")
@mock.patch("api.helpers.cloud_storage.get_cache_hash")
@mock.patch("api.helpers.cloud_storage.fetch_from_cache")
@mock.patch("api.helpers.cloud_storage.upload_to_cache")
@mock.patch("api.helpers.zip_helper.create_zip_file")
def test_separate_track_without_cache(
    mock_create_zip,
    mock_upload_to_cache,
    mock_fetch_from_cache,
    mock_get_cache_hash,
    mock_split_song,
    request_factory,
    song_file,
):
    """Test that the view works normally when caching is disabled."""
    # Mock the song splitting process
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        accomp_path = temp_dir_path / "accompaniment.wav"
        vocal_path = temp_dir_path / "vocals.wav"
        zip_path = temp_dir_path / "split_song.zip"

        # Create test files
        accomp_path.write_bytes(b"accompaniment content")
        vocal_path.write_bytes(b"vocals content")
        zip_path.write_bytes(b"zip content")

        mock_split_song.return_value = (accomp_path, vocal_path)
        mock_create_zip.return_value = zip_path

        # Create the request
        factory = request_factory
        filename, content, content_type = song_file
        data = {"modelName": "test_model"}
        files = {"songFile": (filename, content, content_type)}

        # Test the view with cache disabled
        with mock.patch("api.settings.SEPARATED_TRACKS_BUCKET", ""):
            response = factory.post("/separate_track", data=data, files=files)

            # Assert that cache operations were not attempted (bucket is empty)
            # Note: get_cache_hash may still be called for logging/diagnostics
            mock_fetch_from_cache.assert_not_called()
            mock_upload_to_cache.assert_not_called()

            # Assert that the song was split
            mock_split_song.assert_called_once()
            mock_create_zip.assert_called_once()

            # Assert that the response is successful
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"
