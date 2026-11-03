import cv2
import os

name = input("Enter student name: ")

folder = "dataset/" + name
os.makedirs(folder, exist_ok=True)

camera = cv2.VideoCapture(0)

count = 0

while True:
    success, frame = camera.read()

    if not success:
        print("Camera could not be opened")
        break

    cv2.imshow("Register Face - Press Q to Stop", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        filename = f"{folder}/image_{count}.jpg"
        cv2.imwrite(filename, frame)
        print("Saved:", filename)
        count += 1

    if key == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()

print("Registration completed!")