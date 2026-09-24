"""
AI Gesture Mouse - Main Execution Pipeline.

Combines camera capture, MediaPipe hand landmark tracking, gesture recognition,
smooth cursor interpolation, and interactive HUD overlay.
"""

import sys
import time
import argparse
import cv2
import numpy as np

from src.config import AppConfig
from src.hand_detector import HandDetector, HandLandmarks
from src.mouse_controller import MouseController
from src.gesture_recognizer import GestureRecognizer, GestureType


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Gesture Mouse - Touchless Computer Control System"
    )
    parser.add_argument(
        "--config", type=str, default="config.json",
        help="Path to configuration JSON file"
    )
    parser.add_argument(
        "--camera", type=int, default=None,
        help="Camera device index (overrides config)"
    )
    parser.add_argument(
        "--no-hud", action="store_true",
        help="Disable HUD graphics overlay"
    )
    return parser.parse_args()


def draw_hud(
    frame: np.ndarray,
    active_gesture: GestureType,
    fps: float,
    config: AppConfig,
    cursor_pos: tuple,
    meta: dict
) -> None:
    """Renders real-time HUD graphics, active interaction boundary, and status badge."""
    h, w, _ = frame.shape

    # Active tracking boundary
    x_min, y_min = config.frame_margin, config.frame_margin
    x_max, y_max = w - config.frame_margin, h - config.frame_margin
    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 180, 0), 2)

    # Top banner bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 55), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Status Badge
    gesture_colors = {
        GestureType.MOVE: (0, 255, 128),
        GestureType.LEFT_CLICK: (0, 255, 255),
        GestureType.RIGHT_CLICK: (255, 120, 0),
        GestureType.DOUBLE_CLICK: (255, 0, 255),
        GestureType.DRAG: (0, 100, 255),
        GestureType.SCROLL: (255, 255, 0),
        GestureType.IDLE: (160, 160, 160)
    }
    badge_color = gesture_colors.get(active_gesture, (160, 160, 160))

    cv2.circle(frame, (25, 27), 9, badge_color, -1)
    cv2.putText(
        frame, f"MODE: {active_gesture.value}", (45, 34),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
    )

    # FPS counter
    cv2.putText(
        frame, f"FPS: {int(fps)}", (w - 110, 34),
        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2
    )

    # Visual click pulse
    if active_gesture in (GestureType.LEFT_CLICK, GestureType.DOUBLE_CLICK, GestureType.RIGHT_CLICK):
        cx, cy = cursor_pos
        if cx > 0 and cy > 0:
            cv2.circle(frame, (cx, cy), 22, badge_color, 3)
            cv2.circle(frame, (cx, cy), 10, badge_color, -1)

    # Bottom helper bar
    cv2.putText(
        frame, "AI Gesture Mouse | Press 'q' or ESC to exit", (15, h - 15),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1
    )


def main() -> None:
    args = parse_arguments()
    config = AppConfig.load(args.config)
    if args.camera is not None:
        config.camera_index = args.camera

    print("=" * 60)
    print("                STARTING AI GESTURE MOUSE                ")
    print("=" * 60)
    print(f" Camera Index     : {config.camera_index}")
    print(f" Frame Resolution : {config.frame_width}x{config.frame_height}")
    print(f" Smoothing Factor : {config.smoothing_factor}")
    print(f" Pinch Threshold  : {config.pinch_threshold} px")
    print(" Controls         : Point (Move) | Pinch (Left Click)")
    print("                    3-Fingers Up (Right Click) | 2-Fingers (Scroll)")
    print("                    Pinch & Hold (Drag) | Press 'q' to Quit")
    print("=" * 60)

    cap = cv2.VideoCapture(config.camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    if not cap.isOpened():
        print(f"[Error] Failed to initialize camera index {config.camera_index}.")
        sys.exit(1)

    detector = HandDetector(
        detection_con=config.detection_confidence,
        track_con=config.tracking_confidence
    )
    mouse = MouseController(
        frame_size=(config.frame_width, config.frame_height),
        frame_margin=config.frame_margin,
        smoothing_factor=config.smoothing_factor,
        deadzone=config.deadzone
    )
    recognizer = GestureRecognizer(
        pinch_click_threshold=config.pinch_threshold,
        drag_hold_duration=config.drag_hold_duration,
        click_cooldown=config.click_cooldown,
        scroll_sensitivity=config.scroll_sensitivity
    )

    prev_time = time.time()
    cursor_preview = (0, 0)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Error] Frame capture interrupted.")
                break

            if config.flip_horizontal:
                frame = cv2.flip(frame, 1)

            # Detect landmarks
            frame = detector.find_hands(frame, draw=config.draw_landmarks)
            landmarks = detector.find_positions(frame)
            fingers = detector.fingers_up(landmarks)

            now = time.time()
            fps = 1.0 / max(1e-5, (now - prev_time))
            prev_time = now

            active_gesture, meta = recognizer.recognize(fingers, landmarks, current_time=now)

            # Map gesture to mouse actions
            if active_gesture == GestureType.MOVE:
                if len(landmarks) >= 21:
                    ix, iy = landmarks[HandLandmarks.INDEX_FINGER_TIP][1], landmarks[HandLandmarks.INDEX_FINGER_TIP][2]
                    cursor_preview = (ix, iy)
                    mouse.move_cursor(ix, iy)

            elif active_gesture == GestureType.DRAG:
                if len(landmarks) >= 21:
                    ix, iy = landmarks[HandLandmarks.INDEX_FINGER_TIP][1], landmarks[HandLandmarks.INDEX_FINGER_TIP][2]
                    cursor_preview = (ix, iy)
                    mouse.start_drag()
                    mouse.move_cursor(ix, iy)

            elif active_gesture == GestureType.LEFT_CLICK:
                mouse.left_click()

            elif active_gesture == GestureType.RIGHT_CLICK:
                mouse.right_click()

            elif active_gesture == GestureType.DOUBLE_CLICK:
                mouse.double_click()

            elif active_gesture == GestureType.SCROLL:
                scroll_delta = meta.get("scroll_delta", 0)
                if scroll_delta != 0:
                    mouse.scroll(scroll_delta)

            # If drag was ending
            if meta.get("drag_ended", False):
                mouse.end_drag()

            # Render HUD overlay
            if not args.no_hud and config.show_hud:
                draw_hud(frame, active_gesture, fps, config, cursor_preview, meta)

            cv2.imshow("AI Gesture Mouse", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                print("[Info] Terminating AI Gesture Mouse session.")
                break

    except KeyboardInterrupt:
        print("[Info] Keyboard interrupt received.")
    finally:
        mouse.end_drag()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
