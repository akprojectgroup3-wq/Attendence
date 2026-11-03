import math
from flask import current_app
from sqlalchemy import or_
from ..database.models import Student, db

class StudentService:
    @staticmethod
    def get_paginated(page: int = 1, search: str = '', per_page: int = 10):
        query = Student.query.filter(Student.active == True)
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(Student.student_id.ilike(like),
                    Student.full_name.ilike(like),
                    Student.department.ilike(like))
            )
        total = query.count()
        students = query.order_by(Student.id).offset((page - 1) * per_page).limit(per_page).all()
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': math.ceil(total / per_page) if per_page else 0,
            'has_next': page * per_page < total,
            'has_prev': page > 1,
        }
        return students, pagination

    @staticmethod
    def create_student(data: dict):
        # Ensure uniqueness of student_id
        if Student.query.filter_by(student_id=data['student_id']).first():
            raise ValueError('Student ID already exists.')
        student = Student(
            student_id=data['student_id'],
            full_name=data['full_name'],
            department=data.get('department'),
            academic_year=data.get('academic_year'),
            semester=data.get('semester'),
            email=data.get('email'),
            active=data.get('active', True)
        )
        db.session.add(student)
        db.session.commit()
        return student

    @staticmethod
    def get_student(student_id: int):
        return Student.query.get(student_id)

    @staticmethod
    def update_student(student_id: int, data: dict):
        student = StudentService.get_student(student_id)
        if not student:
            raise ValueError('Student not found.')
        # If changing student_id, enforce uniqueness
        new_sid = data.get('student_id')
        if new_sid and new_sid != student.student_id:
            if Student.query.filter_by(student_id=new_sid).first():
                raise ValueError('Student ID already exists.')
            student.student_id = new_sid
        student.full_name = data.get('full_name', student.full_name)
        student.department = data.get('department', student.department)
        student.academic_year = data.get('academic_year', student.academic_year)
        student.semester = data.get('semester', student.semester)
        student.email = data.get('email', student.email)
        student.active = data.get('active', student.active)
        db.session.commit()
        return student

    @staticmethod
    def deactivate_student(student_id: int):
        student = StudentService.get_student(student_id)
        if not student:
            raise ValueError('Student not found.')
        student.active = False
        db.session.commit()
        return student
