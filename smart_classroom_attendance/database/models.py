from datetime import datetime, date, time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# The db instance will be imported from database/__init__.py
from . import db

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), unique=True, nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    department = db.Column(db.String(64))
    academic_year = db.Column(db.String(8))
    semester = db.Column(db.String(8))
    email = db.Column(db.String(128))
    registration_date = db.Column(db.Date, default=datetime.utcnow().date)
    face_registered = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)

    attendances = db.relationship('Attendance', backref='student', lazy='dynamic')

class ClassSession(db.Model):
    __tablename__ = 'class_sessions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    department = db.Column(db.String(64))
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    attendances = db.relationship('Attendance', backref='session', lazy='dynamic')

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('class_sessions.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    time = db.Column(db.Time, default=datetime.utcnow().time, nullable=False)
    status = db.Column(db.String(8), nullable=False)  # Present / Late / Absent
    camera_source = db.Column(db.String(32), nullable=False)

    __table_args__ = (db.UniqueConstraint('student_id', 'session_id', name='uq_student_session'),)

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.String(256), nullable=False)
