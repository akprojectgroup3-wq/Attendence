# AI & IoT Smart Classroom Attendance System

## Project Overview
This repository implements a complete AI‑powered, IoT‑enabled smart classroom attendance system using **face recognition**. It provides:
- Admin login & session management
- Student registration and face data collection
- Real‑time attendance capture via laptop webcam (and optional ESP32‑CAM)
- Automatic present/late/absent calculation based on configurable cutoff time
- Dashboard with statistics and Chart.js visualisations
- PDF and Excel report generation
- Secure storage of student data and attendance records in SQLite
- Fully responsive UI built with Bootstrap 5

The system is designed for a diploma final‑year project and runs on Windows with Python 3.11.

---

## Folder Structure
```
smart_classroom_attendance/
│   app.py                 # Flask application entry point
│   config.py              # Application configuration
│   requirements.txt
│   README.md
│   .gitignore
│
├── database/
│   │   database.py        # DB engine & helper functions
│   │   models.py          # SQLAlchemy models
│   │   smart_attendance.db   # SQLite database (generated)
│
├── ai/
│   │   face_detection.py
│   │   face_recognition.py
│   │   face_registration.py
│   │   train_model.py
│   │   model/            # Trained recogniser files
│
├── attendance/
│   │   attendance_service.py
│   │   attendance_rules.py
│   │   attendance_reports.py
│
├── iot/
│   │   esp32_camera.py
│   │   camera_service.py
│   │   esp32_firmware/   # Arduino sketch (placeholder)
│
├── routes/
│   │   auth_routes.py
│   │   dashboard_routes.py
│   │   student_routes.py
│   │   attendance_routes.py
│   │   report_routes.py
│   │   settings_routes.py
│   │   camera_routes.py
│
├── services/
│   │   student_service.py
│   │   report_service.py
│   │   dashboard_service.py
│
├── templates/
│   │   base.html
│   │   login.html
│   │   dashboard.html
│   │   ... (other pages)
│
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── images/
│
├── exports/               # Generated PDF/Excel files
├── uploads/student_faces/  # Stored face images per student
└── tests/                 # Automated unit tests
```