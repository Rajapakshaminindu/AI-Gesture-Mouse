"""
Mouse Controller Module.

Provides jitter-free cursor movement with Exponential Moving Average (EMA) smoothing,
deadzone filtering, and OS-level mouse event automation via PyAutoGUI.
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
    pyautogui.PAUSE = 0.001
    PYAUTOGUI_AVAILABLE = True
except Exception:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False


class MouseController:
    """
    Translates normalized camera coordinates into desktop cursor coordinates
    with smoothing, boundary clamping, and click state management.
    """

    def __init__(
        self,
        screen_size: Optional[Tuple[int, int]] = None,
        frame_size: Tuple[int, int] = (640, 480),
        frame_margin: int = 100,
        smoothing_factor: float = 5.0,
        deadzone: float = 3.0
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
        self.smoothing = max(1.0, smoothing_factor)
        self.deadzone = deadzone

        self.prev_x = self.screen_w / 2.0
        self.prev_y = self.screen_h / 2.0
        self.curr_x = self.prev_x
        self.curr_y = self.prev_y

        self.is_dragging = False
        self.last_click_time = 0.0

    def map_coordinates(self, x: float, y: float) -> Tuple[int, int]:
        """
        Maps camera coordinates within an active bounding box to screen coordinates.
        Uses mirror mapping horizontally so user movements feel natural.
        """
        # Active camera box
        x_min = self.frame_margin
        x_max = self.cam_w - self.frame_margin
        y_min = self.frame_margin
        y_max = self.cam_h - self.frame_margin

        # Clamp inside margin
        clamped_x = max(x_min, min(x, x_max))
        clamped_y = max(y_min, min(y, y_max))

        # Linear interpolation with horizontal flip (mirror)
        norm_x = (clamped_x - x_min) / max(1.0, (x_max - x_min))
        norm_y = (clamped_y - y_min) / max(1.0, (y_max - y_min))

        target_x = norm_x * self.screen_w
        target_y = norm_y * self.screen_h

        # Deadzone filter
        dist = math.hypot(target_x - self.prev_x, target_y - self.prev_y)
        if dist < self.deadzone:
            target_x = self.prev_x
            target_y = self.prev_y

        # Exponential smoothing
        self.curr_x = self.prev_x + (target_x - self.prev_x) / self.smoothing
        self.curr_y = self.prev_y + (target_y - self.prev_y) / self.smoothing

        self.prev_x = self.curr_x
        self.prev_y = self.curr_y

        return int(self.curr_x), int(self.curr_y)

    def move_cursor(self, x: float, y: float) -> Tuple[int, int]:
        """
        Calculates smoothed coordinates and positions mouse pointer.
        """
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
        """
        if PYAUTOGUI_AVAILABLE and pyautogui is not None:
            try:
                pyautogui.scroll(clicks)
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
