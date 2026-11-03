from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

report_bp = Blueprint('report', __name__, url_prefix='/reports')

@report_bp.route('/')
@login_required
def reports_page():
    # Placeholder – later will include filters and download buttons
    return render_template('reports.html')
