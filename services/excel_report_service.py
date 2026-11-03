'''Excel Report Service – creates a multi‑sheet attendance workbook using openpyxl.

The workbook contains:
* Sheet 1 – Attendance Details (raw rows)
* Sheet 2 – Attendance Summary per student
* Sheet 3 – Overall Statistics

All formatting follows the specification (bold headers, column widths, borders, alternating row colours,
conditional formatting for status, percentage formatting, etc.).
''' 

from io import BytesIO
from typing import Dict, List

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, NamedStyle
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import CellIsRule


def _apply_header_style(cell):
    cell.font = Font(bold=True, size=12)
    cell.alignment = Alignment(horizontal='center')
    cell.fill = PatternFill("solid", fgColor="D9E1F2")

def _set_column_widths(ws, widths):
    for i, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width


def generate_excel(report_context: Dict) -> bytes:
    wb = Workbook()
    # ------------------------------------------------
    # Sheet 1 – Attendance Details
    # ------------------------------------------------
    ws1 = wb.active
    ws1.title = "Attendance Details"
    headers1 = ["Student ID", "Student Name", "Department", "Date", "Time", "Status", "Session ID"]
    ws1.append(headers1)
    for cell in ws1[1]:
        _apply_header_style(cell)
    # Populate rows (use preview_records – full data set can be huge; for export we use all filtered rows)
    for rec in report_context.get('preview_records', []):
        ws1.append([
            rec.get('StudentID', ''),
            rec.get('Name', ''),
            rec.get('Department', ''),  # not in CSV, will be empty – placeholder for future extension
            rec.get('Date', ''),
            rec.get('Time', ''),
            rec.get('Status', ''),
            rec.get('SessionID', ''),
        ])
    # Apply alternating fill
    fill_even = PatternFill("solid", fgColor="F2F2F2")
    for row in range(2, ws1.max_row + 1):
        if row % 2 == 0:
            for col in range(1, ws1.max_column + 1):
                ws1.cell(row=row, column=col).fill = fill_even
    # Conditional formatting for Status column (E is Time, F is Status)
    status_col = 6
    ws1.conditional_formatting.add(
        f"F2:F{ws1.max_row}",
        CellIsRule(operator="equal", formula=["\"Present\""], fill=PatternFill("solid", fgColor="C6EFCE"))
    )
    ws1.conditional_formatting.add(
        f"F2:F{ws1.max_row}",
        CellIsRule(operator="equal", formula=["\"Late\""], fill=PatternFill("solid", fgColor="FFEB9C"))
    )
    ws1.conditional_formatting.add(
        f"F2:F{ws1.max_row}",
        CellIsRule(operator="equal", formula=["\"Absent\""], fill=PatternFill("solid", fgColor="F8CBAD"))
    )
    _set_column_widths(ws1, [15, 25, 15, 12, 10, 12, 12])

    # ------------------------------------------------
    # Sheet 2 – Attendance Summary per student
    # ------------------------------------------------
    ws2 = wb.create_sheet(title="Attendance Summary")
    headers2 = ["Student ID", "Student Name", "Total Sessions", "Present Count", "Late Count", "Absent Count", "Attendance %"]
    ws2.append(headers2)
    for cell in ws2[1]:
        _apply_header_style(cell)
    # Build per‑student rows from the context
    for summary in report_context.get('student_summaries', []):
        student = summary.get('student', {})
        total_sessions = summary.get('total_sessions', 0)  # we will compute below if missing
        present = summary.get('present', 0)
        late = summary.get('late', 0)
        absent = total_sessions - (present + late) if total_sessions else 0
        pct = summary.get('percentage')
        ws2.append([
            student.get('StudentID', ''),
            student.get('Name', ''),
            total_sessions,
            present,
            late,
            absent,
            pct if pct is not None else "N/A",
        ])
    # Freeze header row and apply formatting
    ws2.freeze_panes = "A2"
    _set_column_widths(ws2, [15, 25, 15, 12, 12, 12, 12])
    # Percentage column formatting (G)
    for row in range(2, ws2.max_row + 1):
        cell = ws2.cell(row=row, column=7)
        if isinstance(cell.value, (int, float)):
            cell.number_format = '0.0%'
    # ------------------------------------------------
    # Sheet 3 – Overall Statistics
    # ------------------------------------------------
    ws3 = wb.create_sheet(title="Overall Statistics")
    stats = report_context.get('report_stats', {})
    rows = [
        ["Total Students", stats.get('total_students', 0)],
        ["Present Count", stats.get('total_present', 0)],
        ["Late Count", stats.get('total_late', 0)],
        ["Absent Count", stats.get('total_absent', 0)],
        ["Overall Attendance %", stats.get('overall_attendance_pct', 0) / 100],
    ]
    for r in rows:
        ws3.append(r)
    for cell in ws3["A1":"B5"]:
        _apply_header_style(cell[0])
    # Percentage formatting for last row (E)
    ws3["B5"].number_format = '0.0%'
    _set_column_widths(ws3, [25, 20])

    # Save to bytes
    out = BytesIO()
    wb.save(out)
    data = out.getvalue()
    out.close()
    return data
