import os
import zipfile
from io import BytesIO
from pathlib import Path
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def audio_file():
    """Fixture providing the test audio file."""
    file_path = Path("tests/fixtures/lookin_up_in_heaven.mp3")
    with open(file_path, "rb") as f:
        uploaded_file = SimpleUploadedFile(
            file_path.name, f.read(), content_type="audio/mpeg"
        )
    return uploaded_file


def test_separate_track_integration(audio_file):
    """Test the music separation API endpoint."""
    # Create a client for making requests
    client = APIClient()
    url = reverse("separate_track")

    # Make the request using the client
    response = client.post(
        url,
        data={"songFile": audio_file, "modelName": "UVR_MDXNET_KARA_2.onnx"},
        format="multipart",
    )

    # Check that we got a streaming response
    assert response.streaming is True

    # Read the streaming content into a buffer
    content = BytesIO()
    for chunk in response.streaming_content:
        content.write(chunk)
    content.seek(0)

    # Check that the response is a valid zip file
    with zipfile.ZipFile(content, "r") as zip_file:
        # Verify the expected files are in the zip
        file_list = zip_file.namelist()
        assert "accompaniment.wav" in file_list
        assert "vocals.wav" in file_list

        # Verify the files have content
        for filename in file_list:
            info = zip_file.getinfo(filename)
            assert info.file_size > 0, f"{filename} is empty"
