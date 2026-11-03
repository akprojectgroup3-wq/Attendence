import csv
import os
import tkinter as tk
from tkinter import ttk

FILE_NAME = "attendance.csv"

root = tk.Tk()
root.title("AI Smart Classroom Attendance")
root.geometry("800x500")

title = tk.Label(
    root,
    text="AI Smart Classroom Attendance",
    font=("Arial", 20, "bold")
)
title.pack(pady=15)

columns = ("Name", "Date", "Time", "Status")

table = ttk.Treeview(root, columns=columns, show="headings")

for column in columns:
    table.heading(column, text=column)
    table.column(column, width=170)

table.pack(fill="both", expand=True, padx=20, pady=20)


def load_attendance():
    for item in table.get_children():
        table.delete(item)

    if not os.path.exists(FILE_NAME):
        return

    with open(FILE_NAME, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            table.insert(
                "",
                "end",
                values=(
                    row["Name"],
                    row["Date"],
                    row["Time"],
                    row["Status"]
                )
            )


refresh_button = tk.Button(
    root,
    text="Refresh Attendance",
    command=load_attendance,
    font=("Arial", 12)
)

refresh_button.pack(pady=10)

load_attendance()

root.mainloop()