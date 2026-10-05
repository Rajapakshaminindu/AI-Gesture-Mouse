"""
AI Gesture Mouse - Main Execution Pipeline.

Combines camera capture, MediaPipe hand landmark tracking, gesture recognition,
adaptive cursor smoothing, action mapping hotkeys, analytics telemetry,
startup splash screen, and interactive HUD overlay.
"""

import sys
import time
import argparse
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np

# Import cv2 with explicit error handling
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    print("[Error] OpenCV (cv2) is not installed. Please run: pip install -r requirements.txt")
    CV2_AVAILABLE = False
    sys.exit(1)

from src.config import AppConfig
from src.hand_detector import HandDetector, HandLandmarks
from src.mouse_controller import MouseController
from src.gesture_recognizer import GestureRecognizer, GestureType
from src.action_mapper import ActionMapper
from src.analytics import GestureAnalytics


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


# Global ring animation tracker for click feedback
click_animation_counter = 0
click_animation_pos = (0, 0)


def draw_splash_screen(frame: np.ndarray, elapsed_time: float, total_duration: float = 2.0) -> None:
    """Renders a sleek startup splash screen with smooth alpha fade-out."""
    if elapsed_time >= total_duration:
        return

    h, w, _ = frame.shape
    overlay = frame.copy()

    # Dim background
    cv2.rectangle(overlay, (0, 0), (w, h), (15, 15, 20), -1)

    # Accent decorative box
    box_w, box_h = min(520, w - 40), 220
    x1, y1 = (w - box_w) // 2, (h - box_h) // 2
    cv2.rectangle(overlay, (x1, y1), (x1 + box_w, y1 + box_h), (35, 35, 45), -1)
    cv2.rectangle(overlay, (x1, y1), (x1 + box_w, y1 + box_h), (0, 210, 255), 2)

    # Header and Instructions
    cv2.putText(overlay, "AI GESTURE MOUSE", (x1 + 40, y1 + 60),
                cv2.FONT_HERSHEY_DUPLEX, 1.1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(overlay, "- Point index finger to guide cursor", (x1 + 40, y1 + 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(overlay, "- Pinch thumb + index finger to click", (x1 + 40, y1 + 145),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(overlay, "- Quick horizontal flick for browser swipe", (x1 + 40, y1 + 180),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 220, 255), 1, cv2.LINE_AA)

    # Calculate fade out over the final 0.5s
    remaining = total_duration - elapsed_time
    alpha = min(0.88, max(0.0, remaining / 0.5)) if remaining < 0.5 else 0.88

    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)


def draw_hud(
    frame: np.ndarray,
    active_gesture: GestureType,
    fps: float,
    config: AppConfig,
    cursor_pos: tuple,
    meta: dict
) -> None:
    """Renders semi-transparent dashboard, gesture color states, crosshair, and click ring."""
    global click_animation_counter, click_animation_pos
    h, w, _ = frame.shape

    # 1. Active Interaction Boundary & Crosshair
    x_min, y_min = config.frame_margin, config.frame_margin
    x_max, y_max = w - config.frame_margin, h - config.frame_margin
    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (70, 70, 70), 1)

    # Center Crosshair
    cx, cy = (x_min + x_max) // 2, (y_min + y_max) // 2
    cv2.line(frame, (cx - 10, cy), (cx + 10, cy), (100, 100, 100), 1)
    cv2.line(frame, (cx, cy - 10), (cx, cy + 10), (100, 100, 100), 1)

    # 2. Semi-Transparent Top Dashboard Panel
    panel_w, panel_h = 360, 52
    overlay = frame.copy()
    cv2.rectangle(overlay, (15, 12), (15 + panel_w, 12 + panel_h), (18, 18, 22), -1)
    cv2.rectangle(overlay, (15, 12), (15 + panel_w, 12 + panel_h), (50, 50, 60), 1)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

    # Color Mapping according to state
    color_palette = {
        GestureType.MOVE: (0, 255, 0),          # Green
        GestureType.LEFT_CLICK: (0, 255, 255),   # Yellow
        GestureType.RIGHT_CLICK: (0, 165, 255),  # Orange
        GestureType.DOUBLE_CLICK: (255, 0, 255), # Magenta
        GestureType.DRAG: (0, 140, 255),         # Deep Orange
        GestureType.SCROLL: (255, 255, 0),       # Cyan
        GestureType.SWIPE_LEFT: (255, 120, 50),  # Blue-Cyan
        GestureType.SWIPE_RIGHT: (255, 120, 50),
        GestureType.IDLE: (220, 220, 220)        # White
    }
    gesture_name = active_gesture.value if hasattr(active_gesture, "value") else str(active_gesture)
    badge_color = color_palette.get(active_gesture, (220, 220, 220))

    # Mode Indicator Pill
    cv2.circle(frame, (35, 38), 7, badge_color, -1)
    cv2.putText(
        frame, f"STATE: {gesture_name}", (52, 43),
        cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA
    )

    # Telemetry Info (FPS & Smoothing)
    cv2.putText(
        frame, f"FPS {int(fps)} | SM {config.smoothing_factor}", (240, 43),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 200, 240), 1, cv2.LINE_AA
    )

    # 3. Click Ring Trigger
    if active_gesture in (GestureType.LEFT_CLICK, GestureType.RIGHT_CLICK):
        click_animation_counter = 6
        click_animation_pos = cursor_pos

    # Render expanding ripple ring when click occurs
    if click_animation_counter > 0:
        radius = int((7 - click_animation_counter) * 6) + 10
        cv2.circle(frame, click_animation_pos, radius, (0, 255, 255), 2, cv2.LINE_AA)
        click_animation_counter -= 1


