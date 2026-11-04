"""Flask Application Controller for AI & IoT Smart Classroom Attendance System.

Provides authentication, web routing, REST API endpoints, video streaming,
and integration between computer vision, student management, and data persistence.
"""

from functools import wraps
import io
import time
import cv2
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    Response
)

from config import Config, load_settings, save_settings
# New report imports
from datetime import datetime
from services.report_service import build_report_context
from services.pdf_report_service import generate_pdf
from services.excel_report_service import generate_excel
from services.storage_service import (
    init_storage,
    sync_admin_password_from_env,
    verify_user,
    update_admin_password
)
from services.student_service import (
    get_all_students,
    get_student_by_id,
    add_student,
    update_student,
    delete_student
)
from services.attendance_service import (
    get_daily_summary,
    get_weekly_analytics,
    get_filtered_attendance,
    generate_attendance_csv
)
from services.face_registration import (
    decode_base64_image,
    register_face_sample,
    finish_student_registration
)

from services.model_training import train_lbph_model
from services.face_recognition_service import recognition_service
from services.esp32_cam_service import esp32_cam_service

app = Flask(__name__)
app.config.from_object(Config)

# Initialize CSV storage files and default admin credentials on startup
init_storage()
sync_admin_password_from_env()


# ==========================================
# AUTHENTICATION & ACCESS CONTROL
# ==========================================

