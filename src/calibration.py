"""
Interactive Calibration Tool for AI Gesture Mouse.

Allows users to test camera feed, measure personal pinch distance threshold,
calibrate active interaction boundary, and persist optimized settings.
"""

import sys
import time
import cv2
import numpy as np

from src.config import AppConfig
from src.hand_detector import HandDetector, HandLandmarks


def run_calibration(config_path: str = "config.json") -> None:
    """Runs interactive calibration routine."""
    config = AppConfig.load(config_path)

    print("=" * 60)
    print("      AI GESTURE MOUSE - INTERACTIVE CALIBRATION TOOL      ")
    print("=" * 60)
    print("1. Point index finger to verify cursor tracking")
    print("2. Pinch Thumb and Index finger to sample click distance")
    print("3. Press 'c' to capture current pinch distance as threshold")
    print("4. Press '+' / '-' to adjust smoothing factor")
    print("5. Press 's' to SAVE configuration and exit")
    print("6. Press 'q' or ESC to CANCEL without saving")
    print("=" * 60)

    cap = cv2.VideoCapture(config.camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    if not cap.isOpened():
        print(f"[Error] Could not open camera {config.camera_index}.")
        return

    detector = HandDetector(
        detection_con=config.detection_confidence,
        track_con=config.tracking_confidence
    )

    current_pinch_dist = 0.0
    recorded_pinch_samples = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Error] Failed to read frame from camera.")
                break

            if config.flip_horizontal:
                frame = cv2.flip(frame, 1)

            h, w, _ = frame.shape
            frame = detector.find_hands(frame, draw=True)
            lm_list = detector.find_positions(frame)

            # Draw active screen bounds
            x_min = config.frame_margin
            x_max = w - config.frame_margin
            y_min = config.frame_margin
            y_max = h - config.frame_margin
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 180, 0), 2)
            cv2.putText(
                frame, "Active Tracking Area", (x_min + 5, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 180, 0), 1
            )

            if len(lm_list) >= 21:
                current_pinch_dist, _, _ = detector.find_distance(
                    HandLandmarks.THUMB_TIP,
                    HandLandmarks.INDEX_FINGER_TIP,
                    frame,
                    draw=True
                )

                # Show status
                is_click = current_pinch_dist < config.pinch_threshold
                status_color = (0, 255, 0) if is_click else (0, 165, 255)
                status_text = "PINCH DETECTED" if is_click else "TRACKING"

                cv2.putText(
                    frame, f"Pinch Distance: {current_pinch_dist:.1f}px (Threshold: {config.pinch_threshold:.1f}px)",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2
                )
                cv2.putText(
                    frame, f"State: {status_text}",
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2
                )
            else:
                cv2.putText(
                    frame, "No Hand Detected - Show hand to camera",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
                )

            # Controls HUD at bottom
            cv2.putText(
                frame, f"Smoothing: {config.smoothing_factor:.1f} (+/-) | 'c': Sample Pinch | 's': Save | 'q': Exit",
                (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1
            )

            cv2.imshow("AI Gesture Mouse - Calibration", frame)
            key = cv2.waitKey(1) & 0xFF

            if key in [ord('q'), 27]:
                print("[Info] Calibration canceled.")
                break
            elif key == ord('c'):
                if current_pinch_dist > 0:
                    recorded_pinch_samples.append(current_pinch_dist)
                    avg = sum(recorded_pinch_samples) / len(recorded_pinch_samples)
                    # Set threshold slightly above avg pinch distance for reliable detection
                    config.pinch_threshold = round(avg + 6.0, 1)
                    print(f"[Calibrate] Sampled {current_pinch_dist:.1f}px. Updated threshold: {config.pinch_threshold}px")
            elif key == ord('+') or key == ord('='):
                config.smoothing_factor = min(20.0, config.smoothing_factor + 0.5)
                print(f"[Calibrate] Smoothing factor increased to {config.smoothing_factor}")
            elif key == ord('-') or key == ord('_'):
                config.smoothing_factor = max(1.0, config.smoothing_factor - 0.5)
                print(f"[Calibrate] Smoothing factor decreased to {config.smoothing_factor}")
            elif key == ord('s'):
                config.save(config_path)
                print("[Info] Saved updated configuration.")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    run_calibration(path)


if __name__ == "__main__":
    main()
