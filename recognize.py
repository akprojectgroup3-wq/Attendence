import cv2
import os
from attendance import mark_attendance

# Load trained recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

# Load face detection file
cascade_path = os.path.join(
    os.path.dirname(cv2.__file__),
    "data",
    "haarcascade_frontalface_default.xml"
)

face_cascade = cv2.CascadeClassifier(cascade_path)

if face_cascade.empty():
    print("Face detection file was not found.")
    print("Cascade path:", cascade_path)
    exit()

# Student names
names = {
    1: "moin"
}

# Start camera
camera = cv2.VideoCapture(0)

print("Camera started.")
print("Look at the camera.")
print("Press Q to stop.")

while True:
    ret, frame = camera.read()

    if not ret:
        print("Camera could not be opened.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5
    )

    for (x, y, w, h) in faces:

        face = gray[y:y+h, x:x+w]

        label, confidence = recognizer.predict(face)

        print("Label:", label, "Confidence:", confidence)

        # LBPH: lower confidence = better match
        if label in names and confidence < 80:
            name = names[label]

            mark_attendance(name)

        else:
            name = "Unknown"

        # Draw rectangle
        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            2
        )

        # Display name
        cv2.putText(
            frame,
            name,
            (x, y-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "Face Recognition + Attendance",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()