def login_required(f):
    """Decorator to protect administrative views against unauthenticated access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_global_settings():
    """Inject active settings into all Jinja2 templates."""
    return {"settings": load_settings()}


@app.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page and credential verification."""
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = verify_user(username, password)
        if user:
            session["logged_in"] = True
            session["user"] = username
            session["full_name"] = user.get("full_name", "Administrator")
            session["role"] = user.get("role", "admin")
            flash("Welcome back, Administrator!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))
        else:
            flash("Invalid username or password. Please try again.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear session and log out."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard displaying live statistics, charts, and today's scans."""
    date_filter = request.args.get("date")
    summary = get_daily_summary(date_filter)
    weekly_data = get_weekly_analytics()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        summary=summary,
        weekly_data=weekly_data
    )


# ==========================================
# STUDENT MANAGEMENT
# ==========================================

@app.route("/students")
@login_required
def students_page():
    """Display student directory with search, filter, and management actions."""
    search_query = request.args.get("search")
    dept = request.args.get("dept")
    status = request.args.get("status")

    students = get_all_students(
        search_query=search_query,
        department=dept,
        face_status=status
    )

    return render_template(
        "students.html",
        active_page="students",
        students=students,
        search_query=search_query,
        selected_dept=dept,
        selected_status=status
    )


@app.route("/api/students/add", methods=["POST"])
@login_required
def api_add_student():
    """API endpoint to enroll a new student."""
    data = request.get_json() or {}
    student_id = data.get("student_id", "")
    name = data.get("name", "")
    class_dept = data.get("class_dept", "")
    year_sem = data.get("year_sem", "")
    email = data.get("email", "")

    success, msg, new_student = add_student(
        student_id=student_id,
        name=name,
        class_department=class_dept,
        year_semester=year_sem,
        email=email
    )

    return jsonify({"success": success, "message": msg, "student": new_student}), (200 if success else 400)


@app.route("/api/students/update", methods=["POST"])
@login_required
def api_update_student():
    """API endpoint to edit student details."""
    data = request.get_json() or {}
    student_id = data.get("student_id", "")
    name = data.get("name", "")
    class_dept = data.get("class_dept", "")
    year_sem = data.get("year_sem", "")
    email = data.get("email", "")

    success, msg = update_student(
        student_id=student_id,
        name=name,
        class_department=class_dept,
        year_semester=year_sem,
        email=email
    )

    return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route("/api/students/delete", methods=["POST"])
@login_required
def api_delete_student():
    """API endpoint to remove student and their face dataset."""
    data = request.get_json() or {}
    student_id = data.get("student_id", "")

    success, msg = delete_student(student_id)
    if success:
        # Reload recognition model since a student was removed
        recognition_service.load_model()

    return jsonify({"success": success, "message": msg}), (200 if success else 400)


# ==========================================
# FACE REGISTRATION & MODEL TRAINING
# ==========================================

@app.route("/register-face")
@login_required
def register_face_page():
    """Face registration workflow page."""
    preselected_id = request.args.get("student_id", "")
    students = get_all_students()

    return render_template(
        "register_face.html",
        active_page="register_face",
        students=students,
        preselected_id=preselected_id
    )


@app.route("/api/register-face/sample", methods=["POST"])
@login_required
def api_register_face_sample():
    """API endpoint to validate and persist a single face capture."""
    data = request.get_json() or {}
    student_id = data.get("student_id", "")
    image_data_uri = data.get("image_data", "")
    target_count = int(data.get("target_count", 25))

    img_bgr = decode_base64_image(image_data_uri)
    if img_bgr is None:
        return jsonify({"success": False, "message": "Failed to decode image data."}), 400

    success, msg, meta = register_face_sample(student_id, img_bgr, target_count=target_count)
    return jsonify({"success": success, "message": msg, "meta": meta}), (200 if success else 400)


@app.route("/api/train-model", methods=["POST"])
@login_required
def api_train_model():
    """API endpoint to train or retrain LBPH face recognizer on dataset."""
    success, msg, meta = train_lbph_model()
    if success:
        # Hot-reload model into recognition service
        recognition_service.load_model()
    return jsonify({"success": success, "message": msg, "meta": meta}), (200 if success else 400)


# ==========================================
# LIVE ATTENDANCE & RECOGNITION
# ==========================================

@app.route("/live-attendance")
@login_required
def live_attendance():
    """Live facial recognition camera page."""
    model_ready = recognition_service.is_ready()
    return render_template(
        "live_attendance.html",
        active_page="live",
        model_ready=model_ready
    )


@app.route("/api/live/process-frame", methods=["POST"])
@login_required
def api_process_live_frame():
    """Process a single frame sent from the browser client via Canvas."""
    data = request.get_json() or {}
    frame_data_uri = data.get("frame", "")
    auto_mark = data.get("auto_mark", True)

    frame_bgr = decode_base64_image(frame_data_uri)
    if frame_bgr is None:
        return jsonify({"success": False, "message": "Invalid frame data."}), 400

    _, events = recognition_service.process_frame(frame_bgr, auto_mark=auto_mark)
    return jsonify({"success": True, "events": events})


def generate_mjpeg_stream():
    """Generate MJPEG video stream from camera (Laptop Webcam or ESP32-CAM)."""
    settings = load_settings()
    cam_source = settings.get("camera_source", "0").strip()

    # Determine whether to use ESP32-CAM or OpenCV VideoCapture
    if cam_source.startswith("http://") or cam_source.startswith("https://"):
        # ESP32-CAM mode
        while True:
            frame = esp32_cam_service.capture_frame(cam_source)
            if frame is not None:
                annotated, _ = recognition_service.process_frame(frame, auto_mark=True)
                ret, buffer = cv2.imencode(".jpg", annotated)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            time.sleep(0.08)
    else:
        # Laptop Webcam mode
        cam_index = 0
        try:
            cam_index = int(cam_source)
        except ValueError:
            cam_index = 0

        cap = cv2.VideoCapture(cam_index)
        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break

                annotated, _ = recognition_service.process_frame(frame, auto_mark=True)
                ret, buffer = cv2.imencode(".jpg", annotated)
                if not ret:
                    continue

                frame_bytes = buffer.tobytes()
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        finally:
            cap.release()


@app.route("/video_feed")
@login_required
def video_feed():
    """MJPEG streaming route."""
    return Response(
        generate_mjpeg_stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ==========================================
# ATTENDANCE RECORDS & EXPORT
# ==========================================

@app.route("/attendance")
@login_required
def attendance_page():
    """Full attendance log with filters."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    student_id = request.args.get("student_id")
    status = request.args.get("status")

    records = get_filtered_attendance(
        start_date=start_date,
        end_date=end_date,
        student_id=student_id,
        status=status
    )

    return render_template(
        "attendance.html",
        active_page="attendance",
        records=records,
        start_date=start_date,
        end_date=end_date,
        student_id=student_id,
        selected_status=status
    )


@app.route("/export-attendance")
@login_required
def export_attendance():
    """Export filtered attendance records to CSV."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    student_id = request.args.get("student_id")
    status = request.args.get("status")

    records = get_filtered_attendance(
        start_date=start_date,
        end_date=end_date,
        student_id=student_id,
        status=status
    )

    csv_content = generate_attendance_csv(records)
    filename = f"attendance_export_{time.strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==========================================
# REPORTS & ANALYTICS
# ==========================================

# ==========================================
# REPORTS (Smart Attendance Report Generation)
# ==========================================

from datetime import datetime

@app.route("/reports")
@login_required
def reports_page():
    """Render the reports page with filters and preview tables."""
    # Extract filter parameters from query string
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    student_id = request.args.get('student_id')
    status = request.args.get('status')
    session_id = request.args.get('session_id')

    ctx = build_report_context(
        start_date=start_date,
        end_date=end_date,
        student_id=student_id,
        status=status,
        session_id=session_id,
    )
    # Add generation date for the PDF header
    ctx['generation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template(
        "reports.html",
        active_page="reports",
        **ctx,
    )

@app.route("/reports/pdf")
@login_required
def reports_pdf():
    """Generate and stream a PDF report based on current filter parameters."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    student_id = request.args.get('student_id')
    status = request.args.get('status')
    session_id = request.args.get('session_id')

    ctx = build_report_context(
        start_date=start_date,
        end_date=end_date,
        student_id=student_id,
        status=status,
        session_id=session_id,
    )
    ctx['generation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pdf_bytes = generate_pdf(ctx)
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment; filename=attendance_report.pdf'}
    )

@app.route("/reports/excel")
@login_required
def reports_excel():
    """Generate and stream an Excel workbook report based on current filters."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    student_id = request.args.get('student_id')
    status = request.args.get('status')
    session_id = request.args.get('session_id')

    ctx = build_report_context(
        start_date=start_date,
        end_date=end_date,
        student_id=student_id,
        status=status,
        session_id=session_id,
    )
    excel_bytes = generate_excel(ctx)
    return Response(
        excel_bytes,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=attendance_report.xlsx'}
    )

# ==========================================
# END OF REPORTS SECTION
# ==========================================



# ==========================================
# SETTINGS & HARDWARE CONFIGURATION
# ==========================================

@app.route("/settings")
@login_required
def settings_page():
    """Settings view for configuring attendance rules, timezone, camera, and admin profile."""
    return render_template("settings.html", active_page="settings")


@app.route("/settings/save", methods=["POST"])
@login_required
def save_settings_route():
    """Save modified settings."""
    current = load_settings()
    current["institution_name"] = request.form.get("institution_name", "").strip() or current["institution_name"]
    current["department"] = request.form.get("department", "").strip() or current["department"]
    current["semester"] = request.form.get("semester", "").strip() or current["semester"]
    current["attendance_session"] = request.form.get("attendance_session", "").strip() or current["attendance_session"]
    current["cutoff_time"] = request.form.get("cutoff_time", "09:30").strip()
    current["timezone"] = request.form.get("timezone", "Asia/Kolkata").strip()
    current["camera_source"] = request.form.get("camera_source", "0").strip()

    try:
        current["recognition_threshold"] = float(request.form.get("recognition_threshold", 75.0))
        current["duplicate_cooldown_seconds"] = int(request.form.get("duplicate_cooldown_seconds", 300))
    except ValueError:
        pass

    success = save_settings(current)
    if success:
        flash("Settings saved successfully.", "success")
    else:
        flash("Failed to save settings.", "error")

    return redirect(url_for("settings_page"))


@app.route("/settings/update-password", methods=["POST"])
@login_required
def update_password_route():
    """Change admin password securely."""
    username = session.get("user", "admin")
    current_pw = request.form.get("current_password", "")
    new_pw = request.form.get("new_password", "")
    confirm_pw = request.form.get("confirm_password", "")

    if new_pw != confirm_pw:
        flash("New passwords do not match.", "error")
        return redirect(url_for("settings_page"))

    user = verify_user(username, current_pw)
    if not user:
        flash("Current password entered is incorrect.", "error")
        return redirect(url_for("settings_page"))

    if len(new_pw) < 6:
        flash("New password must be at least 6 characters long.", "error")
        return redirect(url_for("settings_page"))

    success = update_admin_password(username, new_pw)
    if success:
        flash("Password updated successfully.", "success")
    else:
        flash("Failed to update password.", "error")

    return redirect(url_for("settings_page"))


@app.route("/api/esp32/test", methods=["POST"])
@login_required
def api_test_esp32():
    """Test connection to ESP32-CAM module."""
    data = request.get_json() or {}
    url = data.get("url")
    is_connected, msg, diag = esp32_cam_service.test_connection(url)
    return jsonify({"success": is_connected, "message": msg, "diagnostics": diag})


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AI & IoT Smart Classroom Attendance System")
    print("Server starting on http://127.0.0.1:5000")
    print("Default Admin Login: admin / admin123")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
