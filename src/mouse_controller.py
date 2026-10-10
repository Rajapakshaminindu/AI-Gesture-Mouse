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
import collections

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

        # Stage-2: Multi-stage jitter filter (3-point median + 1-Euro adaptive EMA)
        self._raw_buf_x = collections.deque(maxlen=3)
        self._raw_buf_y = collections.deque(maxlen=3)
        self._filt_x: Optional[float] = None
        self._filt_y: Optional[float] = None
        self._filt_t: Optional[float] = None
        self._ema_x: Optional[float] = None
        self._ema_y: Optional[float] = None

        # Stage-3 velocity history for adaptive smoothing tuning
        self._velocity_history: list = []

        self.is_dragging = False
        self.last_click_time = 0.0
        self.last_velocity = 0.0

    def _ema_filter(self, raw_x: float, raw_y: float) -> Tuple[float, float]:
        """
        Stage-1 — Rolling 3-point median filter + 1-Euro adaptive low-pass filter
        on raw camera coordinates. Completely eliminates sensor pixel wobble and hand
        micro-tremors when stationary or moving slowly, while dynamically opening
        bandwidth during fast sweeps for zero latency.
        """
        self._raw_buf_x.append(raw_x)
        self._raw_buf_y.append(raw_y)
        med_x = sorted(self._raw_buf_x)[len(self._raw_buf_x) // 2]
        med_y = sorted(self._raw_buf_y)[len(self._raw_buf_y) // 2]

        if self._filt_x is None:
            self._filt_x, self._filt_y = med_x, med_y
            self._ema_x, self._ema_y = med_x, med_y
            self._filt_t = time.time()
            return med_x, med_y

        now = time.time()
        dt = max(0.001, now - (self._filt_t or now))
        if dt < 0.005:
            dt = 0.033
        self._filt_t = now

        raw_delta = math.hypot(med_x - self._filt_x, med_y - self._filt_y)

        # Stage-1 Noise Gate:
        # Micro-tremors (< 1.6 camera pixels) are heavily filtered with low alpha
        if raw_delta < 1.6:
            alpha = 0.04
            self._filt_x = alpha * med_x + (1.0 - alpha) * self._filt_x
            self._filt_y = alpha * med_y + (1.0 - alpha) * self._filt_y
            self._ema_x, self._ema_y = self._filt_x, self._filt_y
            return self._filt_x, self._filt_y

        # Intentional movement:
        # Cutoff frequency scales dynamically with velocity
        speed = raw_delta / dt
        cutoff = min(32.0, 0.4 + 0.05 * max(0.0, speed - 15.0))
        tau = 1.0 / (2.0 * math.pi * cutoff)
        dynamic_alpha = 1.0 / (1.0 + tau / dt)

        self._filt_x = dynamic_alpha * med_x + (1.0 - dynamic_alpha) * self._filt_x
        self._filt_y = dynamic_alpha * med_y + (1.0 - dynamic_alpha) * self._filt_y
        self._ema_x, self._ema_y = self._filt_x, self._filt_y
        return self._filt_x, self._filt_y

    def map_coordinates(self, x: float, y: float) -> Tuple[int, int]:
        """
        Maps camera coordinates within an active bounding box to screen coordinates.
        3-stage pipeline: Median + 1-Euro pre-filter → coordinate mapping → adaptive smoothing.
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

        # ── Stage 1: Noise gate + adaptive filter on camera coordinates ─────────
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

        # ── Stage 3: Deadzone + continuous velocity smoothing ───────────────────
        dist = math.hypot(target_x - self.prev_x, target_y - self.prev_y)
        self.last_velocity = dist

        # Deadzone gate: completely rock-solid when hand is at rest
        if dist < self.deadzone:
            return int(self.prev_x), int(self.prev_y)

        # Continuous threshold departure: prevents sudden jump when moving out of deadzone
        smooth_dist = dist - self.deadzone
        ratio = smooth_dist / max(1e-4, dist)
        adj_target_x = self.prev_x + (target_x - self.prev_x) * ratio
        adj_target_y = self.prev_y + (target_y - self.prev_y) * ratio

        if self.enable_adaptive_smoothing:
            speed_factor = min(4.0, max(0.0, dist - self.deadzone) / 16.0)
            effective_smoothing = max(1.2, self.smoothing / (1.0 + speed_factor * 2.0))
        else:
            effective_smoothing = self.smoothing

        self.curr_x = self.prev_x + (adj_target_x - self.prev_x) / effective_smoothing
        self.curr_y = self.prev_y + (adj_target_y - self.prev_y) / effective_smoothing

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
                pyautogui.doubleClick(interval=0.06)
            except Exception:
                try:
                    pyautogui.click()
                    time.sleep(0.04)
                    pyautogui.click()
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
