"""
Mouse Controller Module — Enhanced Ultra-Smooth Edition.

Provides jitter-free cursor movement using a 3-stage smoothing pipeline:
  1. Deadzone gate       — Ignores micro-tremors below threshold
  2. Low-pass EMA        — Exponential moving average for signal smoothing
  3. Velocity-adaptive   — Loosens smoothing at high speed, tightens at low speed
     (feels like a real mouse: fast when you move fast, precise when you're slow)

OS-level mouse automation via PyAutoGUI with zero-latency configuration.
"""

from typing import Tuple, Optional
import time
import math

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0  # Zero latency — no artificial delay between calls
    PYAUTOGUI_AVAILABLE = True
except Exception:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False


class MouseController:
    """
    Translates camera coordinates into desktop cursor coordinates using a
    3-stage ultra-smooth pipeline. Feels natural and precise — better than a
    basic mouse for non-technical users.
    """

    def __init__(
        self,
        screen_size: Optional[Tuple[int, int]] = None,
        frame_size: Tuple[int, int] = (640, 480),
        frame_margin: int = 100,
        frame_margin_top: Optional[int] = None,
        frame_margin_bottom: Optional[int] = None,
        smoothing_factor: float = 5.0,
        deadzone: float = 3.0,
        enable_adaptive_smoothing: bool = True
    ):
        if screen_size is not None:
            self.screen_w, self.screen_h = screen_size
        elif PYAUTOGUI_AVAILABLE:
            try:
                self.screen_w, self.screen_h = pyautogui.size()
            except Exception:
                self.screen_w, self.screen_h = 1920, 1080
        else:
            self.screen_w, self.screen_h = 1920, 1080

        self.cam_w, self.cam_h = frame_size
        self.frame_margin = frame_margin
        self.frame_margin_top = frame_margin_top if frame_margin_top is not None else frame_margin
        self.frame_margin_bottom = frame_margin_bottom if frame_margin_bottom is not None else frame_margin
        self.smoothing = max(1.0, smoothing_factor)
        self.deadzone = deadzone
        self.enable_adaptive_smoothing = enable_adaptive_smoothing

        # Current smoothed screen position
        self.prev_x = self.screen_w / 2.0
        self.prev_y = self.screen_h / 2.0
        self.curr_x = self.prev_x
        self.curr_y = self.prev_y

        # Stage-2: Low-pass EMA buffer (pre-filter before mapping)
        self._ema_x: Optional[float] = None
        self._ema_y: Optional[float] = None
        # EMA alpha: lower = smoother but more lag, higher = faster but jittery
        # 0.40 is the sweet spot: smooth enough to hide tremors, fast enough to track intent
        self._ema_alpha: float = 0.40

        # Stage-3 velocity history for adaptive smoothing tuning
        self._velocity_history: list = []

        self.is_dragging = False
        self.last_click_time = 0.0
        self.last_velocity = 0.0

    def _ema_filter(self, raw_x: float, raw_y: float) -> Tuple[float, float]:
        """
        Stage-1 — Low-pass Exponential Moving Average on raw camera coordinates.
        Removes high-frequency jitter before coordinate mapping.
        Alpha is dynamically raised for fast movements so the cursor doesn't lag.
        """
        if self._ema_x is None:
            self._ema_x, self._ema_y = raw_x, raw_y
            return raw_x, raw_y

        # Compute how far the finger moved to decide EMA alpha dynamically
        raw_delta = math.hypot(raw_x - self._ema_x, raw_y - self._ema_y)

        # Fast motion (>30px): alpha → 0.70 (responsive)
        # Slow motion (<5px):  alpha → 0.25 (ultra-stable, tremor-free)
        dynamic_alpha = self._ema_alpha
        if raw_delta > 30:
            dynamic_alpha = min(0.72, self._ema_alpha + 0.32)
        elif raw_delta < 5:
            dynamic_alpha = max(0.22, self._ema_alpha - 0.18)

        self._ema_x = dynamic_alpha * raw_x + (1.0 - dynamic_alpha) * self._ema_x
        self._ema_y = dynamic_alpha * raw_y + (1.0 - dynamic_alpha) * self._ema_y
        return self._ema_x, self._ema_y

    def map_coordinates(self, x: float, y: float) -> Tuple[int, int]:
        """
        Maps camera coordinates within an active bounding box to screen coordinates.
        3-stage pipeline: EMA pre-filter → coordinate mapping → adaptive smoothing.
        When smoothing <= 1.0, directly maps coordinates without lag.
        """
        # If smoothing is 1.0 (disabled), direct 1-to-1 mapping
        if self.smoothing <= 1.0:
            x_min = self.frame_margin
            x_max = self.cam_w - self.frame_margin
            y_min = self.frame_margin_top
            y_max = self.cam_h - self.frame_margin_bottom

            clamped_x = max(x_min, min(x, x_max))
            clamped_y = max(y_min, min(y, y_max))

            norm_x = (clamped_x - x_min) / max(1.0, (x_max - x_min))
            norm_y = (clamped_y - y_min) / max(1.0, (y_max - y_min))

            self.curr_x = norm_x * self.screen_w
            self.curr_y = norm_y * self.screen_h
            self.prev_x = self.curr_x
            self.prev_y = self.curr_y
            return int(self.curr_x), int(self.curr_y)

        # ── Stage 1: EMA pre-filter on raw camera coordinates ──────────────────
        fx, fy = self._ema_filter(x, y)

        # ── Stage 2: Coordinate mapping (camera ROI → screen space) ────────────
        x_min = self.frame_margin
        x_max = self.cam_w - self.frame_margin
        y_min = self.frame_margin_top
        y_max = self.cam_h - self.frame_margin_bottom

        clamped_x = max(x_min, min(fx, x_max))
        clamped_y = max(y_min, min(fy, y_max))

        norm_x = (clamped_x - x_min) / max(1.0, (x_max - x_min))
        norm_y = (clamped_y - y_min) / max(1.0, (y_max - y_min))

        target_x = norm_x * self.screen_w
        target_y = norm_y * self.screen_h

        # ── Stage 3: Deadzone + adaptive velocity smoothing ─────────────────────
        dist = math.hypot(target_x - self.prev_x, target_y - self.prev_y)
        self.last_velocity = dist

        # Deadzone: ignore sub-threshold micro-movements (prevents cursor drift at rest)
        if dist < self.deadzone:
            target_x = self.prev_x
            target_y = self.prev_y

        if self.enable_adaptive_smoothing:
            # speed_factor scales 0→3.5 based on movement speed
            # High speed → small divisor → cursor reacts instantly
            # Low speed  → larger divisor → rock-steady precision
            speed_factor = min(3.5, dist / 20.0)
            effective_smoothing = max(1.0, self.smoothing / (1.0 + speed_factor * 1.2))
        else:
            effective_smoothing = self.smoothing

        self.curr_x = self.prev_x + (target_x - self.prev_x) / effective_smoothing
        self.curr_y = self.prev_y + (target_y - self.prev_y) / effective_smoothing

        self.prev_x = self.curr_x
        self.prev_y = self.curr_y

        return int(self.curr_x), int(self.curr_y)

    def move_cursor(self, x: float, y: float) -> Tuple[int, int]:
        """Calculates smoothed coordinates and positions mouse pointer."""
        target_x, target_y = self.map_coordinates(x, y)

        if PYAUTOGUI_AVAILABLE and pyautogui is not None:
            try:
                pyautogui.moveTo(target_x, target_y)
            except Exception:
                pass

        return target_x, target_y

    def left_click(self) -> None:
        """Performs standard single left mouse click."""
        if PYAUTOGUI_AVAILABLE and pyautogui is not None:
            try:
                pyautogui.click()
            except Exception:
                pass
        self.last_click_time = time.time()

    def right_click(self) -> None:
        """Performs right mouse click."""
        if PYAUTOGUI_AVAILABLE and pyautogui is not None:
            try:
                pyautogui.rightClick()
            except Exception:
                pass
        self.last_click_time = time.time()

    def double_click(self) -> None:
        """Performs double left mouse click."""
        if PYAUTOGUI_AVAILABLE and pyautogui is not None:
            try:
                pyautogui.doubleClick()
            except Exception:
                pass
        self.last_click_time = time.time()

    def scroll(self, clicks: int) -> None:
        """
        Scrolls the screen vertically.
        Positive values scroll up, negative values scroll down.
        Multiplied by Windows WHEEL_DELTA (120) so OS and PDF/browser apps respond.
        """
        if PYAUTOGUI_AVAILABLE and pyautogui is not None and clicks != 0:
            try:
                # 120 is the official Windows WHEEL_DELTA per notch
                pyautogui.scroll(int(clicks * 120))
            except Exception:
                pass

    def start_drag(self) -> None:
        """Holds mouse down for dragging operation."""
        if not self.is_dragging:
            self.is_dragging = True
            if PYAUTOGUI_AVAILABLE and pyautogui is not None:
                try:
                    pyautogui.mouseDown()
                except Exception:
                    pass

    def end_drag(self) -> None:
        """Releases mouse down to drop dragged element."""
        if self.is_dragging:
            self.is_dragging = False
            if PYAUTOGUI_AVAILABLE and pyautogui is not None:
                try:
                    pyautogui.mouseUp()
                except Exception:
                    pass
