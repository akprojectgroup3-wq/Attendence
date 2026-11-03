import cv2
import os
import numpy as np

recognizer = cv2.face.LBPHFaceRecognizer_create()

data_path = "dataset"

faces = []
labels = []

label_id = 0

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

for person in os.listdir(data_path):

    person_path = os.path.join(data_path, person)

    if not os.path.isdir(person_path):
        continue

    for image_name in os.listdir(person_path):

        image_path = os.path.join(person_path, image_name)

        image = cv2.imread(image_path)

        if image is None:
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        detected_faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5
        )

        for (x, y, w, h) in detected_faces:

            face = gray[y:y+h, x:x+w]

            faces.append(face)
            labels.append(label_id)

    label_id += 1

if len(faces) == 0:
    print("No faces found in dataset!")
    exit()

recognizer.train(faces, np.array(labels))
recognizer.save("trainer.yml")

print("Training completed!")
print("Faces used:", len(faces))
