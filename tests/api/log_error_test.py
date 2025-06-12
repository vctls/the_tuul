import json
from unittest import mock

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def test_log_error_success():
    """Test that LogError view logs client errors and returns success."""
    client = APIClient()
    url = reverse("log_error")
    
    error_data = {
        "message": "JavaScript error occurred",
        "stack": "Error: test error\n    at function1 (app.js:10:5)",
        "url": "https://example.com/page",
        "line": 10,
        "column": 5
    }
    
    with mock.patch("views.logger") as mock_logger:
        response = client.post(
            url,
            data=error_data,
            format="json"
        )
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"success": True}
    
    # Check that logger.error was called with correct parameters
    mock_logger.error.assert_called_once_with(
        "Client error: JavaScript error occurred",
        extra=error_data
    )


def test_log_error_no_message():
    """Test LogError view handles missing message field."""
    client = APIClient()
    url = reverse("log_error")
    
    error_data = {
        "stack": "Error: test error\n    at function1 (app.js:10:5)",
        "url": "https://example.com/page"
    }
    
    with mock.patch("views.logger") as mock_logger:
        response = client.post(
            url,
            data=error_data,
            format="json"
        )
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"success": True}
    
    # Check that logger.error was called with default message
    mock_logger.error.assert_called_once_with(
        "Client error: <no message>",
        extra=error_data
    )


def test_log_error_empty_data():
    """Test LogError view handles empty request data."""
    client = APIClient()
    url = reverse("log_error")
    
    with mock.patch("views.logger") as mock_logger:
        response = client.post(
            url,
            data={},
            format="json"
        )
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"success": True}
    
    # Check that logger.error was called with default message and empty data
    mock_logger.error.assert_called_once_with(
        "Client error: <no message>",
        extra={}
    )