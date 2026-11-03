"""Automated tests for Attendance Recording, Cutoff Times, and Exporting.

Verifies:
- Test 9: Attendance before 9:30 AM is marked Present.
- Test 10: Attendance at or after 9:30 AM is marked Late.
- Test 11: Duplicate attendance is prevented for same student/date/session.
- Test 13: Dashboard statistics match stored data.
- Test 14: CSV export works.
"""

import unittest
import sys
from datetime import datetime, date, time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.attendance_service import (
    determine_attendance_status,
    mark_attendance,
    is_already_marked,
    get_daily_summary,
    get_filtered_attendance,
    generate_attendance_csv
)
from services.student_service import add_student, delete_student
from services.storage_service import init_storage, read_all_attendance, _file_lock, ATTENDANCE_HEADERS
from config import ATTENDANCE_CSV
import csv


class TestAttendanceService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_storage()
        cls.test_student_id = "ATT-TEST-01"
        delete_student(cls.test_student_id)
        add_student(cls.test_student_id, "Test Attendance Student", "Computer Science", "Semester 6")

    @classmethod
    def tearDownClass(cls):
        delete_student(cls.test_student_id)
        # Clean up any test attendance records
        records = read_all_attendance()
        cleaned = [r for r in records if r.get("StudentID", "").upper() != cls.test_student_id]
        with open(ATTENDANCE_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ATTENDANCE_HEADERS)
            writer.writeheader()
            for r in cleaned:
                writer.writerow({k: r.get(k, "") for k in ATTENDANCE_HEADERS})

    def setUp(self):
        # Ensure student is marked for attendance tests
        pass

    def test_01_cutoff_rule_before_0930_is_present(self):
        """Test Case 9: Attendance before 9:30 AM is marked Present."""
        # Test 08:45 AM
        dt_early = datetime.combine(date(2026, 10, 29), time(8, 45, 0))
        status = determine_attendance_status(dt_early, cutoff_str="09:30")
        self.assertEqual(status, "Present", "Scan at 08:45 AM should be 'Present'.")

        # Test 09:29:59 AM
        dt_just_in_time = datetime.combine(date(2026, 10, 29), time(9, 29, 59))
        status = determine_attendance_status(dt_just_in_time, cutoff_str="09:30")
        self.assertEqual(status, "Present", "Scan at 09:29:59 AM should be 'Present'.")

    def test_02_cutoff_rule_at_or_after_0930_is_late(self):
        """Test Case 10: Attendance at or after 9:30 AM is marked Late."""
        # Test 09:30:00 AM (exact cutoff)
        dt_exact = datetime.combine(date(2026, 10, 29), time(9, 30, 0))
        status = determine_attendance_status(dt_exact, cutoff_str="09:30")
        self.assertEqual(status, "Late", "Scan at exactly 09:30 AM should be 'Late'.")

        # Test 10:15 AM
        dt_after = datetime.combine(date(2026, 10, 29), time(10, 15, 0))
        status = determine_attendance_status(dt_after, cutoff_str="09:30")
        self.assertEqual(status, "Late", "Scan at 10:15 AM should be 'Late'.")

    def test_03_mark_attendance_and_duplicate_prevention(self):
        """Test Case 11: Duplicate attendance is prevented for same student, date, and session."""
        custom_dt = datetime(2026, 11, 15, 8, 30, 0)
        session_id = "TEST_SESSION_X"

        # Clean prior record for this session if present
        records = [r for r in read_all_attendance() if not (r.get("StudentID") == self.test_student_id and r.get("Date") == "2026-11-15")]
        with open(ATTENDANCE_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ATTENDANCE_HEADERS)
            writer.writeheader()
            for r in records:
                writer.writerow({k: r.get(k, "") for k in ATTENDANCE_HEADERS})

        # 1. First scan should succeed
        success1, msg1, rec1 = mark_attendance(
            student_id=self.test_student_id,
            session_id=session_id,
            custom_dt=custom_dt
        )
        self.assertTrue(success1, f"Initial attendance should succeed: {msg1}")
        self.assertIsNotNone(rec1)
        self.assertEqual(rec1["Status"], "Present")

        # 2. Second scan for SAME student, date, and session must be prevented
        success2, msg2, rec2 = mark_attendance(
            student_id=self.test_student_id,
            session_id=session_id,
            custom_dt=custom_dt
        )
        self.assertFalse(success2, "Duplicate attendance mark must be rejected.")
        self.assertIn("already marked", msg2.lower())

    def test_04_dashboard_statistics_match_stored_data(self):
        """Test Case 13: Dashboard statistics match stored data."""
        # Ensure attendance marked for test date
        mark_attendance(
            self.test_student_id,
            session_id="TEST_SESSION_X",
            custom_dt=datetime(2026, 11, 15, 8, 30, 0)
        )
        # Query summary for 2026-11-15
        summary = get_daily_summary(date_str="2026-11-15", session_id="TEST_SESSION_X")
        self.assertIsInstance(summary, dict)
        self.assertGreaterEqual(summary["total_students"], 1)
        self.assertGreaterEqual(summary["present_count"], 1)
        self.assertIsInstance(summary["attendance_rate"], float)
        self.assertIsInstance(summary["absent_students"], list)

    def test_05_csv_export_format(self):
        """Test Case 14: CSV export works and outputs valid CSV with required headers."""
        mark_attendance(
            self.test_student_id,
            session_id="TEST_SESSION_X",
            custom_dt=datetime(2026, 11, 15, 8, 30, 0)
        )
        records = get_filtered_attendance(student_id=self.test_student_id)
        csv_str = generate_attendance_csv(records)

        self.assertIsInstance(csv_str, str)
        # Check header columns
        self.assertIn("StudentID,Name,Date,Time,Status,SessionID", csv_str)
        # Check that test record exists in export
        self.assertIn(self.test_student_id, csv_str)


if __name__ == "__main__":
    unittest.main()
