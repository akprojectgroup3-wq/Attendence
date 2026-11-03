'''PDF Report Service – generates a professional attendance PDF using ReportLab.

The layout follows the specification: college header, summary KPIs, and a table with alternating row colours.
All data is supplied by `report_service.build_report_context` – no fake records.
''' 

from io import BytesIO
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)


def _header_paragraph(text: str, style_name: str = 'Heading1'):
    styles = getSampleStyleSheet()
    style = styles[style_name]
    return Paragraph(text, style)


def generate_pdf(report_context: Dict) -> bytes:
    """Return a PDF file (bytes) for the given report context.

    The context is the dict returned by `report_service.build_report_context`.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

    elements: List = []
    # ----- Header -----
    college_name = "Samskruti College of Engineering and Technology"
    department = "AIML"
    title = "AI and IoT Smart Classroom Attendance System"
    subtitle = "Student Attendance Report"
    generation_date = f"Report generated on: {report_context.get('generation_date', '')}"

    elements.append(_header_paragraph(college_name, 'Title'))
    elements.append(_header_paragraph(department, 'Heading2'))
    elements.append(_header_paragraph(title, 'Heading3'))
    elements.append(_header_paragraph(subtitle, 'Heading4'))
    elements.append(_header_paragraph(generation_date, 'Normal'))
    elements.append(Spacer(1, 12))

    # ----- Summary KPIs -----
    stats = report_context.get('report_stats', {})
    summary_data = [
        ['Total Registered Students', stats.get('total_students', 'N/A')],
        ['Present Students', stats.get('total_present', 'N/A')],
        ['Late Students', stats.get('total_late', 'N/A')],
        ['Absent Students', stats.get('total_absent', 'N/A')],
        ['Overall Attendance %', f"{stats.get('overall_attendance_pct', 0)}%"],
    ]
    summary_table = Table(summary_data, colWidths=[80*mm, 40*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 12))

    # ----- Attendance Details Table -----
    attendance = report_context.get('preview_records', [])
    if attendance:
        table_data = [
            ['Student ID', 'Student Name', 'Date', 'Attendance Time', 'Status', 'Session ID']
        ]
        for i, rec in enumerate(attendance):
            row = [
                rec.get('StudentID', ''),
                rec.get('Name', ''),
                rec.get('Date', ''),
                rec.get('Time', ''),
                rec.get('Status', ''),
                rec.get('SessionID', ''),
            ]
            table_data.append(row)
        col_widths = [30*mm, 45*mm, 30*mm, 30*mm, 25*mm, 30*mm]
        att_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        att_table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ])
        # Alternating row background
        for row_idx in range(1, len(table_data)):
            bg = colors.whitesmoke if row_idx % 2 == 0 else colors.lightgrey
            att_table_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), bg)
        # Color‑code status cells
        for row_idx, rec in enumerate(attendance, start=1):
            status = rec.get('Status', '').strip().capitalize()
            if status == 'Present':
                col = colors.green
            elif status == 'Late':
                col = colors.orange
            else:
                col = colors.red
            att_table_style.add('TEXTCOLOR', (4, row_idx), (4, row_idx), col)
        att_table.setStyle(att_table_style)
        elements.append(att_table)
    else:
        elements.append(Paragraph('No attendance records match the selected criteria.', getSampleStyleSheet()['Normal']))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
