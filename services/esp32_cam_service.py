"""ESP32-CAM IoT Hardware Integration Module.

Provides connectivity, stream parsing, single-frame capturing, and status diagnostics
for ESP32-CAM Wi-Fi video streaming modules.

Architecture:
    [ESP32-CAM Module]
          │ (Wi-Fi MJPEG / JPEG Stream HTTP)
          ▼
    [Flask Backend: esp32_cam_service.py]
          │ (Decoded OpenCV numpy frames)
          ▼
    [face_recognition_service.py] -> [attendance_service.py] -> [attendance.csv]
"""

import time
import cv2
import requests
import numpy as np
from typing import Tuple, Optional, Dict

from config import load_settings


class ESP32CamService:
    """Service to connect and stream frames from an ESP32-CAM Wi-Fi module."""

    def __init__(self):
        self.last_check_time = 0
        self.last_status = False
        self.last_error = ""

    def get_cam_url(self) -> str:
        """Fetch configured camera URL or IP."""
        settings = load_settings()
        source = str(settings.get("camera_source", "0")).strip()
        return source

    def is_esp32_configured(self) -> bool:
        """Check whether the active camera source is an IP/HTTP stream rather than webcam 0."""
        source = self.get_cam_url()
        return source.startswith("http://") or source.startswith("https://") or source.startswith("rtsp://")

    def test_connection(self, url: Optional[str] = None, timeout: float = 3.0) -> Tuple[bool, str, Dict]:
        """Test whether the ESP32-CAM HTTP endpoint is reachable and returning valid images.

        Returns:
            (is_connected, message, diagnostics_dict)
        """
        target_url = url or self.get_cam_url()

        if not target_url or target_url == "0":
            return False, "Laptop webcam is currently selected (camera index 0). No ESP32-CAM URL configured.", {
                "source": "webcam",
                "connected": False
            }

        start_time = time.time()
        try:
            # Handle capture URL or stream URL
            # If standard stream URL is given (e.g. :81/stream), test with stream=True or try capture endpoint
            test_endpoint = target_url
            if test_endpoint.endswith("/stream"):
                # Many ESP32 sketches offer /capture for a single JPEG snapshot
                snapshot_candidate = test_endpoint.replace("/stream", "/capture")
            else:
                snapshot_candidate = test_endpoint

            resp = requests.get(snapshot_candidate, timeout=timeout, stream=True)
            latency_ms = int((time.time() - start_time) * 1000)

            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "")
                self.last_status = True
                self.last_error = ""
                return True, f"ESP32-CAM connected successfully at {target_url} (Latency: {latency_ms}ms).", {
                    "source": target_url,
                    "connected": True,
                    "latency_ms": latency_ms,
                    "content_type": content_type
                }
            else:
                msg = f"ESP32-CAM returned HTTP error code {resp.status_code}."
                self.last_status = False
                self.last_error = msg
                return False, msg, {"source": target_url, "connected": False, "status_code": resp.status_code}

        except requests.exceptions.ConnectTimeout:
            msg = f"Connection timed out trying to reach ESP32-CAM at '{target_url}'. Verify the ESP32-CAM is powered on and connected to your Wi-Fi network."
            self.last_status = False
            self.last_error = msg
            return False, msg, {"source": target_url, "connected": False, "error": "timeout"}

        except requests.exceptions.ConnectionError:
            msg = f"Could not connect to ESP32-CAM at '{target_url}'. Check the IP address and make sure your computer and ESP32 are on the same Wi-Fi subnet."
            self.last_status = False
            self.last_error = msg
            return False, msg, {"source": target_url, "connected": False, "error": "connection_refused"}

        except Exception as e:
            msg = f"ESP32-CAM connection error: {str(e)}"
            self.last_status = False
            self.last_error = msg
            return False, msg, {"source": target_url, "connected": False, "error": str(e)}

    def capture_frame(self, url: Optional[str] = None, timeout: float = 2.0) -> Optional[np.ndarray]:
        """Fetch a single JPEG frame from ESP32-CAM and decode into an OpenCV BGR array."""
        target_url = url or self.get_cam_url()

        if not target_url or target_url == "0":
            return None

        # Try /capture endpoint if /stream is configured
        candidate_url = target_url
        if candidate_url.endswith("/stream"):
            candidate_url = candidate_url.replace("/stream", "/capture")

        try:
            resp = requests.get(candidate_url, timeout=timeout)
            if resp.status_code == 200:
                img_arr = np.frombuffer(resp.content, dtype=np.uint8)
                frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                return frame
        except Exception:
            pass

        return None


# Global service instance
esp32_cam_service = ESP32CamService()
