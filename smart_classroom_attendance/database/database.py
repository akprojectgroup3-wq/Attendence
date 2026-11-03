from . import db, init_app
from .models import Admin, Setting
from werkzeug.security import generate_password_hash

def create_default_admin():
    """Create a default admin user and initial settings if they don't exist."""
    if not Admin.query.first():
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        # Default settings
        defaults = [
            Setting(name='college_name', value='SAMSKRUTI COLLEGE OF ENGINEERING AND TECHNOLOGY'),
            Setting(name='department_name', value='Department of Artificial Intelligence and Machine Learning'),
            Setting(name='attendance_cutoff', value='09:30'),
            Setting(name='timezone', value='Asia/Kolkata'),
            Setting(name='camera_source', value='Laptop Webcam'),
            Setting(name='recognition_threshold', value='70'),
        ]
        db.session.bulk_save_objects(defaults)
        db.session.commit()
    else:
        # Ensure settings exist
        needed = {
            'college_name': 'SAMSKRUTI COLLEGE OF ENGINEERING AND TECHNOLOGY',
            'department_name': 'Department of Artificial Intelligence and Machine Learning',
            'attendance_cutoff': '09:30',
            'timezone': 'Asia/Kolkata',
            'camera_source': 'Laptop Webcam',
            'recognition_threshold': '70',
        }
        for name, value in needed.items():
            if not Setting.query.filter_by(name=name).first():
                db.session.add(Setting(name=name, value=value))
        db.session.commit()
