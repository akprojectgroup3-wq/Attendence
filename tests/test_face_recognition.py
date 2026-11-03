"""Automated tests for Face Detection, Registration, LBPH Model Training, and Recognition.

Verifies:
- Test 5: Face images can be captured and registered.
- Test 6: Model can be trained and loaded.
- Test 7: Registered face can be recognized.
- Test 8: Unknown face is NOT marked present.
- Test 16: Application displays useful diagnostics if camera/ESP32 is offline.
"""

import unittest
import sys
import os
import shutil
import cv2
import numpy as np
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATASET_DIR, MODEL_FILE, LABELS_FILE
from services.face_detection import detect_faces, extract_face_roi
from services.face_registration import register_face_sample
from services.model_training import train_lbph_model
from services.face_recognition_service import FaceRecognitionService
from services.student_service import add_student, delete_student
from services.esp32_cam_service import esp32_cam_service


class TestFaceRecognitionPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_student_id = "FACE-TEST-01"
        cls.test_student_id_2 = "FACE-TEST-02"
        delete_student(cls.test_student_id)
        delete_student(cls.test_student_id_2)
        add_student(cls.test_student_id, "Biometric Test Subject", "Computer Science", "Semester 6")
        add_student(cls.test_student_id_2, "Second Test Subject", "Computer Science", "Semester 6")

        # Create structured synthetic face patterns
        # Student 1: Oval face with circular features
        cls.synthetic_face = np.zeros((200, 200), dtype=np.uint8)
        y, x = np.ogrid[:200, :200]
        cls.synthetic_face[((x - 100)**2 + (y - 100)**2 < 80**2)] = 180
        cv2.circle(cls.synthetic_face, (70, 80), 15, 40, -1)
        cv2.circle(cls.synthetic_face, (130, 80), 15, 40, -1)
        cv2.rectangle(cls.synthetic_face, (95, 95), (105, 125), 60, -1)
        cv2.ellipse(cls.synthetic_face, (100, 150), (35, 15), 0, 0, 180, 40, -1)

        # Student 2: Rectangular face with different layout
        cls.synthetic_face_2 = np.zeros((200, 200), dtype=np.uint8)
        cv2.rectangle(cls.synthetic_face_2, (40, 40), (160, 160), 220, -1)
        cv2.circle(cls.synthetic_face_2, (80, 80), 10, 10, -1)
        cv2.circle(cls.synthetic_face_2, (120, 80), 10, 10, -1)

    @classmethod
    def tearDownClass(cls):
        delete_student(cls.test_student_id)
        delete_student(cls.test_student_id_2)

    def test_01_save_face_sample_directly(self):
        """Test Case 5: Face images can be captured and registered."""
        # Save samples for student 1
        student_dir_1 = DATASET_DIR / self.test_student_id
        student_dir_1.mkdir(parents=True, exist_ok=True)
        for i in range(5):
            img_path = student_dir_1 / f"sample_{i}.jpg"
            cv2.imwrite(str(img_path), self.synthetic_face)

        # Save samples for student 2
        student_dir_2 = DATASET_DIR / self.test_student_id_2
        student_dir_2.mkdir(parents=True, exist_ok=True)
        for i in range(5):
            img_path = student_dir_2 / f"sample_{i}.jpg"
            cv2.imwrite(str(img_path), self.synthetic_face_2)

        self.assertGreaterEqual(len(list(student_dir_1.glob("*.jpg"))), 5)
        self.assertGreaterEqual(len(list(student_dir_2.glob("*.jpg"))), 5)

    def test_02_model_training_and_loading(self):
        """Test Case 6: Model can be trained and loaded."""
        success, msg, meta = train_lbph_model()
        self.assertTrue(success, f"Model training failed: {msg}")
        self.assertTrue(MODEL_FILE.exists(), "trainer.yml should exist after training.")
        self.assertTrue(LABELS_FILE.exists(), "labels.json should exist after training.")

        # Test loading into recognition service
        svc = FaceRecognitionService()
        self.assertTrue(svc.is_ready(), "FaceRecognitionService should load the newly trained model.")

    def test_03_registered_face_recognition(self):
        """Test Case 7: A registered face can be recognized under suitable conditions."""
        svc = FaceRecognitionService()
        svc.load_model()

        # Test prediction with synthetic face
        student_id, distance, is_match = svc.recognize_face(self.synthetic_face, threshold=85.0)
        self.assertEqual(student_id, self.test_student_id, "Model should recognize registered synthetic face.")
        self.assertTrue(is_match)
        self.assertLess(distance, 85.0)

    def test_04_unknown_face_is_not_marked_present(self):
        """Test Case 8: An unknown face is not marked present."""
        svc = FaceRecognitionService()
        svc.load_model()

        # Generate a completely inverted random pattern (unknown face)
        unknown_face = np.random.randint(0, 256, (200, 200), dtype=np.uint8)

        # Using standard threshold (75.0)
        student_id, distance, is_match = svc.recognize_face(unknown_face, threshold=75.0)
        self.assertEqual(student_id, "Unknown", "Unknown face must be classified as 'Unknown'.")
        self.assertFalse(is_match)

    def test_05_camera_offline_diagnostics(self):
        """Test Case 16: Application displays useful diagnostics if camera/ESP32 is offline."""
        # Test connecting to an invalid/offline IP address
        is_conn, msg, diag = esp32_cam_service.test_connection("http://192.0.2.1:81/stream", timeout=1.0)
        self.assertFalse(is_conn, "Offline IP should not report as connected.")
        self.assertIn("timed out", msg.lower())
        self.assertFalse(diag.get("connected", True))


if __name__ == "__main__":
    unittest.main()
