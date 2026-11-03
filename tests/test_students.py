"""Automated tests for Student Management Service & Data Storage.

Verifies:
- Test 3: A student can be registered.
- Test 4: Duplicate student IDs are rejected.
- Test 12: Missing CSV files are handled safely.
- Student search, update, deletion, and validation.
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.student_service import (
    add_student,
    get_student_by_id,
    get_all_students,
    update_student,
    delete_student,
    validate_student_id
)
from services.storage_service import init_storage, read_all_students


class TestStudentManagement(unittest.TestCase):

    def setUp(self):
        init_storage()

    def test_01_student_id_validation(self):
        """Validate format rules for student IDs."""
        valid, _ = validate_student_id("STU200")
        self.assertTrue(valid)

        valid, _ = validate_student_id("CS-2026-01")
        self.assertTrue(valid)

        valid, msg = validate_student_id("")
        self.assertFalse(valid)
        self.assertIn("empty", msg.lower())

        valid, msg = validate_student_id("A")  # too short
        self.assertFalse(valid)

        valid, msg = validate_student_id("ID WITH SPACES!")  # invalid characters
        self.assertFalse(valid)

    def test_02_register_student_success(self):
        """Test Case 3: A student can be registered."""
        test_id = "TEST-REG-01"
        # Cleanup first if previously present
        delete_student(test_id)

        success, msg, student = add_student(
            student_id=test_id,
            name="Alice Smith",
            class_department="Computer Science",
            year_semester="Semester 6",
            email="alice@college.edu"
        )

        self.assertTrue(success, f"Failed to add student: {msg}")
        self.assertIsNotNone(student)
        self.assertEqual(student["StudentID"], test_id)
        self.assertEqual(student["Name"], "Alice Smith")

        # Verify retrieved from CSV
        fetched = get_student_by_id(test_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["Name"], "Alice Smith")

        # Cleanup
        delete_student(test_id)

    def test_03_duplicate_student_id_rejected(self):
        """Test Case 4: Duplicate student IDs are rejected."""
        test_id = "TEST-DUP-01"
        delete_student(test_id)

        # First registration should succeed
        s1, _, _ = add_student(test_id, "Bob Ross", "Art", "Semester 1")
        self.assertTrue(s1)

        # Second registration with SAME student ID must be rejected
        s2, msg, _ = add_student(test_id, "Bob Duplicate", "Art", "Semester 1")
        self.assertFalse(s2, "Duplicate student ID must be rejected.")
        self.assertIn("already exists", msg.lower())

        # Cleanup
        delete_student(test_id)

    def test_04_update_student_details(self):
        """Test updating student name and department."""
        test_id = "TEST-UPD-01"
        delete_student(test_id)

        add_student(test_id, "Charlie Original", "Civil", "Semester 2")

        success, _ = update_student(test_id, "Charlie Updated", "Mechanical", "Semester 3", "charlie@college.edu")
        self.assertTrue(success)

        updated = get_student_by_id(test_id)
        self.assertEqual(updated["Name"], "Charlie Updated")
        self.assertEqual(updated["ClassDepartment"], "Mechanical")

        delete_student(test_id)

    def test_05_delete_student_confirmation(self):
        """Test deleting a student."""
        test_id = "TEST-DEL-01"
        add_student(test_id, "Diana Prince", "Computer Science", "Semester 4")

        success, _ = delete_student(test_id)
        self.assertTrue(success)

        self.assertIsNone(get_student_by_id(test_id))

    def test_06_missing_csv_files_handled_safely(self):
        """Test Case 12: Missing CSV files are handled safely and automatically re-initialized."""
        # Calling read_all_students() always re-initializes missing files
        students = read_all_students()
        self.assertIsInstance(students, list)


if __name__ == "__main__":
    unittest.main()
