"""Student management service.

Handles student addition, validation, updating, deletion, searching,
and face-registration tracking.
"""

import os
import shutil
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from config import DATASET_DIR, get_current_time
from services.storage_service import (
    read_all_students,
    write_all_students,
    append_student
)


def validate_student_id(student_id: str) -> Tuple[bool, str]:
    """Validate student ID format (alphanumeric and hyphens, 3-20 characters)."""
    if not student_id or not isinstance(student_id, str):
        return False, "Student ID cannot be empty."
    student_id = student_id.strip()
    if len(student_id) < 2 or len(student_id) > 20:
        return False, "Student ID must be between 2 and 20 characters."
    if not re.match(r"^[A-Za-z0-9_-]+$", student_id):
        return False, "Student ID can only contain letters, numbers, hyphens, and underscores."
    return True, ""


def get_all_students(
    search_query: Optional[str] = None,
    department: Optional[str] = None,
    face_status: Optional[str] = None,
    sort_by: str = "StudentID"
) -> List[Dict[str, str]]:
    """Retrieve students with optional search, filtering, and sorting."""
    students = read_all_students()

    # Apply search filter
    if search_query:
        query = search_query.strip().lower()
        students = [
            s for s in students
            if query in s.get("StudentID", "").lower() or query in s.get("Name", "").lower()
        ]

    # Apply department filter
    if department and department.strip():
        dept_query = department.strip().lower()
        students = [
            s for s in students
            if dept_query == s.get("ClassDepartment", "").strip().lower()
        ]

    # Apply face registration status filter
    if face_status and face_status.strip():
        status_query = face_status.strip().lower()
        students = [
            s for s in students
            if status_query == s.get("FaceRegistered", "").strip().lower()
        ]

    # Apply sorting
    reverse = False
    if sort_by.startswith("-"):
        sort_by = sort_by[1:]
        reverse = True

    students.sort(key=lambda s: s.get(sort_by, "").lower(), reverse=reverse)
    return students


def get_student_by_id(student_id: str) -> Optional[Dict[str, str]]:
    """Find a student by their unique Student ID."""
    if not student_id:
        return None
    students = read_all_students()
    target_id = student_id.strip().upper()
    for student in students:
        if student.get("StudentID", "").strip().upper() == target_id:
            return student
    return None


def add_student(
    student_id: str,
    name: str,
    class_department: str,
    year_semester: str,
    email: str = ""
) -> Tuple[bool, str, Optional[Dict[str, str]]]:
    """Add a new student with validation and duplicate prevention."""
    # Validate Student ID
    is_valid, err_msg = validate_student_id(student_id)
    if not is_valid:
        return False, err_msg, None

    student_id = student_id.strip().upper()
    name = name.strip()

    if not name:
        return False, "Student name cannot be empty.", None

    if len(name) < 2 or len(name) > 60:
        return False, "Student name must be between 2 and 60 characters.", None

    # Check for duplicate Student ID
    existing = get_student_by_id(student_id)
    if existing:
        return False, f"A student with ID '{student_id}' already exists.", None

    now_str = get_current_time().strftime("%Y-%m-%d %H:%M:%S")

    new_student = {
        "StudentID": student_id,
        "Name": name,
        "ClassDepartment": class_department.strip() or "General",
        "YearSemester": year_semester.strip() or "Semester 1",
        "Email": email.strip(),
        "FaceRegistered": "No",
        "RegistrationDate": now_str
    }

    success = append_student(new_student)
    if success:
        return True, f"Student '{name}' ({student_id}) successfully registered.", new_student
    return False, "Failed to write student to storage.", None


def update_student(
    student_id: str,
    name: str,
    class_department: str,
    year_semester: str,
    email: str = ""
) -> Tuple[bool, str]:
    """Update student metadata without changing their unique ID."""
    student_id = student_id.strip().upper()
    students = read_all_students()

    found = False
    for s in students:
        if s.get("StudentID", "").strip().upper() == student_id:
            s["Name"] = name.strip()
            s["ClassDepartment"] = class_department.strip()
            s["YearSemester"] = year_semester.strip()
            s["Email"] = email.strip()
            found = True
            break

    if not found:
        return False, f"Student ID '{student_id}' not found."

    success = write_all_students(students)
    if success:
        return True, "Student details updated successfully."
    return False, "Failed to save updated student details."


def update_face_registration_status(student_id: str, is_registered: bool) -> bool:
    """Update face registration status flag for a student."""
    student_id = student_id.strip().upper()
    students = read_all_students()

    status_str = "Yes" if is_registered else "No"
    updated = False
    for s in students:
        if s.get("StudentID", "").strip().upper() == student_id:
            s["FaceRegistered"] = status_str
            updated = True
            break

    if updated:
        return write_all_students(students)
    return False


def delete_student(student_id: str) -> Tuple[bool, str]:
    """Delete a student record and their registered face training images."""
    student_id = student_id.strip().upper()
    students = read_all_students()

    initial_count = len(students)
    students = [s for s in students if s.get("StudentID", "").strip().upper() != student_id]

    if len(students) == initial_count:
        return False, f"Student with ID '{student_id}' does not exist."

    # Remove face dataset folder if present
    student_dataset_dir = DATASET_DIR / student_id
    if student_dataset_dir.exists():
        try:
            shutil.rmtree(student_dataset_dir)
        except Exception as e:
            print(f"Warning: could not delete face dataset folder: {e}")

    success = write_all_students(students)
    if success:
        return True, f"Student '{student_id}' and associated face data removed successfully."
    return False, "Failed to update storage during deletion."


def count_student_images(student_id: str) -> int:
    """Return count of captured face images for a student."""
    student_id = student_id.strip().upper()
    student_dataset_dir = DATASET_DIR / student_id
    if not student_dataset_dir.exists():
        return 0
    valid_exts = {".jpg", ".jpeg", ".png"}
    return sum(1 for f in student_dataset_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_exts)
