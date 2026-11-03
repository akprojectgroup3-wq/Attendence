# AI and IoT Smart Classroom Attendance System Using Face Recognition

![System Status](https://img.shields.io/badge/Status-Complete%20%26%20Tested-brightgreen)
![Python Version](https://img.shields.io/badge/Python-3.10%20--%203.13-blue)
![Framework](https://img.shields.io/badge/Framework-Flask%203.1-black)
![AI Model](https://img.shields.io/badge/AI%20Model-OpenCV%20LBPH-orange)
![IoT Hardware](https://img.shields.io/badge/IoT-AI--Thinker%20ESP32--CAM-red)

A comprehensive, production-grade college diploma and final-year engineering capstone project. This system eliminates manual paper attendance by employing computer vision face recognition (OpenCV LBPH) to automatically identify students, check in their attendance against campus cutoff rules, flag late arrivals, calculate absent students, and provide administrators with real-time dashboards and downloadable CSV reports.

---

## Key Features

1. **Modern Smart-Campus Dashboard:**
   - Real-time statistics: Total Registered Students, Present (On-Time), Late Arrivals, Absent (Unmarked), and Attendance Compliance %.
   - Interactive visual charts powered by **Chart.js** (7-day stacked trend chart and today's distribution donut chart).
   - Live date selector to audit attendance for any historical day.

2. **Automated Attendance Cutoff Logic:**
   - Configurable cutoff time (default: **9:30 AM**).
   - **Before 9:30 AM:** Automatically marked **Present**.
   - **At or after 9:30 AM:** Automatically marked **Late**.
   - Configurable timezone (defaults to **Asia/Kolkata** / IST +05:30).
   - **Absent Calculation:** For each class session, absent students are dynamically determined by comparing all registered students against scanned attendance records.

3. **Facial Biometric Enrollment & Training:**
   - 25-frame burst capture with live webcam preview and visual head-pose guidance (*Center, Tilt Left, Tilt Right, Smile*).
   - Pre-capture Student Consent & Privacy agreement check.
   - Quality control: Automatically rejects frames where no face or multiple faces are detected.
   - One-click model training and real-time hot-reloading into the running recognition engine.

4. **Live Facial Recognition:**
   - Real-time facial bounding boxes with student name, ID, and confidence percentage.
   - **Unknown Rejection:** Faces not registered or falling below the configurable confidence threshold are flagged as **Unknown** and attendance is strictly **not** recorded.
   - **Duplicate Prevention:** Features both an in-memory visual cooldown timer and strict backend database duplicate prevention to prevent proxy or spam scans.
   - Built-in audio synthesizer chime on verified student check-in.

5. **IoT ESP32-CAM Module Support:**
   - Works immediately with standard **Laptop Webcams (Index 0)**.
   - Optional wireless **AI-Thinker ESP32-CAM** support via HTTP/MJPEG streaming.
   - Live network diagnostic ping button to verify camera connectivity before initiating attendance.
   - Includes full, ready-to-flash Arduino sketch in [`firmware/esp32_cam_attendance.ino`](firmware/esp32_cam_attendance.ino).

6. **Academic Security & Privacy:**
   - Protected administrative routes guarded with `@login_required` session decorators.
   - Passwords hashed using PBKDF2/SHA256 (`werkzeug.security`).
   - Clean deletion of biometric face datasets whenever a student record is removed.
   - Educational disclosure explaining basic face recognition vs. advanced 3D liveness / anti-spoofing hardware.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3 (Custom Navy & Slate Design System), Vanilla JavaScript (ES6+), Chart.js |
| **Backend** | Python, Flask 3.1, Jinja2, Werkzeug |
| **Computer Vision** | OpenCV (`opencv-contrib-python`), Haar Cascades, LBPH Face Recognizer |
| **IoT Hardware** | AI-Thinker ESP32-CAM (OV2640 Sensor, Wi-Fi HTTP Stream) |
| **Data Storage** | Thread-safe CSV storage (`threading.RLock`) with JSON settings & user credentials |
| **Testing** | Pytest, Unittest (20 comprehensive automated test cases) |

---

## Project Structure

```text
smart_classroom_attendance/
│
├── app.py                     # Main Flask web server and API routes
├── config.py                  # System paths, defaults, and timezone configuration
├── requirements.txt           # Python dependency specifications
├── .gitignore                 # Version control exclusions
├── README.md                  # Complete documentation and setup guide
│
├── services/                  # Modular business logic
│   ├── storage_service.py     # Thread-safe CSV and JSON persistence with locking
│   ├── student_service.py     # Enrollment, validation, search, and profile updates
│   ├── attendance_service.py  # Cutoff logic, duplicate prevention, and reports
│   ├── face_detection.py      # Haar Cascade detection and ROI normalization
│   ├── face_registration.py   # Multi-sample capture and dataset management
│   ├── model_training.py      # LBPH model trainer and label dictionary generator
│   ├── face_recognition_service.py # Real-time recognition, debounce, and auto-marking
│   ├── esp32_cam_service.py   # ESP32-CAM frame grabber and connection diagnostics
│   └── migrate_legacy.py      # Seeds default demo students and loads historical data
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Responsive layout, navy sidebar, and clock
│   ├── login.html             # Secure administrative login card
│   ├── dashboard.html         # Live summary cards and Chart.js analytics
│   ├── students.html          # Student directory and enrollment modals
│   ├── register_face.html     # Interactive camera face enrollment workflow
│   ├── live_attendance.html   # Real-time face recognition video feed and audit log
│   ├── attendance.html        # Historical records table and search filters
│   ├── reports.html           # Percentage breakdown and printable reports
│   └── settings.html          # Cutoff time, timezone, ESP32-CAM URL, and password
│
├── static/
│   ├── css/
│   │   └── style.css          # Professional smart-campus styling & print layout
│   └── js/                    # Client-side helpers
│
├── data/                      # Local data persistence
│   ├── students.csv           # Student records
│   ├── attendance.csv         # Attendance records with SessionID
│   ├── settings.json          # System settings
│   ├── users.json             # Hashed admin credentials
│   └── face_dataset/          # Directory of student face images (by Student ID)
│
├── models/
│   ├── trainer.yml            # Trained OpenCV LBPH model binary
│   └── labels.json            # Student ID to numeric label mapping
│
├── firmware/
│   └── esp32_cam_attendance.ino # Complete Arduino sketch for ESP32-CAM module
│
└── tests/                     # Automated test suite (20 tests)
    ├── test_auth.py           # Login, invalid credentials, protected routes
    ├── test_students.py       # Enrollment, duplicates, deletion, CSV safety
    ├── test_attendance.py     # 9:30 AM cutoff, duplicate prevention, export
    └── test_face_recognition.py # Model training, prediction, unknown rejection
```

---

## Quick Start (One-Click Launch)

Simply double-click **`start.bat`** in the project folder! It will automatically:
1. Detect and activate the Python virtual environment (`venv`).
2. Start the Flask server on `http://127.0.0.1:5000`.
3. Open your default web browser to the login dashboard.

---

## Beginner-Friendly Installation & Run Instructions (Windows)

Follow these exact steps to run the project on your Windows laptop.

### Step 1: Open the Project in VS Code
1. Launch **Visual Studio Code**.
2. Go to **File** &rarr; **Open Folder...** and select `AK PROJECT` (`c:\Users\Shane moin\OneDrive\Desktop\AK PROJECT`).
3. Open the built-in terminal by pressing `` Ctrl + ` `` (Control + Backtick) or selecting **Terminal** &rarr; **New Terminal**.

### Step 2: Set Execution Policy in PowerShell (If Blocked)
If Windows blocks PowerShell script execution, run this command in your PowerShell terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Step 3: Activate the Virtual Environment
A virtual environment named `venv` is configured in your project folder. Activate it by running:
```powershell
.\venv\Scripts\Activate.ps1
```
*(You will see `(venv)` appear at the start of your terminal prompt).*

If you ever need to create a fresh virtual environment from scratch:
```powershell
python -m venv --system-site-packages venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 4: Run the Automated Test Suite
Verify that all 20 test cases pass:
```powershell
python -m pytest tests/ -v
```
You will see all tests marked in green `PASSED`.

### Step 5: Start the Flask Application
Run the main server:
```powershell
python app.py
```
You will see output similar to:
```text
============================================================
AI & IoT Smart Classroom Attendance System
Server starting on http://127.0.0.1:5000
Default Admin Login: admin / admin123
============================================================
 * Running on http://127.0.0.1:5000
```

### Step 6: Open the Application in Your Web Browser
1. Open Google Chrome, Microsoft Edge, or Mozilla Firefox.
2. Navigate to:
   ```text
   http://127.0.0.1:5000
   ```
3. Sign in using the administrator credentials:
   - **Username:** `admin`
   - **Password:** `admin123`
   *(You can change this password at any time in the Settings page).*

---

## Step-by-Step Usage Guide

### 1. Enrolling a Student
1. Click **Student Records** in the sidebar.
2. Click **+ Add New Student**.
3. Fill in the Student ID (e.g. `STU103`), Full Name, Department, and Semester.
4. Click **Save Student**. Duplicate student IDs are strictly rejected.

### 2. Capturing Face Biometrics
1. In the Student Records list, click **Capture Face** next to the student's name, or click **Register Faces** in the sidebar.
2. Select the student from the dropdown.
3. Check the **Student Consent & Privacy Agreement** checkbox.
4. Click **Open Camera**.
5. Position your face in the blue guide overlay and click **Auto-Capture 25 Photos**. The system will guide you through slight angle changes.
6. Once 25 valid face images are saved, click **Train Recognition Model (LBPH)**. The system will compile the model in seconds and take you to Live Attendance.

### 3. Running Live Attendance
1. Click **Live Attendance** in the sidebar.
2. Click **Start Live Attendance**.
3. When registered students look at the camera, a green bounding box will highlight their face with their Name, ID, and match confidence percentage.
4. A sound chime will alert the class, and an attendance card will immediately appear in the **Real-Time Scan Activity** log on the right.
5. If the time is before **9:30 AM**, they are marked **Present**. At or after **9:30 AM**, they are marked **Late**.
6. If an unrecognized person steps in front of the camera, a red box displays **Unknown Face** and no attendance is marked.
7. Click **Stop Camera** when class commences.

### 4. Viewing the Dashboard & Absentee Reports
1. Click **Dashboard** in the sidebar.
2. View total enrolled students, present on-time count, late count, and absent list.
3. Registered students who did not scan into the active session appear automatically under the **Absent Students** list.
4. Click **Reports & Analytics** to view compliance percentages and click **Print Clean Report** for a printer-ready document.
5. Click **Attendance Log** to filter by date or student, and click **Export Filtered CSV** to download an Excel-compatible spreadsheet.

---

## IoT ESP32-CAM Setup & Integration

To transition from your laptop webcam to an autonomous wireless IoT classroom camera node:

### Hardware Requirements
- AI-Thinker ESP32-CAM development board with OV2640 camera module.
- FTDI USB-to-TTL Serial adapter (with 5V/3.3V jumper set to 5V).
- Jumper wires.

### Flashing the ESP32-CAM Firmware
1. Open the [Arduino IDE](https://www.arduino.cc/en/software).
2. Install the **esp32** board definitions via Boards Manager (`https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`).
3. Open [`firmware/esp32_cam_attendance.ino`](firmware/esp32_cam_attendance.ino).
4. Update lines 24–25 with your campus Wi-Fi network credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
5. Connect **GPIO 0 to GND** on the ESP32-CAM (enables flash mode), plug the FTDI adapter into your PC, select board **AI Thinker ESP32-CAM**, and click **Upload**.
6. After upload completes, disconnect GPIO 0 from GND and press the **RST** (Reset) button.
7. Open the Serial Monitor at **115200 baud** to see your assigned IP address (e.g. `http://192.168.1.150`).

### Connecting to Flask
1. In the Smart Classroom web interface, go to **Settings**.
2. In the **Active Camera Source** field, replace `0` with your stream URL:
   ```text
   http://192.168.1.150:81/stream
   ```
3. Click **Test ESP32-CAM Connection** to verify live communication and latency.
4. Click **Save Settings**. The system will now draw video directly from the wireless IoT module.

---

## Troubleshooting Guide

| Issue | Cause | Solution |
|---|---|---|
| `Scripts execution is disabled on this system` | Windows PowerShell execution policy | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in the terminal. |
| `Camera could not be opened` | Another application (Zoom, Teams, Camera app) is using webcam | Close any background camera applications and refresh the browser. |
| `No module named cv2.face` | Standard `opencv-python` installed instead of `opencv-contrib-python` | Ensure `opencv-contrib-python` is installed in your virtual environment. |
| `Model Not Trained Yet!` alert on Live Attendance | No faces registered yet | Go to **Register Faces**, capture 25 samples for a student, and click **Train Recognition Model**. |
| ESP32-CAM connection timed out | ESP32-CAM powered off or on a different Wi-Fi subnet | Ensure your laptop and the ESP32-CAM are connected to the same Wi-Fi router / mobile hotspot. |

---

## College Project Viva / Defense FAQ

- **Q: Which face recognition algorithm is used and why?**  
  *A:* Local Binary Pattern Histograms (LBPH). Unlike Eigenfaces or Fisherfaces, LBPH operates locally by analyzing circular neighbor pixel textures. It is computationally lightweight, operates in real time on standard CPU hardware without demanding a discrete GPU, and performs well under indoor lighting variations.

- **Q: How does the system handle proxy attendance?**  
  *A:* Face recognition requires the physical face to match the enrolled biometric model under confidence thresholding. Proxy signatures and manual roll-call manipulation are eliminated.

- **Q: Does this guarantee physical presence against photo spoofing?**  
  *A:* As noted in the system's academic disclaimer, basic 2D appearance matching is vulnerable to high-resolution screen or printed photo presentation. True anti-spoofing requires active optical flow (liveness blink detection) or hardware depth sensors (infrared structured light), which is documented as future research work.

- **Q: How is attendance data preserved?**  
  *A:* Attendance is safely appended to `data/attendance.csv` using Python's `threading.RLock` to guarantee file safety and prevent race conditions or data corruption during simultaneous network requests.
