'''Report Service – core logic for the Smart Attendance Reports

Provides functions to:
* Filter attendance records based on date range, student, status, session.
* Compute aggregate statistics (total counts, percentages).
* Build per‑student attendance summaries used by PDF/Excel generators and the HTML preview.

All calculations are performed on the real CSV storage – no fake data is introduced.
''' 

from typing import List, Dict, Optional
from datetime import datetime

from services.attendance_service import (
    get_filtered_attendance,
    get_daily_summary,
)
from services.student_service import get_all_students
from services.storage_service import read_all_attendance


def _date_range_from_params(start_date: Optional[str], end_date: Optional[str]) -> (Optional[str], Optional[str]):
    """Validate and normalise date strings (YYYY‑MM‑DD). Return (start, end) or (None, None)."""
    # The frontend already supplies ISO dates via <input type="date">; we just pass them through.
    # Empty strings are treated as None.
    start = start_date.strip() if start_date else None
    end = end_date.strip() if end_date else None
    return start, end


def build_report_context(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    student_id: Optional[str] = None,
    status: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict:
    """Collect all data required by the reports page and by the export services.

    Returns a dictionary with keys used in the Jinja template:
    * all_students – list of student dicts (for the filter dropdown)
    * selected_student_id – the currently selected student (if any)
    * start_date / end_date – original query values (for UI persistence)
    * report_stats – aggregate numbers (total, present, late, absent, overall %)
    * student_summaries – list of per‑student dicts containing counts and percentages
    * preview_records – raw attendance rows to show in the preview table (limited to 200 rows for speed)
    """
    start, end = _date_range_from_params(start_date, end_date)

    # ------- Filtered attendance records -------
    filtered = get_filtered_attendance(
        start_date=start,
        end_date=end,
        student_id=student_id,
        status=status,
        session_id=session_id,
    )

    # Aggregate statistics (total records, present, late, absent)
    total_records = len(filtered)
    total_present = sum(1 for r in filtered if r.get('Status', '').strip().capitalize() == 'Present')
    total_late = sum(1 for r in filtered if r.get('Status', '').strip().capitalize() == 'Late')
    # Absent is derived from total registered students minus those who have any record in the filtered set.
    all_students = get_all_students()
    total_students = len(all_students)
    attended_student_ids = {r.get('StudentID', '').strip().upper() for r in filtered}
    total_absent = max(0, total_students - len(attended_student_ids))
    denominator = total_present + total_late + total_absent
    overall_pct = round((total_present + total_late) / denominator * 100, 1) if denominator > 0 else 0.0

    report_stats = {
        'total_records': total_records,
        'total_present': total_present,
        'total_late': total_late,
        'total_absent': total_absent,
        'overall_attendance_pct': overall_pct,
    }

    # ------- Per‑student summary -------
    # Build a lookup of counts per student within the filtered range.
    per_student_counts: Dict[str, Dict[str, int]] = {}
    for r in filtered:
        sid = r.get('StudentID', '').strip().upper()
        if not sid:
            continue
        status = r.get('Status', '').strip().capitalize()
        if sid not in per_student_counts:
            per_student_counts[sid] = {'present': 0, 'late': 0}
        if status == 'Present':
            per_student_counts[sid]['present'] += 1
        elif status == 'Late':
            per_student_counts[sid]['late'] += 1

    student_summaries = []
    for student in all_students:
        sid = student.get('StudentID', '').strip().upper()
        counts = per_student_counts.get(sid, {'present': 0, 'late': 0})
        present = counts['present']
        late = counts['late']
        total_attended = present + late
        # Sessions the student could have attended = number of distinct dates in the filtered range.
        # If no date filter, we treat the period as all dates present in the attendance CSV.
        if start and end:
            # Build a set of dates from filtered records – this matches the period the user selected.
            dates_set = {r.get('Date', '').strip() for r in filtered}
        else:
            # No date constraints – use every date that appears in the full attendance file.
            dates_set = {r.get('Date', '').strip() for r in read_all_attendance()}
        total_sessions = len(dates_set)
        if total_sessions == 0:
            percentage = None  # N/A – no sessions to evaluate
        else:
            percentage = round((present + late) / total_sessions * 100, 1)
        student_summaries.append({
            'student': student,
            'present': present,
            'late': late,
            'total_attended': total_attended,
            'percentage': percentage,
        })

    # Sort summaries by attendance percentage descending, treating None as lowest.
    student_summaries.sort(key=lambda x: (x['percentage'] is not None, x['percentage']), reverse=True)

    # Limit preview rows to keep the page responsive.
    preview_records = filtered[:200]

    return {
        'all_students': all_students,
        'selected_student_id': student_id or '',
        'start_date': start,
        'end_date': end,
        'report_stats': report_stats,
        'student_summaries': student_summaries,
        'preview_records': preview_records,
    }
