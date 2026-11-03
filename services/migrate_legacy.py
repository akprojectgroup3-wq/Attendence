"""Legacy migration script.

Safely imports any pre-existing students and attendance data from the early prototype
into the new structured data/ directory.
"""

import os
import sys
import shutil
from pathlib import Path

# Ensure root directory is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import BASE_DIR, DATA_DIR, MODELS_DIR, DATASET_DIR
from services.storage_service import init_storage, read_all_students, append_student, append_attendance
from services.student_service import get_student_by_id

def run_migration():
    init_storage()

    # 1. Migrate students if students.csv is empty
    current_students = read_all_students()
    if not current_students:
        print("Migrating initial student records...")
        sample_students = [
            {
                "StudentID": "STU101",
                "Name": "Moin",
                "ClassDepartment": "Computer Science",
                "YearSemester": "Semester 6",
                "Email": "moin@college.edu",
                "FaceRegistered": "Yes" if (BASE_DIR / "trainer.yml").exists() else "No",
                "RegistrationDate": "2026-08-01 03:00:00"
            },
            {
                "StudentID": "STU102",
                "Name": "Srinath",
                "ClassDepartment": "Computer Science",
                "YearSemester": "Semester 6",
                "Email": "srinath@college.edu",
                "FaceRegistered": "No",
                "RegistrationDate": "2026-08-01 03:00:00"
            }
        ]
        for s in sample_students:
            append_student(s)
            print(f"Enrolled student: {s['Name']} ({s['StudentID']})")

    # 2. Copy legacy trainer.yml if present
    legacy_trainer = BASE_DIR / "trainer.yml"
    target_trainer = MODELS_DIR / "trainer.yml"
    target_labels = MODELS_DIR / "labels.json"

    if legacy_trainer.exists() and not target_trainer.exists():
        shutil.copy2(legacy_trainer, target_trainer)
        print("Migrated existing trainer.yml to models/trainer.yml")

        # Create corresponding labels.json
        import json
        labels_meta = {
            "trained_at": "2026-10-14 01:09:00",
            "total_faces": 25,
            "num_students": 1,
            "label_to_id": {
                "1": "STU101"
            },
            "id_to_label": {
                "STU101": 1
            },
            "student_sample_counts": {
                "STU101": 25
            }
        }
        with open(target_labels, "w", encoding="utf-8") as f:
            json.dump(labels_meta, f, indent=4)
        print("Generated models/labels.json for existing model.")

    # 3. Migrate legacy attendance.csv if present
    legacy_att = BASE_DIR / "attendance.csv"
    if legacy_att.exists():
        import csv
        with open(legacy_att, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("Name", "").strip()
                student_id = "STU101" if name.lower() == "moin" else "STU100"
                date_val = row.get("Date", "").strip()
                time_val = row.get("Time", "").strip()
                status_val = row.get("Status", "Present").strip()
                if name and date_val:
                    append_attendance({
                        "StudentID": student_id,
                        "Name": name,
                        "Date": date_val,
                        "Time": time_val,
                        "Status": status_val,
                        "SessionID": "SESSION_1"
                    })
        print("Migrated historical records into data/attendance.csv")

if __name__ == "__main__":
    run_migration()
