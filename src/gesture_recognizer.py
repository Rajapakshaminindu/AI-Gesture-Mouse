"""
Gesture Classification Engine and State Machine — Enhanced Edition.

Gesture Map:
  ☝️  Index only              → MOVE cursor
  🤏  Pinch (thumb+index)     → LEFT CLICK (quick) / DRAG (hold)
  🖐️  All 5 fingers, PALM     → RIGHT CLICK  (front-of-hand facing camera)
  🖐️  All 5 fingers, BACK     → DOUBLE CLICK (back-of-hand facing camera)
  ✌️  Index + middle, ring    → SCROLL (vertical hand movement)
       curled (direct geometry)
  ✊  Fist                    → IDLE

Scroll detection uses direct landmark Y comparison (ring tip vs ring MCP)
instead of the binary fingers_up result, which is unreliable when the ring
finger is partially raised. This makes peace-sign detection robust.

Includes per-gesture cooldown debounce, temporal drag state tracking,
velocity-based swipe detection, multi-frame confirmation buffer, and
a scroll-transition guard that prevents window-minimize accidents.
"""

from enum import Enum
from typing import List, Tuple, Dict, Any, Optional
import time
import math
import collections


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
    Evaluates finger configuration, palm orientation, distance metrics,
    and temporal dynamics to classify gestures.
    """

    def __init__(
        self,
        pinch_click_threshold: float = 48.0,
        drag_hold_duration: float = 0.40,
        click_cooldown: float = 0.22,
        scroll_sensitivity: float = 2.0,
        swipe_velocity_threshold: float = 380.0,
        confidence_threshold: float = 0.70,
        cooldowns: Optional[Dict[str, float]] = None,
        confirm_frames: int = 2
    ):
        self.pinch_click_threshold = pinch_click_threshold
        self.drag_hold_duration = drag_hold_duration
        self.click_cooldown = click_cooldown
        self.scroll_sensitivity = scroll_sensitivity
        self.swipe_velocity_threshold = swipe_velocity_threshold
        self.confidence_threshold = confidence_threshold
        self.confirm_frames = confirm_frames

        self.cooldowns: Dict[str, float] = {
            GestureType.LEFT_CLICK.value:   click_cooldown,
            GestureType.RIGHT_CLICK.value:  0.45,
            GestureType.DOUBLE_CLICK.value: 0.60,
            GestureType.SWIPE_LEFT.value:   0.55,
            GestureType.SWIPE_RIGHT.value:  0.55,
        }
        if cooldowns:
            self.cooldowns.update(cooldowns)

        self.last_triggered_time: Dict[str, float] = {}

        # Drag state
        self.pinch_start_time: Optional[float] = None
        self.is_dragging: bool = False

        # Swipe tracking
        self.swipe_history: List[Tuple[float, float]] = []

        # Multi-frame confirmation buffer (requires confirm_frames consecutive frames)
        self._gesture_buffer: collections.deque = collections.deque(maxlen=confirm_frames)

        # Orientation buffer (3 frames = ~100ms, enough for stable reads)
        self._z_orientation_buffer: collections.deque = collections.deque(maxlen=3)

        # ── Scroll state ────────────────────────────────────────────────────────
        self._scroll_accumulator: float = 0.0
        self._was_scrolling: bool = False   # True while in scroll mode
        self._prev_scroll_y: float = 0.0   # previous avg_y for delta calculation

        # ── Scroll transition guard ─────────────────────────────────────────────
        self._last_scroll_time: float = 0.0
        self._scroll_guard_duration: float = 0.80

        # Mutual click lockout: prevents Left Click and Right Click from firing together
        self._last_any_click_time: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    #  Utility helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _euclidean_distance(self, p1: List[int], p2: List[int]) -> float:
        if len(p1) == 3:
            return math.hypot(p1[1] - p2[1], p1[2] - p2[2])
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _is_cooling_down(self, gesture: GestureType, now: float) -> bool:
        cooldown_period = self.cooldowns.get(gesture.value, 0.0)
        last_time = self.last_triggered_time.get(gesture.value, 0.0)
        return (now - last_time) < cooldown_period

    def _record_trigger(self, gesture: GestureType, now: float) -> None:
        self.last_triggered_time[gesture.value] = now

    def _confirm(self, candidate: str) -> bool:
        """Returns True if candidate fills the entire confirmation buffer."""
        self._gesture_buffer.append(candidate)
        if len(self._gesture_buffer) < self._gesture_buffer.maxlen:
            return False
        return all(g == candidate for g in self._gesture_buffer)

    def _clear_buffer(self) -> None:
        self._gesture_buffer.clear()

    def _lm_y(self, landmarks: List[List[int]], idx: int) -> float:
        """Extract Y pixel coordinate from a landmark (handles both [x,y] and [id,x,y])."""
        pt = landmarks[idx]
        return float(pt[2] if len(pt) == 3 else pt[1])

    # ─────────────────────────────────────────────────────────────────────────
    #  Palm orientation detection
    # ─────────────────────────────────────────────────────────────────────────

    def _get_palm_orientation(self, landmarks: List[List[int]], handedness: str = "Right") -> str:
        """
        Detects whether the palm or back of hand faces the camera.
        Uses the 2D cross-product of wrist→index_mcp and wrist→pinky_mcp vectors,
        plus thumb vs pinky relative horizontal order.
        Returns: "PALM" | "BACK" | "UNKNOWN"
        """
        if not landmarks or len(landmarks) < 21:
            return "UNKNOWN"
        try:
            def lm(idx):
                pt = landmarks[idx]
                if len(pt) == 3:
                    return float(pt[1]), float(pt[2])
                return float(pt[0]), float(pt[1])

            wx, wy = lm(0)
            ix, iy = lm(5)
            px, py = lm(17)

            v1x, v1y = ix - wx, iy - wy
            v2x, v2y = px - wx, py - wy
            cross_z = v1x * v2y - v1y * v2x

            self._z_orientation_buffer.append(cross_z)
            smoothed = sum(self._z_orientation_buffer) / len(self._z_orientation_buffer)

            if abs(smoothed) < 200:
                return "UNKNOWN"

            # In mirrored webcam mode (standard in webcams):
            # For Right Hand:
            #   Palm facing camera -> Thumb is on left, index is left of pinky -> cross_z > 0
            #   Back facing camera -> Thumb is on right, index is right of pinky -> cross_z < 0
            # For Left Hand:
            #   Opposite signs
            if handedness != "Left":
                return "PALM" if smoothed > 0 else "BACK"
            else:
                return "PALM" if smoothed < 0 else "BACK"

        except Exception:
            return "UNKNOWN"

    # ─────────────────────────────────────────────────────────────────────────
    #  Swipe detection
    # ─────────────────────────────────────────────────────────────────────────

    def _detect_swipe(self, index_tip: List[int], now: float) -> Optional[GestureType]:
        tip_x = float(index_tip[1]) if len(index_tip) == 3 else float(index_tip[0])
        self.swipe_history.append((now, tip_x))
        self.swipe_history = [(t, x) for t, x in self.swipe_history if (now - t) <= 0.25]

        if len(self.swipe_history) < 2:
            return None

        dt = self.swipe_history[-1][0] - self.swipe_history[0][0]
        if dt < 0.05:
            return None

        dx = self.swipe_history[-1][1] - self.swipe_history[0][1]
        velocity = dx / dt

        if abs(velocity) >= self.swipe_velocity_threshold:
            self.swipe_history.clear()
            if velocity < -self.swipe_velocity_threshold:
                return GestureType.SWIPE_LEFT
            elif velocity > self.swipe_velocity_threshold:
                return GestureType.SWIPE_RIGHT
        return None

    # ─────────────────────────────────────────────────────────────────────────
    #  Ring-finger-curled check (landmark geometry)
    # ─────────────────────────────────────────────────────────────────────────

    def _ring_is_curled(self, landmarks: List[List[int]], ring_binary: int) -> bool:
        """
        Returns True if the ring finger is clearly curled (not extended).

        Uses direct landmark Y comparison:
          ring tip Y > ring MCP Y  →  tip is BELOW the knuckle base → curled

        This is far more reliable than the binary fingers_up result, which
        flickers when the ring finger is only partially raised. A small margin
        of -5 pixels means the ring finger must be noticeably curled before
        scroll mode is blocked.
        """
        try:
            slot = 2 if len(landmarks[13]) == 3 else 1
            ring_mcp_y = landmarks[13][slot]   # ring MCP (base knuckle)
            ring_tip_y = landmarks[16][slot]   # ring tip
            # Y increases downward. Tip below MCP = curled.
            return ring_tip_y > (ring_mcp_y - 5)
        except (IndexError, TypeError):
            return ring_binary == 0   # safe fallback

    # ─────────────────────────────────────────────────────────────────────────
    #  Index Finger Bend / Tap detection (for natural mouse click)
    # ─────────────────────────────────────────────────────────────────────────

    def _is_index_finger_bent(self, landmarks: List[List[int]]) -> bool:
        """
        Determines if the index finger is bent/tapped downward (like clicking a mouse button).
        Uses a scale-invariant ratio of tip-to-MCP distance over PIP-to-MCP distance,
        and vertical tip-vs-PIP comparison.
        """
        if not landmarks or len(landmarks) < 21:
            return False
        try:
            def pt(idx):
                p = landmarks[idx]
                return (float(p[1]), float(p[2])) if len(p) == 3 else (float(p[0]), float(p[1]))

            p5 = pt(5)  # INDEX_MCP
            p6 = pt(6)  # INDEX_PIP
            p8 = pt(8)  # INDEX_TIP

            d_tip_mcp = math.hypot(p8[0] - p5[0], p8[1] - p5[1])
            d_pip_mcp = math.hypot(p6[0] - p5[0], p6[1] - p5[1])

            if d_pip_mcp < 1.0:
                return False

            ratio = d_tip_mcp / d_pip_mcp
            # Extended straight index finger: ratio is ~2.2 - 2.8
            # Bent index finger (air click): ratio drops < 1.30
            y_bent = (p8[1] >= p6[1] - 8)

            return (ratio < 1.30) or y_bent
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────────
    #  Main recognition entry point
    # ─────────────────────────────────────────────────────────────────────────

    def recognize(
        self,
        fingers: List[int],
        landmarks: List[List[int]],
        confidence: float = 1.0,
        current_time: Optional[float] = None,
        handedness: str = "Right"
    ) -> Tuple[GestureType, Dict[str, Any]]:
        """
        Classifies current gesture from finger flags [thumb, index, middle, ring, pinky]
        and raw 21 landmark positions.
        """
        now = time.time() if current_time is None else current_time
        meta: Dict[str, Any] = {"confidence": confidence}

        if confidence < self.confidence_threshold:
            return GestureType.IDLE, {"status": "low_confidence", "confidence": confidence}

        if not landmarks or len(landmarks) < 21:
            return GestureType.IDLE, {"status": "insufficient_landmarks"}

        thumb, index, middle, ring, pinky = fingers if len(fingers) == 5 else [0, 0, 0, 0, 0]

        # ── 1. SWIPE — index only, fast horizontal movement ────────────────────
        if index == 1 and middle == 0 and ring == 0 and pinky == 0:
            swipe = self._detect_swipe(landmarks[8], now)
            if swipe is not None:
                if not self._is_cooling_down(swipe, now):
                    self._record_trigger(swipe, now)
                    self._clear_buffer()
                    self._was_scrolling = False
                    return swipe, {"velocity": swipe.value}
                return GestureType.IDLE, {"status": "cooldown_blocked"}

        # ── 2. LEFT CLICK / DRAG — Index Finger Bend / Tap (or Pinch) ─────────
        pinch_dist = self._euclidean_distance(landmarks[4], landmarks[8])
        meta["pinch_distance"] = pinch_dist

        # Check if index finger is bent/tapped downward
        index_bent = self._is_index_finger_bent(landmarks)
        meta["index_bent"] = index_bent

        # If hand has ring or pinky raised, or is opening into an open hand pose,
        # it CANNOT be a click. Cancel any pending press immediately.
        if ring == 1 or pinky == 1 or (middle == 1 and ring == 1):
            self.pinch_start_time = None
            self.is_dragging = False

        # Left click press triggers if user is in pointing mode (ring & pinky down)
        # and EITHER bends index finger down OR pinches thumb & index
        is_pressing = False
        if ring == 0 and pinky == 0:
            if index_bent or (pinch_dist < self.pinch_click_threshold):
                is_pressing = True

        if is_pressing:
            self._clear_buffer()
            self._was_scrolling = False
            if self.pinch_start_time is None:
                self.pinch_start_time = now
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
            if self.pinch_start_time is not None:
                hold_duration = now - self.pinch_start_time
                self.pinch_start_time = None

                if self.is_dragging:
                    self.is_dragging = False
                    return GestureType.IDLE, {"status": "drag_released"}

                # Trigger left click on release (unbend / unpinch) while ring and pinky stay down
                if hold_duration < self.drag_hold_duration and ring == 0 and pinky == 0:
                    if not self._is_cooling_down(GestureType.LEFT_CLICK, now) and (now - self._last_any_click_time) >= 0.35:
                        self._record_trigger(GestureType.LEFT_CLICK, now)
                        self._last_any_click_time = now
                        return GestureType.LEFT_CLICK, meta
                    return GestureType.IDLE, {"status": "cooldown_blocked"}

        # ── 3. THREE-FINGER RIGHT CLICK (index + middle + ring UP, pinky DOWN) ──
        if index == 1 and middle == 1 and ring == 1 and pinky == 0:
            self.pinch_start_time = None
            if not self._is_cooling_down(GestureType.RIGHT_CLICK, now) and (now - self._last_any_click_time) >= 0.35:
                self._record_trigger(GestureType.RIGHT_CLICK, now)
                self._last_any_click_time = now
                self._clear_buffer()
                self._was_scrolling = False
                return GestureType.RIGHT_CLICK, meta
            return GestureType.IDLE, {"status": "cooldown_blocked"}

        # ── 4. ALL 5 FINGERS — Right Click (PALM) or Double Click (BACK) ────────
        # Guarded: blocked for 0.80s after scroll ends to prevent uncurling fingers
        # from accidentally firing double click (which could minimize windows).
        all_five_up = (thumb == 1 and index == 1 and middle == 1
                       and ring == 1 and pinky == 1)
        scroll_just_ended = (now - self._last_scroll_time) < self._scroll_guard_duration

        if all_five_up and not scroll_just_ended:
            self.pinch_start_time = None
            self._was_scrolling = False
            orientation = self._get_palm_orientation(landmarks, handedness=handedness)
            meta["palm_orientation"] = orientation

            if orientation == "PALM":
                if self._confirm("RIGHT_CLICK"):
                    if not self._is_cooling_down(GestureType.RIGHT_CLICK, now) and (now - self._last_any_click_time) >= 0.35:
                        self._record_trigger(GestureType.RIGHT_CLICK, now)
                        self._last_any_click_time = now
                        self._clear_buffer()
                        return GestureType.RIGHT_CLICK, meta
                return GestureType.IDLE, {"status": "confirming_right_click", **meta}

            elif orientation == "BACK":
                if self._confirm("DOUBLE_CLICK"):
                    if not self._is_cooling_down(GestureType.DOUBLE_CLICK, now) and (now - self._last_any_click_time) >= 0.35:
                        self._record_trigger(GestureType.DOUBLE_CLICK, now)
                        self._last_any_click_time = now
                        self._clear_buffer()
                        return GestureType.DOUBLE_CLICK, meta
                return GestureType.IDLE, {"status": "confirming_double_click", **meta}

            else:
                self._confirm("UNKNOWN_FIVE")
                return GestureType.IDLE, {"status": "orientation_unknown", **meta}

        # ── 5. SCROLL — Two fingers up (Index + Middle, Ring & Pinky down) ─────
        # Natural & comfortable: user holds up Index and Middle (like trackpad 2-finger scroll).
        # Ring and Pinky MUST be DOWN so it never conflicts with 3-finger or 5-finger gestures.
        if index == 1 and middle == 1 and ring == 0 and pinky == 0:
            self._clear_buffer()
            self._last_scroll_time = now   # refresh guard every scroll frame

            slot = 2 if len(landmarks[8]) == 3 else 1
            avg_y = (landmarks[8][slot] + landmarks[12][slot]) / 2.0

            # Fresh entry: reset anchor and accumulator
            if not self._was_scrolling:
                self._prev_scroll_y = avg_y
                self._scroll_anchor_y = avg_y
                self._scroll_accumulator = 0.0
                self._was_scrolling = True
                return GestureType.SCROLL, {"scroll_delta": 0, "delta_y": avg_y, "scroll_mode": "START"}

            raw_delta = self._prev_scroll_y - avg_y   # +ve = up, -ve = down
            self._prev_scroll_y = avg_y

            # Dual Scroll Engine:
            # 1. Flick motion (direct dynamic hand movement)
            self._scroll_accumulator += (raw_delta / 6.0) * (self.scroll_sensitivity / 2.0)
            self._scroll_accumulator = max(-6.0, min(6.0, self._scroll_accumulator))

            flick_tick = int(self._scroll_accumulator)
            if flick_tick != 0:
                self._scroll_accumulator -= flick_tick
                flick_tick = max(-4, min(4, flick_tick))

            # 2. Continuous Anchor Tilt Glide:
            # If user holds fingers slightly above or below starting point,
            # glide continuously without needing to repeatedly wave arm!
            anchor_offset = getattr(self, "_scroll_anchor_y", avg_y) - avg_y
            glide_tick = 0
            if abs(anchor_offset) > 30:
                direction = 1 if anchor_offset > 0 else -1
                glide_speed = min(3.0, (abs(anchor_offset) - 30) / 25.0)
                glide_tick = int(direction * max(1.0, glide_speed))

            # Prioritize active flick, otherwise continuous glide
            total_tick = flick_tick if flick_tick != 0 else glide_tick
            total_tick = max(-4, min(4, total_tick))

            return GestureType.SCROLL, {
                "scroll_delta": total_tick,
                "delta_y": avg_y,
                "anchor_offset": anchor_offset,
                "scroll_mode": "UP" if total_tick > 0 else ("DOWN" if total_tick < 0 else "HOLD")
            }

        # Not in scroll this frame — clear entry flag
        self._was_scrolling = False

        # ── 6. MOVE — only index finger extended ───────────────────────────────
        if index == 1 and middle == 0 and ring == 0 and pinky == 0:
            self._clear_buffer()
            if len(landmarks[8]) == 3:
                cursor_pt = (landmarks[8][1], landmarks[8][2])
            else:
                cursor_pt = (landmarks[8][0], landmarks[8][1])
            return GestureType.MOVE, {"cursor_pt": cursor_pt, "cursor_pos": cursor_pt}

        # ── 7. IDLE / unrecognised pose ─────────────────────────────────────────
        self._clear_buffer()
        return GestureType.IDLE, meta