def open_working_camera(preferred_idx: int, width: int, height: int) -> tuple[cv2.VideoCapture, int]:
    """Probes candidate camera indices and returns the first one delivering live video frames."""
    if not CV2_AVAILABLE or cv2 is None:
        print("[Error] OpenCV is not available. Cannot access camera.")
        return None, -1

    candidates = [preferred_idx] + [i for i in (1, 0, 2, 3) if i != preferred_idx]
    
    for idx in candidates:
        try:
            cap = cv2.VideoCapture(idx)
            if cap is None:
                print(f"[Warning] Camera device #{idx} returned None object.")
                continue
                
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # Minimize frame buffer lag
                cap.set(cv2.CAP_PROP_FPS, 30)          # Request 30 fps from camera
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    print(f"[Info] Successfully connected to live camera device #{idx}.")
                    return cap, idx
                cap.release()
        except Exception as e:
            print(f"[Warning] Failed to open camera device #{idx}: {e}")
            continue

    # Final fallback attempt
    try:
        print(f"[Info] Attempting fallback to preferred camera index #{preferred_idx}...")
        cap = cv2.VideoCapture(preferred_idx)
        if cap is not None and cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FPS, 30)
            return cap, preferred_idx
    except Exception as e:
        print(f"[Error] Fallback camera attempt failed: {e}")
    
    return None, -1


