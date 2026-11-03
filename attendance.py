import csv
import os
from datetime import datetime

FILE_NAME = "attendance.csv"


def mark_attendance(name):
    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if now.hour < 9 or (now.hour == 9 and now.minute < 30):
        status = "Present"
    else:
        status = "Late"

    # Check whether this student is already marked today
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                if row["Name"] == name and row["Date"] == date:
                    print(f"{name} is already marked today.")
                    return

    file_exists = os.path.exists(FILE_NAME)

    with open(FILE_NAME, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Name", "Date", "Time", "Status"])

        writer.writerow([name, date, time, status])

    print(f"Attendance marked: {name} - {status}")