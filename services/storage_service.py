"""Thread-safe CSV and JSON storage service.

Ensures reliable file locking, safe atomic reads/writes, header initialization,
and data validation for students, attendance records, settings, and user credentials.
"""

import csv
import json
import os
import threading
from pathlib import Path
from typing import List, Dict, Optional
from werkzeug.security import generate_password_hash, check_password_hash

from config import (
    STUDENTS_CSV,
    ATTENDANCE_CSV,
    SETTINGS_JSON,
    USERS_JSON,
    DEFAULT_SETTINGS,
    save_settings,
    load_settings
)

# Global re-entrant lock to ensure thread safety across concurrent Flask web requests
_file_lock = threading.RLock()

STUDENT_HEADERS = [
    "StudentID",
    "Name",
    "ClassDepartment",
    "YearSemester",
    "Email",
    "FaceRegistered",
    "RegistrationDate"
]

ATTENDANCE_HEADERS = [
    "StudentID",
    "Name",
    "Date",
    "Time",
    "Status",
    "SessionID"
]


def init_storage():
    """Initialize CSV files and default administrator credentials if not present."""
    with _file_lock:
        # Initialize students.csv
        if not STUDENTS_CSV.exists() or os.path.getsize(STUDENTS_CSV) == 0:
            with open(STUDENTS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(STUDENT_HEADERS)

        # Initialize attendance.csv
        if not ATTENDANCE_CSV.exists() or os.path.getsize(ATTENDANCE_CSV) == 0:
            with open(ATTENDANCE_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(ATTENDANCE_HEADERS)

        # Initialize settings.json
        if not SETTINGS_JSON.exists():
            save_settings(DEFAULT_SETTINGS)

        # Initialize users.json with default admin credentials
        if not USERS_JSON.exists() or os.path.getsize(USERS_JSON) == 0:
            default_admin = {
                "admin": {
                    "username": "admin",
                    "password_hash": generate_password_hash(
                        os.environ.get("ADMIN_PASSWORD", "admin123")
                    ),
                    "full_name": "System Administrator",
                    "role": "admin"
                }
            }
            with open(USERS_JSON, "w", encoding="utf-8") as f:
                json.dump(default_admin, f, indent=4)


# ==========================================
# USER AUTHENTICATION STORAGE
# ==========================================

def get_user(username: str) -> Optional[dict]:
    """Retrieve user dictionary by username."""
    with _file_lock:
        if not USERS_JSON.exists():
            return None
        try:
            with open(USERS_JSON, "r", encoding="utf-8") as f:
                users = json.load(f)
                return users.get(username)
        except Exception:
            return None


def verify_user(username: str, password: str) -> Optional[dict]:
    """Verify username and password hash. Returns user dict on success, None on failure."""
    user = get_user(username)
    if not user:
        return None
    if check_password_hash(user.get("password_hash", ""), password):
        return user
    return None


def update_admin_password(username: str, new_password: str) -> bool:
    """Update password for an existing administrative user."""
    with _file_lock:
        if not USERS_JSON.exists():
            return False
        try:
            with open(USERS_JSON, "r", encoding="utf-8") as f:
                users = json.load(f)
            if username in users:
                users[username]["password_hash"] = generate_password_hash(new_password)
                with open(USERS_JSON, "w", encoding="utf-8") as f:
                    json.dump(users, f, indent=4)
                return True
            return False
        except Exception as e:
            print(f"Error updating password: {e}")
            return False


# ==========================================
# STUDENTS CSV STORAGE
# ==========================================

def read_all_students() -> List[Dict[str, str]]:
    """Read all student records from students.csv."""
    init_storage()
    records = []
    with _file_lock:
        try:
            with open(STUDENTS_CSV, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean whitespace
                    clean_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
                    if clean_row.get("StudentID"):
                        records.append(clean_row)
        except Exception as e:
            print(f"Error reading students CSV: {e}")
    return records


def write_all_students(students: List[Dict[str, str]]) -> bool:
    """Overwrite students.csv safely with given list of student records."""
    init_storage()
    with _file_lock:
        try:
            temp_file = STUDENTS_CSV.with_suffix(".tmp")
            with open(temp_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=STUDENT_HEADERS)
                writer.writerow(dict(zip(STUDENT_HEADERS, STUDENT_HEADERS)))  # header row
                for student in students:
                    # Filter only known headers
                    row = {k: student.get(k, "") for k in STUDENT_HEADERS}
                    writer.writerow(row)
            # Atomic replace
            os.replace(temp_file, STUDENTS_CSV)
            return True
        except Exception as e:
            print(f"Error writing students CSV: {e}")
            return False


def append_student(student_data: Dict[str, str]) -> bool:
    """Append a single student record to students.csv."""
    init_storage()
    with _file_lock:
        try:
            with open(STUDENTS_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=STUDENT_HEADERS)
                row = {k: student_data.get(k, "") for k in STUDENT_HEADERS}
                writer.writerow(row)
            return True
        except Exception as e:
            print(f"Error appending student to CSV: {e}")
            return False


# ==========================================
# ATTENDANCE CSV STORAGE
# ==========================================

def read_all_attendance() -> List[Dict[str, str]]:
    """Read all attendance records from attendance.csv."""
    init_storage()
    records = []
    with _file_lock:
        try:
            with open(ATTENDANCE_CSV, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    clean_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
                    if clean_row.get("StudentID") or clean_row.get("Name"):
                        records.append(clean_row)
        except Exception as e:
            print(f"Error reading attendance CSV: {e}")
    return records


def append_attendance(record: Dict[str, str]) -> bool:
    """Safely append an attendance record to attendance.csv."""
    init_storage()
    with _file_lock:
        try:
            with open(ATTENDANCE_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=ATTENDANCE_HEADERS)
                row = {k: record.get(k, "") for k in ATTENDANCE_HEADERS}
                writer.writerow(row)
            return True
        except Exception as e:
            print(f"Error appending attendance to CSV: {e}")
            return False
