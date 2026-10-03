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
