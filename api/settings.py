"""
FastAPI application settings.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "frabbaglabba")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True") != "False"

# Google Cloud Storage bucket for caching separated tracks
SEPARATED_TRACKS_BUCKET = os.getenv("SEPARATED_TRACKS_BUCKET", "")

# YouTube proxy settings
YOUTUBE_PROXY = os.getenv("YOUTUBE_PROXY", "")

# Valid values are 'console' or 'gcp'
LOGGING_FORMAT = os.getenv("LOGGING_FORMAT", "console")

# Static files configuration
if DEBUG:
    STATIC_DIR = BASE_DIR / "assets"
else:
    STATIC_DIR = BASE_DIR / "staticroot"

# Templates directory
TEMPLATES_DIR = BASE_DIR / "templates"

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True

# Server settings
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8000"))
