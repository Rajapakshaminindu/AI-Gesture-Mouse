"""
Gesture Classification Engine and State Machine.

Classifies hand landmark poses into concrete mouse actions according to
the HackX AI Gesture Mouse specification.
Includes:
- Dynamic hand-scale normalization (robust against variable hand-to-camera distances)
- Exponential moving average smoothing for landmark jitter reduction
- Predominantly horizontal swipe vector filtering
- Per-gesture configurable cooldown debouncing
"""

from enum import Enum
from typing import List, Tuple, Dict, Any, Optional
from collections import deque
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
    to classify active gestures with high accuracy, noise suppression, and debounce.
    """

    def __init__(
        self,
        pinch_click_threshold_ratio: float = 0.22,
        drag_hold_duration: float = 0.40,
        click_cooldown: float = 0.35,
        scroll_sensitivity: float = 2.0,
        swipe_velocity_threshold: float = 380.0,
        confidence_threshold: float = 0.75,
        smoothing_factor: float = 0.35,
        cooldowns: Optional[Dict[str, float]] = None
    ):
        self.pinch_threshold_ratio = pinch_click_threshold_ratio
        self.drag_hold_duration = drag_hold_duration
        self.click_cooldown = click_cooldown
        self.scroll_sensitivity = scroll_sensitivity
        self.swipe_velocity_threshold = swipe_velocity_threshold
        self.confidence_threshold = confidence_threshold
        self.smoothing_factor = smoothing_factor

        # Per-gesture configurable cooldown dictionary (in seconds)
        self.cooldowns: Dict[str, float] = {
            GestureType.LEFT_CLICK.value: click_cooldown,
            GestureType.RIGHT_CLICK.value: 0.40,
            GestureType.DOUBLE_CLICK.value: 0.50,
            GestureType.SWIPE_LEFT.value: 0.60,
            GestureType.SWIPE_RIGHT.value: 0.60,
        }
        if cooldowns:
            self.cooldowns.update(cooldowns)

        # Debounce timestamp trackers
        self.last_triggered_time: Dict[str, float] = {}

        # Drag tracking
        self.pinch_start_time: Optional[float] = None
        self.is_dragging: bool = False

        # Jitter smoothing (Exponential Moving Average) for index tip
        self.smoothed_index_pos: Optional[Tuple[float, float]] = None

        # Swipe tracking: stores (timestamp, x, y)
        self.swipe_history: deque = deque(maxlen=10)

    def _euclidean_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate 2D Euclidean distance between two coordinate tuples."""
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _get_hand_scale(self, landmarks: List[List[int]]) -> float:
        """
        Calculates reference hand scale based on distance between Wrist (0) and Middle MCP (9).
        Provides invariant normalization across different camera distances.
        """
        wrist = (float(landmarks[0][0]), float(landmarks[0][1]))
        middle_base = (float(landmarks[9][0]), float(landmarks[9][1]))
        scale = self._euclidean_distance(wrist, middle_base)
        return max(scale, 20.0)  # Avoid division by zero

    def _smooth_point(self, raw_point: Tuple[float, float]) -> Tuple[float, float]:
        """Applies exponential moving average to filter out high-frequency landmark jitter."""
        if self.smoothed_index_pos is None:
            self.smoothed_index_pos = raw_point
            return raw_point

        alpha = self.smoothing_factor
        sx = alpha * raw_point[0] + (1.0 - alpha) * self.smoothed_index_pos[0]
        sy = alpha * raw_point[1] + (1.0 - alpha) * self.smoothed_index_pos[1]
        self.smoothed_index_pos = (sx, sy)
        return (sx, sy)

    def _is_cooling_down(self, gesture: GestureType, now: float) -> bool:
        """Check if gesture is blocked by cooldown."""
        cooldown_period = self.cooldowns.get(gesture.value, 0.0)
        last_time = self.last_triggered_time.get(gesture.value, 0.0)
        return (now - last_time) < cooldown_period

    def _record_trigger(self, gesture: GestureType, now: float) -> None:
        """Record timestamp for cooldown debouncing."""
        self.last_triggered_time[gesture.value] = now

    def _detect_swipe(self, index_pos: Tuple[float, float], now: float) -> Optional[GestureType]:
        """
        Evaluates horizontal swipe velocity and trajectory angle.
        Rejects movements where vertical displacement dominates horizontal displacement.
        """
        self.swipe_history.append((now, index_pos[0], index_pos[1]))

        # Retain history strictly within last 0.22 seconds
        while self.swipe_history and (now - self.swipe_history[0][0]) > 0.22:
            self.swipe_history.popleft()

        if len(self.swipe_history) < 3:
            return None

        dt = self.swipe_history[-1][0] - self.swipe_history[0][0]
        if dt < 0.04:
            return None

        dx = self.swipe_history[-1][1] - self.swipe_history[0][1]
        dy = self.swipe_history[-1][2] - self.swipe_history[0][2]

        # Trajectory check: horizontal motion must dominate vertical motion
        if abs(dx) < 1.4 * abs(dy):
            return None

        velocity_x = dx / dt
        if abs(velocity_x) >= self.swipe_velocity_threshold:
            self.swipe_history.clear()
            return GestureType.SWIPE_LEFT if velocity_x < 0 else GestureType.SWIPE_RIGHT

        return None

    def recognize(
        self,
        fingers: List[int],
        landmarks: List[List[int]],
        confidence: float = 1.0,
        current_time: Optional[float] = None
    ) -> Tuple[GestureType, Dict[str, Any]]:
        """
        Classifies current hand pose and returns (GestureType, metadata).
        """
        now = time.time() if current_time is None else current_time
        meta: Dict[str, Any] = {"confidence": round(confidence, 2)}

        # 1. Confidence validation gate
        if confidence < self.confidence_threshold:
            return GestureType.IDLE, {"status": "low_confidence", "confidence": confidence}

        if not landmarks or len(landmarks) < 21:
            return GestureType.IDLE, {"status": "insufficient_landmarks"}

        hand_scale = self._get_hand_scale(landmarks)
        meta["hand_scale"] = round(hand_scale, 2)

        thumb_tip = (float(landmarks[4][0]), float(landmarks[4][1]))
        raw_index_tip = (float(landmarks[8][0]), float(landmarks[8][1]))
        index_tip = self._smooth_point(raw_index_tip)
        middle_tip = (float(landmarks[12][0]), float(landmarks[12][1]))

        thumb, index, middle, ring, pinky = fingers if len(fingers) == 5 else [0, 0, 0, 0, 0]

        
  # 2. Check for Horizontal Swipe (Only when index finger is solo pointing)
        if index == 1 and middle == 0 and ring == 0 and pinky == 0:
            swipe = self._detect_swipe(index_tip, now)
            if swipe is not None:
                if not self._is_cooling_down(swipe, now):
                    self._record_trigger(swipe, now)
                    return swipe, {"gesture": swipe.value, "status": "triggered"}
                return GestureType.IDLE, {"status": "cooldown_blocked", "gesture": swipe.value}
        # 3. Dynamic Normalized Pinch Distance (Thumb Tip to Index Tip)
        pinch_dist = self._euclidean_distance(thumb_tip, index_tip)
        norm_pinch = pinch_dist / hand_scale
        meta["normalized_pinch"] = round(norm_pinch, 3)
        if norm_pinch < self.pinch_threshold_ratio:
            if self.pinch_start_time is None:
                self.pinch_start_time = now
            hold_time = now - self.pinch_start_time
            meta["pinch_hold_time"] = round(hold_time, 3)
            if hold_time >= self.drag_hold_duration:
                self.is_dragging = True
                return GestureType.DRAG, meta
            return GestureType.IDLE, meta
        else:
            # Pinch released: evaluate if click or drag end
            if self.pinch_start_time is not None:
                hold_time = now - self.pinch_start_time
                self.pinch_start_time = None
                if self.is_dragging:
                    self.is_dragging = False
                    return GestureType.IDLE, {"status": "drag_released"}
                if hold_time < self.drag_hold_duration:
                    if not self._is_cooling_down(GestureType.LEFT_CLICK, now):
                        self._record_trigger(GestureType.LEFT_CLICK, now)
                        return GestureType.LEFT_CLICK, meta


 # 3. Third click after cooldown expires at 1.60 (elapsed 0.50s > 0.40s) -> allowed
    rec.recognize([1, 1, 0, 0, 0], landmarks_pinch, confidence=0.95, current_time=1.55)
    g3, _ = rec.recognize([1, 1, 0, 0, 0], landmarks_release, confidence=0.95, current_time=1.60)
    assert g3 == GestureType.LEFT_CLICK
