"""
Gesture Classification Engine and State Machine.

Classifies hand landmark poses into concrete mouse actions according to
the HackX AI Gesture Mouse specification.
Includes per-gesture cooldown debounce, temporal drag state tracking,
and dynamic horizontal swipe detection.
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
    SWIPE_LEFT = "SWIPE_LEFT"
    SWIPE_RIGHT = "SWIPE_RIGHT"


class GestureRecognizer:
    """
    Evaluates finger configuration, distance metrics, and temporal dynamics
    to classify active gestures with per-gesture debounce and swipe recognition.
    """

    def __init__(
        self,
        pinch_click_threshold: float = 45.0,  # Increased: easier to trigger left click
        drag_hold_duration: float = 0.35,  # Faster drag detection so click window feels snappier
        click_cooldown: float = 0.25,
        scroll_sensitivity: float = 2.0,
        swipe_velocity_threshold: float = 400.0,
        confidence_threshold: float = 0.75,
        cooldowns: Optional[Dict[str, float]] = None
    ):
        self.pinch_click_threshold = pinch_click_threshold
        self.drag_hold_duration = drag_hold_duration
        self.click_cooldown = click_cooldown
        self.scroll_sensitivity = scroll_sensitivity
        self.swipe_velocity_threshold = swipe_velocity_threshold
        self.confidence_threshold = confidence_threshold

        # Per-gesture configurable cooldown dictionary (in seconds)
        self.cooldowns: Dict[str, float] = {
            GestureType.LEFT_CLICK.value: click_cooldown,
            GestureType.RIGHT_CLICK.value: 0.70,  # Longer cooldown — prevents repeated firing while held
            GestureType.DOUBLE_CLICK.value: 0.70,  # longer cooldown — prevents palm-hold spam
            GestureType.SWIPE_LEFT.value: 0.60,
            GestureType.SWIPE_RIGHT.value: 0.60,
        }
        if cooldowns:
            self.cooldowns.update(cooldowns)

        # Per-gesture timestamp trackers
        self.last_triggered_time: Dict[str, float] = {}

        # Drag state tracking
        self.pinch_start_time: Optional[float] = None
        self.is_dragging: bool = False

        # Swipe tracking: stores (timestamp, x_position) history
        self.swipe_history: List[Tuple[float, float]] = []

    def _euclidean_distance(self, p1: List[int], p2: List[int]) -> float:
        """Calculate 2D Euclidean distance between landmark points.

        Landmarks may be 2-element [x, y] or 3-element [id, x, y].
        Detects format automatically and uses the correct indices.
        """
        if len(p1) == 3:  # [id, x, y] format from HandDetector.find_positions()
            return math.hypot(p1[1] - p2[1], p1[2] - p2[2])
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])  # [x, y] format

    def _is_cooling_down(self, gesture: GestureType, now: float) -> bool:
        """Check if a gesture is currently blocked by its individual cooldown period."""
        gesture_name = gesture.value
        cooldown_period = self.cooldowns.get(gesture_name, 0.0)
        last_time = self.last_triggered_time.get(gesture_name, 0.0)
        return (now - last_time) < cooldown_period

    def _record_trigger(self, gesture: GestureType, now: float) -> None:
        """Record timestamp for debouncing."""
        self.last_triggered_time[gesture.value] = now

    def _detect_swipe(self, index_tip: List[int], now: float) -> Optional[GestureType]:
        """
        Detect quick horizontal swipe movement of index tip.
        Maintains a rolling window of recent positions (last 0.25 seconds).
        Supports both [x, y] and [id, x, y] landmark formats.
        """
        # Extract x coordinate — handle both [x,y] and [id,x,y] formats
        tip_x = float(index_tip[1]) if len(index_tip) == 3 else float(index_tip[0])
        self.swipe_history.append((now, tip_x))

        # Keep history within last 0.25 seconds
        self.swipe_history = [(t, x) for t, x in self.swipe_history if (now - t) <= 0.25]

        if len(self.swipe_history) < 2:
            return None

        dt = self.swipe_history[-1][0] - self.swipe_history[0][0]
        if dt < 0.05:
            return None

        dx = self.swipe_history[-1][1] - self.swipe_history[0][1]
        velocity = dx / dt  # pixels per second

        if abs(velocity) >= self.swipe_velocity_threshold:
            self.swipe_history.clear()
            if velocity < -self.swipe_velocity_threshold:
                return GestureType.SWIPE_LEFT
            elif velocity > self.swipe_velocity_threshold:
                return GestureType.SWIPE_RIGHT

        return None

    def recognize(
        self,
        fingers: List[int],
        landmarks: List[List[int]],
        confidence: float = 1.0,
        current_time: Optional[float] = None
    ) -> Tuple[GestureType, Dict[str, Any]]:
        """
        Classifies current gesture from finger flags [thumb, index, middle, ring, pinky]
        and raw 21 landmark positions.
        """
        now = time.time() if current_time is None else current_time
        meta: Dict[str, Any] = {"confidence": confidence}

        # Confidence gate filter
        if confidence < self.confidence_threshold:
            return GestureType.IDLE, {"status": "low_confidence", "confidence": confidence}

        if not landmarks or len(landmarks) < 21:
            return GestureType.IDLE, {"status": "insufficient_landmarks"}

        thumb, index, middle, ring, pinky = fingers if len(fingers) == 5 else [0, 0, 0, 0, 0]

        # Check for swipe gestures (active when only index finger is extended)
        if index == 1 and middle == 0 and ring == 0 and pinky == 0:
            swipe = self._detect_swipe(landmarks[8], now)
            if swipe is not None:
                if not self._is_cooling_down(swipe, now):
                    self._record_trigger(swipe, now)
                    return swipe, {"velocity": swipe.value}
                return GestureType.IDLE, {"status": "cooldown_blocked"}

        # Measure pinch distance between Thumb tip (4) and Index tip (8)
        pinch_dist = self._euclidean_distance(landmarks[4], landmarks[8])
        meta["pinch_distance"] = pinch_dist

        # Pinch detection (Left Click or Drag)
        if pinch_dist < self.pinch_click_threshold:
            if self.pinch_start_time is None:
                self.pinch_start_time = now
                # Clear swipe history to prevent false swipe detection after pinch
                self.swipe_history.clear()

            hold_duration = now - self.pinch_start_time
            meta["pinch_hold_time"] = hold_duration

            if hold_duration >= self.drag_hold_duration:
                self.is_dragging = True
                meta["drag_duration"] = hold_duration
                return GestureType.DRAG, meta
            else:
                return GestureType.IDLE, meta
        else:
            # Pinch released: check if it was a quick click or drag termination
            if self.pinch_start_time is not None:
                hold_duration = now - self.pinch_start_time
                self.pinch_start_time = None

                if self.is_dragging:
                    self.is_dragging = False
                    return GestureType.IDLE, {"status": "drag_released"}

                if hold_duration < self.drag_hold_duration:
                    if not self._is_cooling_down(GestureType.LEFT_CLICK, now):
                        self._record_trigger(GestureType.LEFT_CLICK, now)
                        return GestureType.LEFT_CLICK, meta
                    return GestureType.IDLE, {"status": "cooldown_blocked"}

        # Double Click: 4 fingers up — index+middle+ring+pinky, thumb ignored
        # Easy natural transition from index-only move gesture
        # Thumb NOT required — thumb detection is unreliable when hand is angled
        if index == 1 and middle == 1 and ring == 1 and pinky == 1:
            if not self._is_cooling_down(GestureType.DOUBLE_CLICK, now):
                self._record_trigger(GestureType.DOUBLE_CLICK, now)
                return GestureType.DOUBLE_CLICK, meta
            return GestureType.IDLE, {"status": "cooldown_blocked"}

        # Right click: 3-finger salute — index+middle+ring up, pinky DOWN
        # pinky==0 ensures no overlap with double click (4 fingers)
        if index == 1 and middle == 1 and ring == 1 and pinky == 0:
            if not self._is_cooling_down(GestureType.RIGHT_CLICK, now):
                self._record_trigger(GestureType.RIGHT_CLICK, now)
                return GestureType.RIGHT_CLICK, meta
            return GestureType.IDLE, {"status": "cooldown_blocked"}

        # Scrolling: Peace sign (index + middle only, ring==0)
        middle_index_dist = self._euclidean_distance(landmarks[8], landmarks[12])
        if index == 1 and middle == 1 and ring == 0:
            # Compute average Y of index+middle tips for scroll delta tracking
            if len(landmarks[8]) == 3:
                avg_y = (landmarks[8][2] + landmarks[12][2]) / 2.0
            else:
                avg_y = (landmarks[8][1] + landmarks[12][1]) / 2.0

            prev_avg_y = getattr(self, "_prev_scroll_y", avg_y)
            scroll_delta = prev_avg_y - avg_y  # positive = hand moved up = scroll up
            self._prev_scroll_y = avg_y
            return GestureType.SCROLL, {"scroll_delta": scroll_delta, "delta_y": avg_y}

        # Pointer Movement: Only Index finger is extended
        if index == 1 and middle == 0 and ring == 0 and pinky == 0:
            if len(landmarks[8]) == 3:  # [id, x, y] format
                cursor_pt = (landmarks[8][1], landmarks[8][2])
            else:  # [x, y] format
                cursor_pt = (landmarks[8][0], landmarks[8][1])
            return GestureType.MOVE, {"cursor_pt": cursor_pt, "cursor_pos": cursor_pt}

        return GestureType.IDLE, meta
