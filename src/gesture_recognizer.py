"""
Gesture Classification Engine and State Machine.

Classifies hand landmark poses into concrete mouse actions according to
the HackX AI Gesture Mouse specification.
"""

from enum import Enum
from typing import List, Tuple, Dict, Any, Optional
import time
import math


class GestureType(str, Enum):
    IDLE = "IDLE"
    MOVE = "MOVE"
    LEFT_CLICK = "LEFT_CLICK"
    RIGHT_CLICK = "RIGHT_CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    DRAG = "DRAG"
    SCROLL = "SCROLL"


class GestureRecognizer:
    """
    Evaluates finger configuration and distances to classify active gestures.
    Includes temporal state tracking to handle pinch-to-drag, debounce, and cooldowns.
    """

    def __init__(
        self,
        pinch_click_threshold: float = 38.0,
        drag_hold_duration: float = 0.45,
        click_cooldown: float = 0.35,
        scroll_sensitivity: float = 2.0
    ):
        self.pinch_click_threshold = pinch_click_threshold
        self.drag_hold_duration = drag_hold_duration
        self.click_cooldown = click_cooldown
        self.scroll_sensitivity = scroll_sensitivity

        # State tracking
        self.pinch_start_time: Optional[float] = None
        self.is_dragging = False
        self.last_action_time = 0.0
        self.last_click_timestamp = 0.0
        self.last_scroll_y: Optional[float] = None

    def recognize(
        self,
        fingers: List[int],
        landmarks: List[List[int]],
        current_time: Optional[float] = None
    ) -> Tuple[GestureType, Dict[str, Any]]:
        """
        Classifies current gesture from finger flags [thumb, index, middle, ring, pinky]
        and raw 21 landmark positions.
        """
        now = time.time() if current_time is None else current_time
        meta: Dict[str, Any] = {}

        if not landmarks or len(landmarks) < 21 or len(fingers) < 5:
            self._reset_transient_states()
            return GestureType.IDLE, meta

        thumb, index, middle, ring, pinky = fingers[0], fingers[1], fingers[2], fingers[3], fingers[4]

        # Calculate distance between thumb tip (4) and index tip (8)
        p_thumb = landmarks[4]
        p_index = landmarks[8]
        pinch_dist = math.hypot(p_thumb[1] - p_index[1], p_thumb[2] - p_index[2])
        meta["pinch_distance"] = pinch_dist

        # Calculate distance between thumb tip (4) and middle tip (12) for double click
        p_middle = landmarks[12]
        thumb_middle_dist = math.hypot(p_thumb[1] - p_middle[1], p_thumb[2] - p_middle[2])
        meta["thumb_middle_distance"] = thumb_middle_dist

        # 1. Check for Pinch (Left Click or Drag)
        # Pinch occurs when index tip is brought near thumb tip
        is_pinching = pinch_dist < self.pinch_click_threshold

        if is_pinching:
            if self.pinch_start_time is None:
                self.pinch_start_time = now

            duration = now - self.pinch_start_time

            # If held longer than drag threshold -> continuous DRAG
            if duration >= self.drag_hold_duration:
                self.is_dragging = True
                meta["drag_duration"] = duration
                return GestureType.DRAG, meta

            return GestureType.IDLE, meta

        else:
            # Pinch released: if we were dragging, end drag
            if self.is_dragging:
                self.is_dragging = False
                self.pinch_start_time = None
                self.last_action_time = now
                meta["drag_ended"] = True
                return GestureType.IDLE, meta

            # If pinch was released quickly before drag threshold -> triggers LEFT_CLICK
            if self.pinch_start_time is not None:
                duration = now - self.pinch_start_time
                self.pinch_start_time = None

                if duration < self.drag_hold_duration and (now - self.last_action_time) > self.click_cooldown:
                    self.last_action_time = now
                    self.last_click_timestamp = now
                    return GestureType.LEFT_CLICK, meta

        # 2. Right Click Gesture: Three fingers raised (Index, Middle, Ring UP; Pinky DOWN)
        # As documented in Proposal Page 4 & 7
        if index == 1 and middle == 1 and ring == 1 and pinky == 0:
            if (now - self.last_action_time) > self.click_cooldown:
                self.last_action_time = now
                return GestureType.RIGHT_CLICK, meta
            return GestureType.IDLE, meta

        # 3. Double Click: Thumb + Middle pinch while index is extended
        if thumb_middle_dist < self.pinch_click_threshold and index == 1:
            if (now - self.last_action_time) > self.click_cooldown:
                self.last_action_time = now
                return GestureType.DOUBLE_CLICK, meta
            return GestureType.IDLE, meta

        # 4. Two-Finger Scroll: Index & Middle UP, Ring & Pinky DOWN (Peace sign pose)
        if index == 1 and middle == 1 and ring == 0 and pinky == 0:
            center_y = (landmarks[8][2] + landmarks[12][2]) / 2.0
            scroll_delta = 0

            if self.last_scroll_y is not None:
                diff = self.last_scroll_y - center_y
                if abs(diff) > 5.0:
                    scroll_delta = int(diff * self.scroll_sensitivity)

            self.last_scroll_y = center_y
            meta["scroll_delta"] = scroll_delta
            return GestureType.SCROLL, meta
        else:
            self.last_scroll_y = None

        # 5. Move Cursor: Only Index Finger UP (Pointing Pose)
        if index == 1 and middle == 0 and ring == 0 and pinky == 0:
            meta["cursor_pt"] = (landmarks[8][1], landmarks[8][2])
            return GestureType.MOVE, meta

        return GestureType.IDLE, meta

    def _reset_transient_states(self) -> None:
        """Resets tracking when hand disappears."""
        self.pinch_start_time = None
        self.is_dragging = False
        self.last_scroll_y = None
