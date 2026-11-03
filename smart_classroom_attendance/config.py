"""Configuration settings for the Smart Classroom Attendance System.
All values can be overridden by environment variables if needed.
"""
import os
from datetime import timezone, timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'change_this_secret_key')
    DEBUG = True

    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'database', 'smart_attendance.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads (face images)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'student_faces')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    # AI model directory
    MODEL_DIR = os.path.join(BASE_DIR, 'ai', 'model')
    LBPH_MODEL_FILE = os.path.join(MODEL_DIR, 'lbph_model.yml')

    # Attendance settings
    TIMEZONE = timezone(timedelta(hours=5, minutes=30))  # Asia/Kolkata
    CUTOFF_TIME = "09:30"  # HH:MM string; will be parsed when needed
    RECOGNITION_THRESHOLD = 70  # confidence percentage
