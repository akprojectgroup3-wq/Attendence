"""Face recognition service using OpenCV LBPH.

Provides real-time multi-face detection, identity prediction, confidence thresholding,
visual annotation, in-memory debounce/cooldown, and automated attendance marking.
"""

import json
import time
import threading
import cv2
import numpy as np
from typing import Dict, Tuple, List, Optional

from config import MODEL_FILE, LABELS_FILE, load_settings
from services.face_detection import detect_faces, extract_face_roi, normalize_face_roi
from services.student_service import get_student_by_id
from services.attendance_service import mark_attendance


class FaceRecognitionService:
    """Thread-safe face recognition service."""

    def __init__(self):
        self._lock = threading.Lock()
        self.recognizer = None
        self.label_to_id: Dict[str, str] = {}
        self.id_to_label: Dict[str, int] = {}
        self.model_loaded = False
        self.last_trained_at = ""

        # In-memory cooldown tracking: {student_id: timestamp_of_last_scan}
        self.recent_scans: Dict[str, float] = {}

        # Camera streaming control
        self.camera = None
        self.is_camera_running = False
        self.camera_lock = threading.Lock()

        # Load existing model if present
        self.load_model()

    def load_model(self) -> bool:
        """Load or reload the trained LBPH model and label dictionary."""
        with self._lock:
            if not MODEL_FILE.exists() or not LABELS_FILE.exists():
                self.model_loaded = False
                self.recognizer = None
                return False

            try:
                recognizer = cv2.face.LBPHFaceRecognizer_create()
                recognizer.read(str(MODEL_FILE))

                with open(LABELS_FILE, "r", encoding="utf-8") as f:
                    meta = json.load(f)

                self.label_to_id = meta.get("label_to_id", {})
                self.id_to_label = meta.get("id_to_label", {})
                self.last_trained_at = meta.get("trained_at", "")
                self.recognizer = recognizer
                self.model_loaded = True
                return True
            except Exception as e:
                print(f"Error loading face recognition model: {e}")
                self.model_loaded = False
                self.recognizer = None
                return False

    def is_ready(self) -> bool:
        """Check if recognition model is ready."""
        return self.model_loaded and self.recognizer is not None

    def recognize_face(
        self,
        face_roi: np.ndarray,
        threshold: float = 75.0
    ) -> Tuple[str, float, bool]:
        """Predict identity for a normalized face ROI.

        LBPH returns a distance metric where 0 is an exact match and higher numbers
        indicate greater dissimilarity.
        - Distance < threshold: Match
        - Distance >= threshold: Unknown

        Returns:
            (student_id_or_Unknown, confidence_score, is_match)
        """
        if not self.is_ready() or face_roi is None:
            return "Unknown", 999.0, False

        try:
            norm_roi = normalize_face_roi(face_roi)
            if norm_roi is None:
                return "Unknown", 999.0, False
            label, distance = self.recognizer.predict(norm_roi)
            str_label = str(label)

            # Check if label exists and distance is strictly below threshold
            if str_label in self.label_to_id and distance < threshold:
                student_id = self.label_to_id[str_label]
                return student_id, float(distance), True
            else:
                return "Unknown", float(distance), False
        except Exception as e:
            print(f"Error predicting face: {e}")
            return "Unknown", 999.0, False

    def process_frame(
        self,
        frame: np.ndarray,
        auto_mark: bool = True,
        session_id: Optional[str] = None
    ) -> Tuple[np.ndarray, List[Dict]]:
        """Process a single camera frame: detect faces, predict identities,

        annotate with visual bounding boxes, and optionally mark attendance.

        Returns:
            (annotated_frame, list_of_event_dicts)
        """
        if frame is None or frame.size == 0:
            return frame, []

        settings = load_settings()
        threshold = float(settings.get("recognition_threshold", 75.0))
        cooldown_sec = float(settings.get("duplicate_cooldown_seconds", 300))
        active_session = session_id or settings.get("attendance_session", "SESSION_1")

        annotated = frame.copy()
        gray, boxes = detect_faces(frame, min_size=(50, 50))
        events = []
        now = time.time()

        for box in boxes:
            x, y, w, h = box
            face_roi = extract_face_roi(gray, box, target_size=(200, 200))
            if face_roi is None:
                continue

            student_id, distance, is_match = self.recognize_face(face_roi, threshold=threshold)

            if is_match and student_id != "Unknown":
                student = get_student_by_id(student_id)
                display_name = student.get("Name", student_id) if student else student_id
                # Confidence representation (higher percentage for lower LBPH distance)
                confidence_pct = max(0, min(100, int((100 - distance))))

                # Green box for recognized student
                box_color = (34, 197, 94)  # Tailwind emerald-500
                label_text = f"{display_name} ({student_id}) [{confidence_pct}%]"

                event_info = {
                    "student_id": student_id,
                    "name": display_name,
                    "confidence": confidence_pct,
                    "status": "recognized",
                    "distance": round(distance, 1),
                    "attendance_marked": False,
                    "message": ""
                }

                # Handle automated attendance recording with cooldown check
                if auto_mark:
                    last_scan = self.recent_scans.get(student_id, 0)
                    if (now - last_scan) > cooldown_sec:
                        # Attempt to mark attendance
                        marked, msg, rec = mark_attendance(student_id, active_session)
                        self.recent_scans[student_id] = now
                        event_info["attendance_marked"] = marked
                        event_info["message"] = msg
                        if rec:
                            event_info["attendance_status"] = rec.get("Status", "")
                    else:
                        remaining = int(cooldown_sec - (now - last_scan))
                        event_info["message"] = f"Cooldown active ({remaining}s remaining)."

                events.append(event_info)

            else:
                # Red box for unrecognized or unknown face
                box_color = (239, 68, 68)  # Tailwind red-500
                label_text = "Unknown Face"
                events.append({
                    "student_id": "Unknown",
                    "name": "Unknown",
                    "confidence": 0,
                    "status": "unknown",
                    "distance": round(distance, 1),
                    "attendance_marked": False,
                    "message": "Face not recognized. Attendance will not be recorded."
                })

            # Draw stylish rounded corner bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), box_color, 2)

            # Draw background tag banner for text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            text_size = cv2.getTextSize(label_text, font, font_scale, thickness)[0]

            tag_y = max(y - 10, text_size[1] + 10)
            cv2.rectangle(
                annotated,
                (x, tag_y - text_size[1] - 6),
                (x + text_size[0] + 10, tag_y + 4),
                box_color,
                -1
            )
            cv2.putText(
                annotated,
                label_text,
                (x + 5, tag_y - 2),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )

        return annotated, events


# Global singleton instance
recognition_service = FaceRecognitionService()
