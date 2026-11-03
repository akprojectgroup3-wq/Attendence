"""Attendance tracking and management service.

Handles attendance recording, cutoff time validation (Present vs Late),
duplicate scan prevention, session tracking, daily absent calculation,
and historical analytics.
"""

from datetime import datetime, timedelta, time as dt_time
import io
import csv
from typing import List, Dict, Tuple, Optional

from config import load_settings, get_current_time
from services.storage_service import (
    read_all_attendance,
    append_attendance
)
from services.student_service import get_all_students, get_student_by_id


def parse_time_str(time_str: str) -> dt_time:
    """Parse a 'HH:MM' or 'HH:MM:SS' string into a datetime.time object."""
    parts = [int(p) for p in time_str.strip().split(":")]
    if len(parts) == 2:
        return dt_time(hour=parts[0], minute=parts[1])
    elif len(parts) >= 3:
        return dt_time(hour=parts[0], minute=parts[1], second=parts[2])
    return dt_time(hour=9, minute=30)


def determine_attendance_status(current_dt: datetime, cutoff_str: str = "09:30") -> str:
    """Determine attendance status based on cutoff time.

    - Scanned strictly before cutoff: 'Present'
    - Scanned at or after cutoff: 'Late'
    """
    cutoff = parse_time_str(cutoff_str)
    scan_time = current_dt.time()
    if scan_time < cutoff:
        return "Present"
    return "Late"


def is_already_marked(student_id: str, date_str: str, session_id: str) -> Tuple[bool, Optional[Dict[str, str]]]:
    """Check if the student has already been marked for the given date and session."""
    student_id = student_id.strip().upper()
    session_id = session_id.strip().upper()
    records = read_all_attendance()

    for record in records:
        r_id = record.get("StudentID", "").strip().upper()
        r_date = record.get("Date", "").strip()
        r_session = record.get("SessionID", "").strip().upper()

        if r_id == student_id and r_date == date_str:
            # If session is specified, match session as well
            if not session_id or not r_session or r_session == session_id:
                return True, record
    return False, None


