from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from services.student_service import StudentService
from forms.student_form import StudentForm

student_bp = Blueprint('student', __name__, url_prefix='/students')

@student_bp.route('/')
@login_required
def list_students():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    students, pagination = StudentService.get_paginated(page, search)
    return render_template('students.html', students=students, pagination=pagination, search=search)

@student_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        try:
            StudentService.create_student(form.data)
            flash('Student added successfully.', 'success')
            return redirect(url_for('student.list_students'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('add_student.html', form=form)

@student_bp.route('/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = StudentService.get_student(student_id)
    if not student:
        flash('Student not found.', 'warning')
        return redirect(url_for('student.list_students'))
    form = StudentForm(obj=student)
    if form.validate_on_submit():
        try:
            StudentService.update_student(student_id, form.data)
            flash('Student updated.', 'success')
            return redirect(url_for('student.list_students'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('edit_student.html', form=form, student=student)

@student_bp.route('/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    try:
        StudentService.deactivate_student(student_id)
        flash('Student deactivated.', 'info')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('student.list_students'))

@student_bp.route('/detail/<int:student_id>')
@login_required
def student_detail(student_id):
    student = StudentService.get_student(student_id)
    if not student:
        flash('Student not found.', 'warning')
        return redirect(url_for('student.list_students'))
    return render_template('student_detail.html', student=student)

@student_bp.route('/register_face/<int:student_id>')
@login_required
def register_face(student_id):
    # Placeholder page – actual face capture handled by JS + AI module later
    return render_template('face_registration.html', student_id=student_id)
