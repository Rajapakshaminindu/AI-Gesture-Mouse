python
"""
Interactive Calibration Tool for AI Gesture Mouse.

Allows users to test camera feed, measure personal pinch distance threshold,
calibrate active interaction boundary, and persist optimized settings with
a live graphical dashboard.
"""

import sys
import time
import cv2
import numpy as np

from src.config import AppConfig
from src.hand_detector import HandDetector


def draw_bar(frame: np.ndarray, x: int, y: int, w: int, h: int, value: float, max_val: float, label: str, color: tuple):
    """Draws a sleek labeled horizontal bar graph with background track."""
    cv2.rectangle(frame, (x, y), (x + w, y + h), (40, 40, 45), -1)
    fill_w = int(min(max(value / max_val, 0.0), 1.0) * w)
    cv2.rectangle(frame, (x, y), (x + fill_w, y + h), color, -1)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (90, 90, 100), 1)
    cv2.putText(frame, f"{label}: {value:.1f}", (x, y - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)


def run_calibration(config_path: str = "config.json") -> None:
    """Runs interactive calibration routine with on-screen visual analytics."""
    config = AppConfig.load(config_path)

    cap = cv2.VideoCapture(config.camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    if not cap.isOpened():
        print(f"[Error] Could not open camera #{config.camera_index}.")
        return

    detector = HandDetector(
        detection_con=config.detection_confidence,
        track_con=config.tracking_confidence
    )

    current_pinch = 0.0
    status_msg = "Ready. Point index finger or test pinch."
    status_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if config.flip_horizontal:
                frame = cv2.flip(frame, 1)

            h, w, _ = frame.shape
            frame = detector.find_hands(frame, draw=True)
            landmarks = detector.get_landmarks(frame)

            # Active margin box
            m = config.frame_margin
            cv2.rectangle(frame, (m, m), (w - m, h - m), (0, 180, 255), 2)

            if landmarks and len(landmarks) >= 21:
                # Calculate Thumb(4) to Index(8) distance
                p1 = np.array(landmarks[4][:2])
                p2 = np.array(landmarks[8][:2])
                current_pinch = float(np.linalg.norm(p1 - p2))
                cv2.line(frame, tuple(p1), tuple(p2), (0, 255, 255), 2)


# Top Control Panel (Semi-transparent overlay)
            overlay = frame.copy()
            cv2.rectangle(overlay, (15, 15), (w - 15, 125), (20, 20, 25), -1)
            cv2.rectangle(overlay, (15, 15), (w - 15, 125), (60, 60, 70), 1)
            cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

            # Keybindings Header
            cv2.putText(frame, "CALIBRATION CONTROLS:", (25, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "[C] Capture Pinch  |  [+/-] Smoothing  |  [S] Save  |  [Q] Quit",
                        (25, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 220, 255), 1, cv2.LINE_AA)

            # Live Parameter Bars
            draw_bar(frame, 25, 95, 160, 14, current_pinch, 100.0, "Live Pinch Dist", (0, 220, 255))
            draw_bar(frame, 215, 95, 160, 14, config.pinch_threshold, 100.0, "Saved Threshold", (0, 255, 120))
            draw_bar(frame, 405, 95, 140, 14, config.smoothing_factor, 15.0, "Smoothing Factor", (255, 160, 0))

            # Status Toast Notification
            if time.time() - status_time < 3.0:
                cv2.putText(frame, status_msg, (25, h - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 180), 1, cv2.LINE_AA)

            cv2.imshow("AI Gesture Mouse - Calibration", frame)
            key = cv2.waitKey(1) & 0xFF

            if key in (ord('q'), 27):
                break
            elif key == ord('c'):
                config.pinch_threshold = round(current_pinch, 1)
                status_msg = f"Captured pinch threshold: {config.pinch_threshold}px"
                status_time = time.time()
            elif key in (ord('+'), ord('=')):
                config.smoothing_factor = round(min(config.smoothing_factor + 0.5, 15.0), 1)
                status_msg = f"Smoothing increased to: {config.smoothing_factor}"
                status_time = time.time()
            elif key in (ord('-'), ord('_')):
                config.smoothing_factor = round(max(config.smoothing_factor - 0.5, 1.0), 1)
                status_msg = f"Smoothing decreased to: {config.smoothing_factor}"
                status_time = time.time()
            elif key == ord('s'):
                config.save(config_path)
                status_msg = f"Config successfully saved to {config_path}!"
                status_time = time.time()

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run_calibration()

