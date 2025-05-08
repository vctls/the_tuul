import tempfile
from pathlib import Path
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIRequestFactory

from api.views import SeparateTrack
from api.helpers import cloud_storage


@pytest.fixture
def song_file():
    """Create a simple test audio file."""
    return SimpleUploadedFile("test_song.mp3", b"test audio content", content_type="audio/mpeg")


@pytest.fixture
def request_factory():
    """Create a request factory for testing."""
    return APIRequestFactory()


@mock.patch("api.views.music_separation.split_song")
@mock.patch("api.views.cloud_storage.get_cache_hash")
@mock.patch("api.views.cloud_storage.fetch_from_cache")
@mock.patch("api.views.cloud_storage.upload_to_cache")
@mock.patch("api.views.zip_helper.create_zip_file")
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
    factory = request_factory
    data = {"songFile": song_file, "modelName": "test_model"}
    request = factory.post("/api/separate-track/", data, format="multipart")

    # Test the view with cache enabled
    with override_settings(SEPARATED_TRACKS_BUCKET="test-bucket"):
        view = SeparateTrack()
        response = view.post(request)

        # Assert that the cache was checked
        mock_get_cache_hash.assert_called_once_with("test_model", song_file)
        mock_fetch_from_cache.assert_called_once_with("test_hash")

        # Assert that the song was not split (cached version was used)
        mock_split_song.assert_not_called()
        mock_create_zip.assert_not_called()
        mock_upload_to_cache.assert_not_called()

        # Assert that the response is streaming
        assert hasattr(response, "streaming_content")

    # Clean up the temp file
    temp_path.unlink()


@mock.patch("api.views.music_separation.split_song")
@mock.patch("api.views.cloud_storage.get_cache_hash")
@mock.patch("api.views.cloud_storage.fetch_from_cache")
@mock.patch("api.views.cloud_storage.upload_to_cache")
@mock.patch("api.views.zip_helper.create_zip_file")
def test_separate_track_with_cache_miss(
    mock_create_zip,
    mock_upload_to_cache,
    mock_fetch_from_cache,
    mock_get_cache_hash,
    mock_split_song,
    request_factory,
    song_file,
):
    """Test that the view processes the track and caches it when not in cache."""
    # Setup mocks
    mock_get_cache_hash.return_value = "test_hash"
    mock_fetch_from_cache.return_value = None  # Cache miss

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
        data = {"songFile": song_file, "modelName": "test_model"}
        request = factory.post("/api/separate-track/", data, format="multipart")

        # Test the view with cache enabled
        with override_settings(SEPARATED_TRACKS_BUCKET="test-bucket"):
            view = SeparateTrack()
            response = view.post(request)

            # Assert that the cache was checked
            mock_get_cache_hash.assert_called_with("test_model", song_file)
            mock_fetch_from_cache.assert_called_once_with("test_hash")

            # Assert that the song was split and cached
            mock_split_song.assert_called_once()
            mock_create_zip.assert_called_once()
            mock_upload_to_cache.assert_called_once_with("test_hash", zip_path)

            # Assert that the response is streaming
            assert hasattr(response, "streaming_content")


@mock.patch("api.views.music_separation.split_song")
@mock.patch("api.views.cloud_storage.get_cache_hash")
@mock.patch("api.views.cloud_storage.fetch_from_cache")
@mock.patch("api.views.cloud_storage.upload_to_cache")
@mock.patch("api.views.zip_helper.create_zip_file")
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
        data = {"songFile": song_file, "modelName": "test_model"}
        request = factory.post("/api/separate-track/", data, format="multipart")

        # Test the view with cache disabled
        with override_settings(SEPARATED_TRACKS_BUCKET=""):
            view = SeparateTrack()
            response = view.post(request)

            # Assert that no cache operations were performed
            mock_get_cache_hash.assert_not_called()
            mock_fetch_from_cache.assert_not_called()
            mock_upload_to_cache.assert_not_called()

            # Assert that the song was split
            mock_split_song.assert_called_once()
            mock_create_zip.assert_called_once()

            # Assert that the response is streaming
            assert hasattr(response, "streaming_content")