def mark_attendance(
    student_id: str,
    session_id: Optional[str] = None,
    custom_dt: Optional[datetime] = None
) -> Tuple[bool, str, Optional[Dict[str, str]]]:
    """Mark attendance for a registered student.

    Validates student identity, prevents duplicate records for the date/session,
    and applies cutoff time rules.
    """
    student_id = student_id.strip().upper()
    student = get_student_by_id(student_id)
    if not student:
        return False, f"Cannot mark attendance: Student ID '{student_id}' is not registered.", None

    settings = load_settings()
    session = session_id or settings.get("attendance_session", "SESSION_1")
    cutoff_str = settings.get("cutoff_time", "09:30")

    now = custom_dt or get_current_time(settings.get("timezone", "Asia/Kolkata"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # Check for duplicate scan
    already_marked, existing_rec = is_already_marked(student_id, date_str, session)
    if already_marked:
        status = existing_rec.get("Status", "Present")
        time_marked = existing_rec.get("Time", "")
        return (
            False,
            f"{student['Name']} ({student_id}) was already marked '{status}' today at {time_marked}.",
            existing_rec
        )

    # Calculate status: Present if before cutoff, Late if at or after
    status = determine_attendance_status(now, cutoff_str)

    record = {
        "StudentID": student_id,
        "Name": student["Name"],
        "Date": date_str,
        "Time": time_str,
        "Status": status,
        "SessionID": session
    }

    success = append_attendance(record)
    if success:
        return True, f"Attendance recorded: {student['Name']} marked '{status}' at {time_str}.", record
    return False, "Failed to persist attendance record to storage.", None


def get_today_records(date_str: Optional[str] = None) -> List[Dict[str, str]]:
    """Retrieve all attendance records for a specific date (defaults to today)."""
    if not date_str:
        now = get_current_time()
        date_str = now.strftime("%Y-%m-%d")

    records = read_all_attendance()
    return [r for r in records if r.get("Date", "").strip() == date_str]


def get_daily_summary(date_str: Optional[str] = None, session_id: Optional[str] = None) -> Dict:
    """Calculate daily summary statistics including Present, Late, and Absent students.

    Absent students are derived by comparing registered students with scanned records.
    """
    if not date_str:
        now = get_current_time()
        date_str = now.strftime("%Y-%m-%d")

    all_students = get_all_students()
    total_students = len(all_students)

    today_records = get_today_records(date_str)
    if session_id:
        today_records = [
            r for r in today_records
            if r.get("SessionID", "").strip().upper() == session_id.strip().upper()
        ]

    scanned_ids = set()
    present_count = 0
    late_count = 0

    for r in today_records:
        sid = r.get("StudentID", "").strip().upper()
        scanned_ids.add(sid)
        status = r.get("Status", "").strip().capitalize()
        if status == "Present":
            present_count += 1
        elif status == "Late":
            late_count += 1

    # Absent students: all registered students who did not scan today
    absent_students = [
        s for s in all_students
        if s.get("StudentID", "").strip().upper() not in scanned_ids
    ]
    absent_count = len(absent_students)

    attended_count = present_count + late_count
    attendance_rate = round((attended_count / total_students * 100), 1) if total_students > 0 else 0.0

    return {
        "date": date_str,
        "total_students": total_students,
        "present_count": present_count,
        "late_count": late_count,
        "absent_count": absent_count,
        "attended_count": attended_count,
        "attendance_rate": attendance_rate,
        "today_records": today_records,
        "absent_students": absent_students
    }


def get_weekly_analytics() -> Dict:
    """Get 7-day attendance trend breakdown for Chart.js."""
    now = get_current_time()
    labels = []
    present_series = []
    late_series = []
    absent_series = []

    all_students = get_all_students()
    total_students = len(all_students)
    all_records = read_all_attendance()

    # Pre-index records by date
    records_by_date: Dict[str, List[Dict[str, str]]] = {}
    for r in all_records:
        d = r.get("Date", "").strip()
        records_by_date.setdefault(d, []).append(r)

    # Last 7 days backwards up to today
    for i in range(6, -1, -1):
        day_dt = now - timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        day_label = day_dt.strftime("%a (%d %b)")
        labels.append(day_label)

        day_records = records_by_date.get(day_str, [])
        p_cnt = sum(1 for r in day_records if r.get("Status", "").strip().capitalize() == "Present")
        l_cnt = sum(1 for r in day_records if r.get("Status", "").strip().capitalize() == "Late")
        attended_ids = {r.get("StudentID", "").strip().upper() for r in day_records}
        a_cnt = max(0, total_students - len(attended_ids))

        present_series.append(p_cnt)
        late_series.append(l_cnt)
        absent_series.append(a_cnt)

    return {
        "labels": labels,
        "present": present_series,
        "late": late_series,
        "absent": absent_series
    }


def get_filtered_attendance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    student_id: Optional[str] = None,
    status: Optional[str] = None,
    session_id: Optional[str] = None
) -> List[Dict[str, str]]:
    """Query attendance records matching search filters."""
    records = read_all_attendance()
    filtered = []

    for r in records:
        r_date = r.get("Date", "").strip()
        r_id = r.get("StudentID", "").strip().upper()
        r_status = r.get("Status", "").strip().capitalize()
        r_session = r.get("SessionID", "").strip().upper()

        if start_date and r_date < start_date:
            continue
        if end_date and r_date > end_date:
            continue
        if student_id and student_id.strip().upper() != r_id:
            continue
        if status and status.strip().capitalize() != r_status:
            continue
        if session_id and session_id.strip().upper() != r_session:
            continue

        filtered.append(r)

    # Sort descending by Date, then Time
    filtered.sort(key=lambda x: (x.get("Date", ""), x.get("Time", "")), reverse=True)
    return filtered


def generate_attendance_csv(records: List[Dict[str, str]]) -> str:
    """Generate RFC-4180 CSV string for downloading or exporting records."""
    output = io.StringIO()
    headers = ["StudentID", "Name", "Date", "Time", "Status", "SessionID"]
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for r in records:
        writer.writerow({k: r.get(k, "") for k in headers})
    return output.getvalue()
