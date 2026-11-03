"""Configuration module for AI & IoT Smart Classroom Attendance System.

Manages filesystem paths, application defaults, security keys, and runtime settings.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import zoneinfo

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATASET_DIR = DATA_DIR / "face_dataset"
MODELS_DIR = BASE_DIR / "models"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Data file paths
STUDENTS_CSV = DATA_DIR / "students.csv"
ATTENDANCE_CSV = DATA_DIR / "attendance.csv"
SETTINGS_JSON = DATA_DIR / "settings.json"
USERS_JSON = DATA_DIR / "users.json"
MODEL_FILE = MODELS_DIR / "trainer.yml"
LABELS_FILE = MODELS_DIR / "labels.json"

# Ensure directories exist
for directory in [DATA_DIR, DATASET_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Default configuration values
DEFAULT_SETTINGS = {
    "institution_name": "Smart Classroom Campus",
    "department": "Computer Science & Engineering",
    "semester": "Semester 6 - 2026",
    "cutoff_time": "09:30",
    "timezone": "Asia/Kolkata",
    "camera_source": "0",  # "0" for laptop webcam, or "http://<ip>:81/stream" for ESP32-CAM
    "recognition_threshold": 75.0,  # LBPH distance threshold: below this is considered a match
    "duplicate_cooldown_seconds": 300,  # 5 minutes visual cooldown on live feed
    "attendance_session": "SESSION_1"
}


def load_settings() -> dict:
    """Load settings from JSON file or create with default values."""
    if not SETTINGS_JSON.exists():
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge defaults for any missing keys
            merged = dict(DEFAULT_SETTINGS)
            merged.update(data)
            return merged
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings_data: dict) -> bool:
    """Save settings safely to JSON file."""
    try:
        with open(SETTINGS_JSON, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def get_current_time(timezone_str: str = None) -> datetime:
    """Get current localized datetime based on configured timezone."""
    if timezone_str is None:
        settings = load_settings()
        timezone_str = settings.get("timezone", "Asia/Kolkata")
    try:
        tz = zoneinfo.ZoneInfo(timezone_str)
        return datetime.now(tz)
    except Exception:
        # Fallback to local time if timezone is invalid
        return datetime.now()


class Config:
    """Flask configuration object."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "smart-classroom-attendance-secret-key-2026")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
