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
from src.launcher_ui import LauncherWindow


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
    box_w, box_h = min(540, w - 40), 260
    x1, y1 = (w - box_w) // 2, (h - box_h) // 2
    cv2.rectangle(overlay, (x1, y1), (x1 + box_w, y1 + box_h), (35, 35, 45), -1)
    cv2.rectangle(overlay, (x1, y1), (x1 + box_w, y1 + box_h), (0, 210, 255), 2)

    # Header and Instructions
    cv2.putText(overlay, "AI GESTURE MOUSE", (x1 + 40, y1 + 55),
                cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(overlay, "- Point index finger = Move cursor", (x1 + 40, y1 + 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(overlay, "- 2 Fingers (Index+Middle) = Left Click (one-shot)", (x1 + 40, y1 + 118),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(overlay, "- 3 Fingers (Index+Middle+Ring) = Smooth Scroll", (x1 + 40, y1 + 146),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(overlay, "- Thumbs Up = Right Click", (x1 + 40, y1 + 174),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(overlay, "- Open hand (back 5 fingers) = Double Click", (x1 + 40, y1 + 202),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(overlay, "Tip: Window stays pinned on top. Press 'm' to resize.", (x1 + 40, y1 + 230),
                cv2.FONT_HERSHEY_SIMPLEX, 0.46, (140, 200, 140), 1, cv2.LINE_AA)

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
    x_min, x_max = config.frame_margin, w - config.frame_margin
    y_min = getattr(config, "frame_margin_top", config.frame_margin)
    y_max = h - getattr(config, "frame_margin_bottom", config.frame_margin)
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
        GestureType.SCROLL: (0, 255, 255),       # Bright Yellow/Cyan
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

    # Telemetry Info (FPS, Smoothing, Palm Orientation)
    orientation_hint = meta.get("palm_orientation", "")
    orient_label = f" | {orientation_hint}" if orientation_hint and orientation_hint != "UNKNOWN" else ""
    cv2.putText(
        frame, f"FPS {int(fps)} | SM {config.smoothing_factor}{orient_label}", (210, 43),
        cv2.FONT_HERSHEY_SIMPLEX, 0.44, (160, 200, 240), 1, cv2.LINE_AA
    )

    # 3. Dedicated Scroll HUD Widget
    if active_gesture == GestureType.SCROLL:
        scroll_mode = meta.get("scroll_mode", "HOLD")
        scroll_delta = meta.get("scroll_delta", 0)
        s_box_w, s_box_h = 240, 38
        s_x = (w - s_box_w) // 2
        s_y = h - s_box_h - 18
        s_overlay = frame.copy()
        cv2.rectangle(s_overlay, (s_x, s_y), (s_x + s_box_w, s_y + s_box_h), (20, 20, 25), -1)
        cv2.rectangle(s_overlay, (s_x, s_y), (s_x + s_box_w, s_y + s_box_h), (0, 255, 255), 2)
        cv2.addWeighted(s_overlay, 0.80, frame, 0.20, 0, frame)

        if scroll_delta > 0 or scroll_mode == "UP":
            s_text = f"SCROLL UP  ▲"
            s_color = (0, 255, 128)
        elif scroll_delta < 0 or scroll_mode == "DOWN":
            s_text = f"SCROLL DOWN  ▼"
            s_color = (0, 200, 255)
        else:
            s_text = "SCROLL: READY"
            s_color = (255, 255, 255)

        cv2.putText(frame, s_text, (s_x + 24, s_y + 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, s_color, 2, cv2.LINE_AA)

    # 4. Click Ring Trigger
    if active_gesture in (GestureType.LEFT_CLICK, GestureType.RIGHT_CLICK, GestureType.DOUBLE_CLICK):
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
    # ── Show Launcher UI first ────────────────────────────────────────────────
    launcher = LauncherWindow()
    started = launcher.show()     # blocks until Start clicked or window closed
    launcher.destroy()

    if not started:
        print("[Info] Launcher closed without starting. Exiting.")
        sys.exit(0)

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
        frame_margin_top=config.frame_margin_top,
        frame_margin_bottom=config.frame_margin_bottom,
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
    print("  'm' = toggle compact/full window size | 'h' = move window to corner")

    # ── Window setup: always-on-top, compact, bottom-right corner ─────────────
    WIN_TITLE = "AI Gesture Mouse"
    COMPACT_W, COMPACT_H = 340, 255   # compact preview that stays out of the way

    cv2.namedWindow(WIN_TITLE, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_TITLE, COMPACT_W, COMPACT_H)
    try:
        cv2.setWindowProperty(WIN_TITLE, cv2.WND_PROP_TOPMOST, 1)
    except Exception:
        pass

    # Position: bottom-right corner (12px margin from edges, above taskbar)
    try:
        import ctypes
        user32 = ctypes.windll.user32
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        win_x = screen_w - COMPACT_W - 12
        win_y = screen_h - COMPACT_H - 65   # 65px offset for Windows taskbar
    except Exception:
        win_x, win_y = 10, 10

    cv2.moveWindow(WIN_TITLE, win_x, win_y)

    def set_always_on_top(win_name: str) -> None:
        """
        Forces the OpenCV preview window to stay pinned on top of ALL applications
        (PDF readers, browsers, full screen apps) without stealing keyboard/mouse focus.
        """
        try:
            cv2.setWindowProperty(win_name, cv2.WND_PROP_TOPMOST, 1)
        except Exception:
            pass

        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, win_name)
            if hwnd:
                GWL_EXSTYLE = -20
                cur_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                # WS_EX_TOPMOST = 0x08 (float on top of all other windows)
                # WS_EX_TOOLWINDOW = 0x80 (tool overlay, doesn't hide when another window gains focus)
                WS_EX_TOPMOST = 0x00000008
                WS_EX_TOOLWINDOW = 0x00000080
                new_style = (cur_style | WS_EX_TOPMOST | WS_EX_TOOLWINDOW) & ~0x08000000
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

                HWND_TOPMOST = -1
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOACTIVATE = 0x0010
                SWP_SHOWWINDOW = 0x0040
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
                )
        except Exception:
            pass

    _last_topmost_assert = 0.0
    _is_compact = True
    _window_closed = False   # set True the moment the user clicks X

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
            handedness = detector.get_handedness()
            fingers = detector.fingers_up(landmarks, handedness=handedness)

            active_gesture = GestureType.IDLE
            meta = {}
            cursor_pos = (config.frame_width // 2, config.frame_height // 2)

            if landmarks and len(landmarks) >= 21:
                # landmarks[8] = [id, x, y]; use [1],[2] for pixel coords
                cursor_pos = (landmarks[8][1], landmarks[8][2])
                active_gesture, meta = recognizer.recognize(
                    fingers, landmarks, current_time=curr_time, handedness=handedness
                )

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
                    elif active_gesture == GestureType.SCROLL:
                        scroll_delta = meta.get("scroll_delta", 0)
                        if scroll_delta != 0:
                            mouse.scroll(scroll_delta)
                    elif active_gesture in (GestureType.SWIPE_LEFT, GestureType.SWIPE_RIGHT):
                        action_mapper.trigger_action(active_gesture.value, current_time=curr_time)
                    else:
                        # IDLE / neutral — no action
                        pass


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

            # ── 1. Check keyboard & window-close BEFORE imshow ────────────────
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                print("\n[Info] Quit key pressed.")
                break
            elif key == ord('m'):   # toggle compact / full size
                _is_compact = not _is_compact
                if _is_compact:
                    cv2.resizeWindow(WIN_TITLE, COMPACT_W, COMPACT_H)
                    cv2.moveWindow(WIN_TITLE, win_x, win_y)
                else:
                    cv2.resizeWindow(WIN_TITLE, config.frame_width, config.frame_height)
                    cv2.moveWindow(WIN_TITLE, 10, 10)
                set_always_on_top(WIN_TITLE)
            elif key == ord('h'):   # snap back to corner
                cv2.moveWindow(WIN_TITLE, win_x, win_y)
                set_always_on_top(WIN_TITLE)

            # ── 2. Detect X-button close BEFORE showing next frame ────────────
            # IMPORTANT: cv2.imshow() RECREATES a destroyed window, so we must
            # check visibility first and break before imshow is called again.
            if not _window_closed:
                try:
                    if cv2.getWindowProperty(WIN_TITLE, cv2.WND_PROP_VISIBLE) < 1:
                        _window_closed = True
                        print("\n[Info] Window closed by user.")
                        break
                except Exception:
                    pass

            # ── 3. Emergency Esc key (works even when window is not focused) ──
            try:
                import ctypes
                if ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000:
                    print("\n[Info] Emergency exit: Esc pressed.")
                    break
            except Exception:
                pass

            # ── 4. Render frame ───────────────────────────────────────────────
            cv2.imshow(WIN_TITLE, frame)

            # ── 5. Re-assert always-on-top every 1 second ─────────────────────
            if not _window_closed and curr_time - _last_topmost_assert > 1.0:
                set_always_on_top(WIN_TITLE)
                _last_topmost_assert = curr_time

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
