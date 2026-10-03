python
"""
AI Gesture Mouse - Main Execution Pipeline.

Combines camera capture, MediaPipe hand landmark tracking, gesture recognition,
smooth cursor interpolation, startup splash screen, and interactive HUD overlay.
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
        GestureType.MOVE: (0, 255, 0),         # Green
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
