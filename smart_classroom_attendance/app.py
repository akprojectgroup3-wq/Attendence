"""Flask application entry point for Smart Classroom Attendance System.
Sets up Flask, database, login manager and registers all route blueprints.
"""

from flask import Flask, redirect, url_for
from config import Config

# Initialise Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(Config)

# Initialise database (SQLAlchemy) and create tables
from database import init_app, db
init_app(app)

# Initialise Flask-Login
from flask_login import LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = "info"

# User loader for Flask-Login
@login_manager.user_loader
def load_user(admin_id):
    from database.models import Admin
    return Admin.query.get(int(admin_id))

# ----------------------------------------------------------------------
# Register blueprints (routes)
# ----------------------------------------------------------------------
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.student_routes import student_bp
from routes.attendance_routes import attendance_bp
from routes.report_routes import report_bp
from routes.settings_routes import settings_bp
from routes.camera_routes import camera_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(student_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(report_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(camera_bp)

# ----------------------------------------------------------------------
# Home route – redirect based on authentication status
# ----------------------------------------------------------------------
@app.route('/')
def index():
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

# ----------------------------------------------------------------------
# CLI command to initialise the DB and create a default admin account
# ----------------------------------------------------------------------
@app.cli.command('initdb')
def initdb_command():
    """Initialise the SQLite database and create a default admin user."""
    from database.database import create_default_admin
    create_default_admin()
    print('Database initialised and default admin created (username: admin, password: admin123).')

if __name__ == '__main__':
    # Ensure upload and model directories exist
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MODEL_DIR'], exist_ok=True)
    app.run(host='127.0.0.1', port=5000, debug=True)
