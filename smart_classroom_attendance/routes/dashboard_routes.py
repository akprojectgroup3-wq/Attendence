from flask import Blueprint, render_template

# Placeholder – real stats will be added later

@dashboard_bp.route('/')
def dashboard():
    return render_template('dashboard.html')
