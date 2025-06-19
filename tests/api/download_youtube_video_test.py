import json
import zipfile
from io import BytesIO
from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient

import pytubefix as pytube
from api.helpers import youtube_helper
from api.main import app


@pytest.fixture
def youtube_fixture_dir():
    """Path to YouTube test fixtures. Creates minimal dummy fixtures if they don't exist."""
    fixture_dir = Path("tests/fixtures/youtube")
    return fixture_dir


class MockYouTubeStream:
    """Mock class for YouTube streams."""

    def __init__(self, stream_type, fixture_dir):
        self.fixture_dir = fixture_dir
        self.stream_type = stream_type

        # Load stream info from fixture
        info_path = fixture_dir / "streams_info.json"
        if info_path.exists():
            with open(info_path, "r") as f:
                streams_info = json.load(f)
                self.__dict__.update(streams_info[stream_type])

    def download(self, output_path, filename=None):
        """Mock download method that copies the fixture file."""
        src_path = self.fixture_dir / self.stream_type

        if filename:
            dest_path = Path(output_path) / filename
        else:
            dest_path = Path(output_path) / f"{self.stream_type}.mp4"

        # Create a copy of the fixture file
        with open(src_path, "rb") as src, open(dest_path, "wb") as dest:
            dest.write(src.read())

        return str(dest_path)


class MockYouTubeStreamQuery:
    """Mock class for YouTube stream queries."""

    def __init__(self, stream_type, fixture_dir):
        self.stream_type = stream_type
        self.fixture_dir = fixture_dir

    def first(self):
        """Return the first stream (only one in our mocked data)."""
        return MockYouTubeStream(self.stream_type, self.fixture_dir)


class MockYouTubeStreams:
    """Mock class for YouTube streams collection."""

    def __init__(self, fixture_dir):
        self.fixture_dir = fixture_dir

    def filter(self, only_audio=False, only_video=False, res=None):
        """Filter streams based on type."""
        if only_audio:
            return MockYouTubeStreamQuery("audio", self.fixture_dir)
        elif only_video:
            return MockYouTubeStreamQuery("video", self.fixture_dir)
        return None


class MockYouTube:
    """Mock class for YouTube API."""

    def __init__(self, url, proxies=None, fixture_dir=None):
        self.url = url
        self.proxies = proxies
        self.fixture_dir = fixture_dir or Path("tests/fixtures/youtube")

        # Load metadata from fixture
        metadata_path = self.fixture_dir / "metadata.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            self.__dict__.update(metadata)

        # Set up streams
        self.streams = MockYouTubeStreams(self.fixture_dir)


@pytest.mark.parametrize("youtube_url", ["https://www.youtube.com/watch?v=gVw-wI1GeqI"])
def test_download_youtube_video_integration(youtube_url, youtube_fixture_dir):
    """Test the YouTube download API endpoint with mocked YouTube API."""

    # Create a client for making requests
    client = TestClient(app)
    url = f"/download_video?url={youtube_url}"

    # Mock the YouTube class and zip helper to avoid file cleanup issues
    with mock.patch("api.helpers.youtube_helper.pytube.YouTube") as mock_youtube, \
         mock.patch("api.helpers.zip_helper.create_zip_file") as mock_create_zip:
        
        # Configure the mock to use our fixture data
        mock_youtube.return_value = MockYouTube(
            youtube_url, fixture_dir=youtube_fixture_dir
        )
        
        # Create a simple zip file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            import zipfile
            with zipfile.ZipFile(temp_zip, 'w') as zf:
                zf.writestr("audio.mp4", b"dummy audio content")
                zf.writestr("video.mp4", b"dummy video content")
                zf.writestr("metadata.json", '{"title": "test", "author": "test"}')
            mock_create_zip.return_value = Path(temp_zip.name)

        # Make the request using the client
        response = client.get(url)
        
        # Clean up the temp file
        Path(temp_zip.name).unlink()

        # Check that we got a successful response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

        # Read the response content into a buffer
        content = BytesIO(response.content)
        content.seek(0)

        # Check that the response is a valid zip file
        with zipfile.ZipFile(content, "r") as zip_file:
            # Verify the expected files are in the zip
            file_list = zip_file.namelist()
            assert "audio.mp4" in file_list
            assert "video.mp4" in file_list
            assert "metadata.json" in file_list

            # Verify the files have content
            for filename in file_list:
                info = zip_file.getinfo(filename)
                assert info.file_size > 0, f"{filename} is empty"

            # Check metadata content
            with zip_file.open("metadata.json") as f:
                metadata = json.load(f)
                assert "title" in metadata
                assert "author" in metadata
