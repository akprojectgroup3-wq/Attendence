"""Face detection service using OpenCV Haar Cascades.

Provides pre-processing, multi-scale face detection, and normalized
region-of-interest (ROI) extraction.
"""

import os
import cv2
import numpy as np
from typing import List, Tuple, Optional

# Locate Haar Cascade XML file
CASCADE_FILENAME = "haarcascade_frontalface_default.xml"
_cascade_path = None

if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
    candidate = os.path.join(cv2.data.haarcascades, CASCADE_FILENAME)
    if os.path.exists(candidate):
        _cascade_path = candidate

if not _cascade_path:
    # Fallback to local opencv path
    candidate = os.path.join(os.path.dirname(cv2.__file__), "data", CASCADE_FILENAME)
    if os.path.exists(candidate):
        _cascade_path = candidate

if not _cascade_path or not os.path.exists(_cascade_path):
    raise RuntimeError(f"OpenCV Haar Cascade classifier '{CASCADE_FILENAME}' could not be located.")

_face_cascade = cv2.CascadeClassifier(_cascade_path)


def detect_faces(
    image: np.ndarray,
    scale_factor: float = 1.15,
    min_neighbors: int = 5,
    min_size: Tuple[int, int] = (60, 60)
) -> Tuple[np.ndarray, List[Tuple[int, int, int, int]]]:
    """Detect faces in a BGR or grayscale image.

    Returns:
        (gray_image, list_of_bounding_boxes)
        where each bounding box is (x, y, width, height)
    """
    if image is None or image.size == 0:
        return np.array([]), []

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Apply CLAHE or histogram equalization for consistent illumination
    gray = cv2.equalizeHist(gray)

    faces = _face_cascade.detectMultiScale(
        gray,
        scaleFactor=scale_factor,
        minNeighbors=min_neighbors,
        minSize=min_size
    )

    boxes = [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
    return gray, boxes


def normalize_face_roi(
    face_img: np.ndarray,
    target_size: Tuple[int, int] = (200, 200)
) -> Optional[np.ndarray]:
    """Uniformly normalize, resize, and contrast-balance a face region for LBPH."""
    if face_img is None or face_img.size == 0:
        return None
    if len(face_img.shape) == 3:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = face_img.copy()

    resized = cv2.resize(gray, target_size, interpolation=cv2.INTER_AREA)
    equalized = cv2.equalizeHist(resized)
    return equalized


def extract_face_roi(
    gray: np.ndarray,
    box: Tuple[int, int, int, int],
    target_size: Tuple[int, int] = (200, 200)
) -> Optional[np.ndarray]:
    """Extract and normalize a cropped face region of interest."""
    x, y, w, h = box
    h_img, w_img = gray.shape[:2]

    # Clip coordinates to frame boundary
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(w_img, x + w)
    y2 = min(h_img, y + h)

    if (x2 - x1) < 20 or (y2 - y1) < 20:
        return None

    face_crop = gray[y1:y2, x1:x2]
    return normalize_face_roi(face_crop, target_size=target_size)