def main() -> None:
    # Verify dependencies
    if not CV2_AVAILABLE:
        print("[Error] OpenCV is required. Please install it: pip install -r requirements.txt")
        sys.exit(1)

    args = parse_arguments()
    config = AppConfig.load(args.config)
    camera_idx = args.camera if args.camera is not None else config.camera_index

    print(f"[Info] Initializing camera device #{camera_idx}...")
    cap, active_cam_idx = open_working_camera(camera_idx, config.frame_width, config.frame_height)

    if cap is None or not cap.isOpened():
        print(f"[Error] Failed to open any camera device. Please check:")
        print("  - Camera is connected and not in use by another application")
        print("  - Camera permissions are granted")
        print("  - Try specifying a different camera with --camera <index>")
        sys.exit(1)

    detector = HandDetector(
        detection_con=config.detection_confidence,
        track_con=config.tracking_confidence
    )
    recognizer = GestureRecognizer(
        pinch_click_threshold=config.pinch_threshold,
        drag_hold_duration=config.drag_hold_duration,
        click_cooldown=config.click_cooldown,
        scroll_sensitivity=config.scroll_sensitivity
    )
    mouse = MouseController(
        frame_size=(config.frame_width, config.frame_height),
        frame_margin=config.frame_margin,
        smoothing_factor=config.smoothing_factor,
        deadzone=config.deadzone,
        enable_adaptive_smoothing=config.enable_adaptive_smoothing
    )
    action_mapper = ActionMapper(custom_bindings=config.action_bindings)
    analytics = GestureAnalytics() if config.enable_analytics else None

    prev_time = time.time()
    start_time = time.time()
    fps = 0.0
    # Stores the last cursor position from MOVE state — used for all action gestures
    # to prevent cursor drift when hand shape changes to form a gesture
    locked_cursor_pos = (config.frame_width // 2, config.frame_height // 2)

    print("AI Gesture Mouse operational. Press 'q' in webcam window to terminate.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Warning] Failed to read frame from camera. Retrying...")
                time.sleep(0.1)
                continue

            if frame is None or frame.size == 0:
                print("[Warning] Received empty frame from camera.")
                time.sleep(0.1)
                continue

            if config.flip_horizontal:
                frame = cv2.flip(frame, 1)

            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 30.0
            prev_time = curr_time

            # Hand Tracking — pass real timestamp in ms for VIDEO mode accuracy
            timestamp_ms = int(curr_time * 1000)
            if hasattr(detector, '_frame_timestamp_ms'):
                detector._frame_timestamp_ms = timestamp_ms
            frame = detector.find_hands(frame, draw=config.draw_landmarks)
            landmarks = detector.find_positions(frame)
            fingers = detector.fingers_up(landmarks)

            active_gesture = GestureType.IDLE
            meta = {}
            cursor_pos = (config.frame_width // 2, config.frame_height // 2)

            if landmarks and len(landmarks) >= 21:
                # landmarks[8] = [id, x, y]; use [1],[2] for pixel coords
                cursor_pos = (landmarks[8][1], landmarks[8][2])
                active_gesture, meta = recognizer.recognize(fingers, landmarks, current_time=curr_time)

                # Check for pause tracking status via ActionMapper
                if not action_mapper.tracking_paused:
                    # Dispatch gesture to mouse controller
                    if active_gesture == GestureType.MOVE:
                        # Only update locked position while actively moving
                        locked_cursor_pos = cursor_pos
                        mouse.move_cursor(cursor_pos[0], cursor_pos[1])
                    elif active_gesture == GestureType.LEFT_CLICK:
                        # Use locked position — cursor must NOT drift during click gesture
                        mouse.move_cursor(locked_cursor_pos[0], locked_cursor_pos[1])
                        mouse.left_click()
                    elif active_gesture == GestureType.RIGHT_CLICK:
                        mouse.move_cursor(locked_cursor_pos[0], locked_cursor_pos[1])
                        mouse.right_click()
                    elif active_gesture == GestureType.DOUBLE_CLICK:
                        mouse.move_cursor(locked_cursor_pos[0], locked_cursor_pos[1])
                        mouse.double_click()
                    elif active_gesture == GestureType.DRAG:
                        mouse.move_cursor(locked_cursor_pos[0], locked_cursor_pos[1])
                        mouse.start_drag()
                    elif active_gesture == GestureType.SCROLL:
                        scroll_delta = meta.get("scroll_delta", 0)
                        mouse.scroll(int(scroll_delta * config.scroll_sensitivity))
                    elif active_gesture in (GestureType.SWIPE_LEFT, GestureType.SWIPE_RIGHT):
                        action_mapper.trigger_action(active_gesture.value, current_time=curr_time)
                    else:
                        # IDLE or drag released – if drag was active, end it
                        if mouse.is_dragging:
                            mouse.end_drag()

            # Record Telemetry Frame
            if analytics is not None:
                g_name = active_gesture.value if hasattr(active_gesture, "value") else str(active_gesture)
                analytics.log_frame(g_name, fps, cursor_pos)

            # Draw HUD
            if not args.no_hud and config.show_hud:
                draw_hud(frame, active_gesture, fps, config, cursor_pos, meta)

            # Draw Splash Screen during first 2 seconds
            elapsed = curr_time - start_time
            if elapsed < 2.0:
                draw_splash_screen(frame, elapsed, total_duration=2.0)

            cv2.imshow("AI Gesture Mouse", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                break

    except KeyboardInterrupt:
        print("\n[Info] Interrupted by user.")
    except Exception as e:
        print(f"[Error] Unexpected error in main loop: {e}")
        import traceback
        traceback.print_exc()
    finally:
        mouse.end_drag()
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        if analytics is not None:
            analytics.export_report()
        print("[Info] Cleanup complete. Exiting.")


if __name__ == "__main__":
    main()
