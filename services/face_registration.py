"""Face registration service for capturing, validating, and persisting training images.

Provides image decoding, face presence validation, and dataset folder management.
"""

import base64
import os
import time
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Optional

from config import DATASET_DIR
from services.face_detection import detect_faces, extract_face_roi
from services.student_service import get_student_by_id, count_student_images
from services.model_training import train_lbph_model


def decode_base64_image(image_data_uri: str) -> Optional[np.ndarray]:
    """Decode a base64 Data URL (from HTML5 canvas/webcam) to an OpenCV BGR numpy array."""
    if not image_data_uri:
        return None
    try:
        if "," in image_data_uri:
            image_data_uri = image_data_uri.split(",", 1)[1]
        image_bytes = base64.b64decode(image_data_uri)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None


def register_face_sample(
    student_id: str,
    image_bgr: np.ndarray,
    target_count: int = 25
) -> Tuple[bool, str, Dict]:
    """Validate and save a single face capture for the given student.

    Validates that a single clear face is present, crops and normalizes the ROI,
    and writes to the student's dataset directory.

    Returns:
        (success, message, metadata_dict)
    """
    student_id = student_id.strip().upper()
    student = get_student_by_id(student_id)
    if not student:
        return False, f"Cannot register face: Student '{student_id}' does not exist.", {}

    if image_bgr is None or image_bgr.size == 0:
        return False, "Invalid image data provided.", {}

    # Detect faces
    gray, boxes = detect_faces(image_bgr, min_size=(50, 50))
    if len(boxes) == 0:
        return False, "No face detected in the frame. Please look directly at the camera.", {}
    if len(boxes) > 1:
        return False, "Multiple faces detected. Please ensure only one person is in the frame.", {}

    box = boxes[0]
    face_roi = extract_face_roi(gray, box, target_size=(200, 200))
    if face_roi is None:
        return False, "Face is too small or near the edge. Please move closer to the camera.", {}

    # Target directory for this student
    student_dir = DATASET_DIR / student_id
    student_dir.mkdir(parents=True, exist_ok=True)

    # Save face image with timestamp
    timestamp = int(time.time() * 1000)
    current_count = count_student_images(student_id)
    filename = f"face_{timestamp}_{current_count + 1}.jpg"
    file_path = student_dir / filename

    saved = cv2.imwrite(str(file_path), face_roi)
    if not saved:
        return False, "Failed to save face image to disk.", {}

    new_count = count_student_images(student_id)
    is_complete = new_count >= target_count

    meta = {
        "student_id": student_id,
        "name": student.get("Name", ""),
        "current_count": new_count,
        "target_count": target_count,
        "is_complete": is_complete
    }

    return True, f"Face sample captured successfully ({new_count}/{target_count}).", meta


def finish_student_registration(student_id: str) -> Tuple[bool, str, Dict]:
    """Finalize face registration for student by training the LBPH model."""
    student_id = student_id.strip().upper()
    count = count_student_images(student_id)
    if count == 0:
        return False, f"No images found for student '{student_id}'. Capture face images first.", {}

    # Train model
    success, msg, train_meta = train_lbph_model()
    if success:
        return True, f"Registration complete! {count} face samples trained for student '{student_id}'.", train_meta
    return False, f"Images saved, but model training failed: {msg}", train_meta
