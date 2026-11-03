"""Face recognition model training service using OpenCV LBPH.

Builds and persists the LBPH recognizer model file and student ID mappings.
"""

import json
import os
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Tuple

from config import DATASET_DIR, MODEL_FILE, LABELS_FILE, get_current_time
from services.face_detection import detect_faces, extract_face_roi, normalize_face_roi
from services.student_service import update_face_registration_status


def train_lbph_model() -> Tuple[bool, str, Dict]:
    """Train LBPH Face Recognizer on all captured face images in the dataset.

    Returns:
        (success, message, statistics_dict)
    """
    if not DATASET_DIR.exists():
        return False, "Face dataset directory does not exist.", {}

    student_dirs = [d for d in DATASET_DIR.iterdir() if d.is_dir()]
    if not student_dirs:
        return False, "No student face datasets found. Please register at least one student face first.", {}

    faces = []
    labels = []
    label_to_id: Dict[str, str] = {}
    id_to_label: Dict[str, int] = {}
    student_sample_counts: Dict[str, int] = {}

    current_label = 0
    valid_exts = {".jpg", ".jpeg", ".png"}

    for s_dir in student_dirs:
        student_id = s_dir.name.strip().upper()
        image_files = [f for f in s_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]

        if not image_files:
            continue

        label_to_id[str(current_label)] = student_id
        id_to_label[student_id] = current_label
        student_samples = 0

        for img_file in image_files:
            try:
                img = cv2.imread(str(img_file))
                if img is None:
                    continue

                gray, boxes = detect_faces(img)
                if boxes:
                    # Use the most prominent face in the training frame
                    largest_box = max(boxes, key=lambda b: b[2] * b[3])
                    face_roi = extract_face_roi(gray, largest_box)
                    if face_roi is not None:
                        faces.append(face_roi)
                        labels.append(current_label)
                        student_samples += 1
                else:
                    # If already cropped during registration, use directly
                    face_roi = normalize_face_roi(img)
                    if face_roi is not None:
                        faces.append(face_roi)
                        labels.append(current_label)
                        student_samples += 1
                    student_samples += 1
            except Exception as e:
                print(f"Skipping bad image {img_file}: {e}")

        if student_samples > 0:
            student_sample_counts[student_id] = student_samples
            update_face_registration_status(student_id, True)
            current_label += 1

    if not faces:
        return False, "No valid face samples detected in the dataset. Please capture clearer face photos.", {}

    try:
        # Create and train LBPH Face Recognizer
        recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1,
            neighbors=8,
            grid_x=8,
            grid_y=8
        )
        recognizer.train(faces, np.array(labels, dtype=np.int32))

        # Save model file
        MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
        recognizer.save(str(MODEL_FILE))

        # Save label mappings and training metadata
        meta = {
            "trained_at": get_current_time().strftime("%Y-%m-%d %H:%M:%S"),
            "total_faces": len(faces),
            "num_students": len(label_to_id),
            "label_to_id": label_to_id,
            "id_to_label": id_to_label,
            "student_sample_counts": student_sample_counts
        }

        with open(LABELS_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4)

        return True, f"Model successfully trained on {len(faces)} face samples across {len(label_to_id)} students.", meta

    except Exception as e:
        return False, f"Failed to train LBPH model: {str(e)}", {}
