"""
Gesture Classification Engine and State Machine — Enhanced Edition.

Gesture Map:
  ☝️  Index only                      → MOVE cursor
  ✌️  2 fingers (Index + Middle)      → LEFT CLICK (one-shot latched)
  👍  Thumbs Up                       → RIGHT CLICK
  🖐️  All 5 fingers, BACK             → DOUBLE CLICK (back-of-hand facing camera)
  3️⃣  3 fingers (Index + Mid + Ring)  → SCROLL (vertical hand movement)
  Neutral / unrecognised              → IDLE (no interaction)

Includes per-gesture cooldown debounce, temporal state latching,
velocity-based swipe detection, multi-frame confirmation buffer, and
a scroll-transition guard that prevents accidental clicks.
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
        min_click_duration: float = 0.05,
        click_cooldown: float = 0.22,
        scroll_sensitivity: float = 2.0,
        swipe_velocity_threshold: float = 380.0,
        confidence_threshold: float = 0.70,
        cooldowns: Optional[Dict[str, float]] = None,
        confirm_frames: int = 2
    ):
        self.pinch_click_threshold = pinch_click_threshold
        self.drag_hold_duration = drag_hold_duration
        self.min_click_duration = min_click_duration
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

        # ── Two-finger one-shot click latch & transition debounce ──────────────
        self._two_finger_click_fired: bool = False
        self._two_finger_start_time: Optional[float] = None
        self._two_finger_confirm_duration: float = 0.030  # 30ms: balanced fast click response

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
    #  Thumbs Up detection (for right click)
    # ─────────────────────────────────────────────────────────────────────────

    def _is_thumbs_up(self, landmarks: List[List[int]], fingers: List[int]) -> bool:
        """
        Returns True if the hand is making a clean thumbs-up gesture.

        Geometry rules:
          1. Hand must NOT be pinching: thumb tip and index tip must be well separated.
          2. Thumb tip must be clearly ABOVE the wrist and above thumb MCP (pointing straight up).
          3. Thumb tip must be significantly higher (smaller Y) than index tip and all other fingers.
          4. All four non-thumb fingers (index, middle, ring, pinky) must be curled into a fist.
        """
        if not landmarks or len(landmarks) < 21:
            return False
        try:
            slot = 2 if len(landmarks[0]) == 3 else 1  # Y-coordinate index

            wrist_y     = float(landmarks[0][slot])   # lm 0  = WRIST
            thumb_mcp_y = float(landmarks[2][slot])   # lm 2  = THUMB_MCP
            thumb_tip_y = float(landmarks[4][slot])   # lm 4  = THUMB_TIP
            index_tip_y = float(landmarks[8][slot])   # lm 8  = INDEX_TIP

            # 1. Pinch guard: if thumb and index tips are close, it is a PINCH, NEVER a thumbs-up!
            pinch_dist = self._euclidean_distance(landmarks[4], landmarks[8])
            if pinch_dist < (self.pinch_click_threshold + 15.0):
                return False

            # 2. Thumb tip must be clearly above the wrist (Y decreases upward)
            if not (wrist_y - thumb_tip_y > 35):
                return False

            # 3. Thumb tip must be above the thumb MCP (thumb extended upward)
            if not (thumb_tip_y < thumb_mcp_y - 10):
                return False

            # 4. In a thumbs-up, thumb tip is high above the curled index finger
            if not (thumb_tip_y < index_tip_y - 25):
                return False

            # 5. Non-thumb fingers must be curled: tip Y >= PIP Y
            # Pairs: (tip_lm, pip_lm) for index, middle, ring, pinky
            curl_pairs = [(8, 6), (12, 10), (16, 14), (20, 18)]
            for tip_idx, pip_idx in curl_pairs:
                tip_y = float(landmarks[tip_idx][slot])
                pip_y = float(landmarks[pip_idx][slot])
                # Tip must be AT or BELOW the PIP joint (curled down)
                if tip_y < pip_y - 8:
                    return False

            return True
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────────
    #  Multi-finger helpers (2-finger click & 3-finger scroll)
    # ─────────────────────────────────────────────────────────────────────────

    def _is_three_fingers(self, landmarks: List[List[int]], fingers: List[int]) -> bool:
        """Returns True if index, middle, and ring are extended, and pinky is curled down."""
        if not landmarks or len(landmarks) < 21:
            return False
        thumb, index, middle, ring, pinky = fingers if len(fingers) == 5 else [0, 0, 0, 0, 0]
        if index == 1 and middle == 1 and ring == 1 and pinky == 0:
            return True
        try:
            slot = 2 if len(landmarks[0]) == 3 else 1
            # Index, Middle, Ring tips must be above their PIP joints
            idx_up = float(landmarks[8][slot]) < float(landmarks[6][slot])
            mid_up = float(landmarks[12][slot]) < float(landmarks[10][slot])
            rng_up = float(landmarks[16][slot]) < float(landmarks[14][slot])
            pky_dn = float(landmarks[20][slot]) >= float(landmarks[18][slot]) - 10
            return idx_up and mid_up and rng_up and pky_dn
        except Exception:
            return False

    def _is_two_fingers(self, landmarks: List[List[int]], fingers: List[int]) -> bool:
        """Returns True if only index and middle are extended, and ring and pinky are curled down."""
        if not landmarks or len(landmarks) < 21:
            return False
        thumb, index, middle, ring, pinky = fingers if len(fingers) == 5 else [0, 0, 0, 0, 0]
        if index == 1 and middle == 1 and ring == 0 and pinky == 0:
            return True
        try:
            slot = 2 if len(landmarks[0]) == 3 else 1
            idx_up = float(landmarks[8][slot]) < float(landmarks[6][slot])
            mid_up = float(landmarks[12][slot]) < float(landmarks[10][slot])
            rng_dn = float(landmarks[16][slot]) >= float(landmarks[14][slot]) - 6
            pky_dn = float(landmarks[20][slot]) >= float(landmarks[18][slot]) - 6
            return idx_up and mid_up and rng_dn and pky_dn
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

        # ── 2. THUMBS UP RIGHT CLICK ──────────────────────────────────────────
        if self._is_thumbs_up(landmarks, fingers):
            self._two_finger_click_fired = False
            if self._confirm("RIGHT_CLICK"):
                if not self._is_cooling_down(GestureType.RIGHT_CLICK, now) and (now - self._last_any_click_time) >= 0.35:
                    self._record_trigger(GestureType.RIGHT_CLICK, now)
                    self._last_any_click_time = now
                    self._clear_buffer()
                    self._was_scrolling = False
                    return GestureType.RIGHT_CLICK, meta
                return GestureType.IDLE, {"status": "cooldown_blocked"}
            return GestureType.IDLE, {"status": "confirming_right_click", **meta}

        # ── 3. ALL 5 FINGERS — Double Click (BACK of hand only) ─────────────────
        all_five_up = (thumb == 1 and index == 1 and middle == 1
                       and ring == 1 and pinky == 1)
        scroll_just_ended = (now - self._last_scroll_time) < self._scroll_guard_duration

        if all_five_up and not scroll_just_ended:
            self._two_finger_click_fired = False
            self._was_scrolling = False
            orientation = self._get_palm_orientation(landmarks, handedness=handedness)
            meta["palm_orientation"] = orientation

            if orientation == "BACK":
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

        # ── 4. SCROLL — Three fingers up (Index + Middle + Ring, Pinky down) ──
        if self._is_three_fingers(landmarks, fingers):
            self._clear_buffer()
            self._two_finger_start_time = None
            self._two_finger_click_fired = False
            self._last_scroll_time = now

            slot = 2 if len(landmarks[8]) == 3 else 1
            avg_y = (landmarks[8][slot] + landmarks[12][slot] + landmarks[16][slot]) / 3.0

            if not self._was_scrolling:
                self._prev_scroll_y = avg_y
                self._scroll_anchor_y = avg_y
                self._scroll_accumulator = 0.0
                self._was_scrolling = True
                return GestureType.SCROLL, {"scroll_delta": 0, "delta_y": avg_y, "scroll_mode": "START"}

            raw_delta = self._prev_scroll_y - avg_y
            self._prev_scroll_y = avg_y

            self._scroll_accumulator += (raw_delta / 5.0) * (self.scroll_sensitivity / 2.0)
            self._scroll_accumulator = max(-6.0, min(6.0, self._scroll_accumulator))

            flick_tick = int(self._scroll_accumulator)
            if flick_tick != 0:
                self._scroll_accumulator -= flick_tick
                flick_tick = max(-4, min(4, flick_tick))

            anchor_offset = getattr(self, "_scroll_anchor_y", avg_y) - avg_y
            glide_tick = 0
            if abs(anchor_offset) > 28:
                direction = 1 if anchor_offset > 0 else -1
                glide_speed = min(3.0, (abs(anchor_offset) - 28) / 22.0)
                glide_tick = int(direction * max(1.0, glide_speed))

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

        # ── 5. TWO FINGERS (INDEX + MIDDLE) — ONE-SHOT LEFT CLICK ─────────────
        # Guarded against scroll transitions (blocked for 0.40s after scroll ends)
        # and requires 70ms stable hold so raising 3 fingers quickly never misfires a click.
        scroll_recently_active = (now - self._last_scroll_time) < 0.40
        is_two_fingers = self._is_two_fingers(landmarks, fingers) and not scroll_recently_active

        if is_two_fingers:
            self._clear_buffer()
            if not self._two_finger_click_fired:
                if self._two_finger_start_time is None:
                    self._two_finger_start_time = now

                hold_time = now - self._two_finger_start_time
                if hold_time >= self._two_finger_confirm_duration:
                    if not self._is_cooling_down(GestureType.LEFT_CLICK, now) and (now - self._last_any_click_time) >= 0.20:
                        self._record_trigger(GestureType.LEFT_CLICK, now)
                        self._last_any_click_time = now
                        self._two_finger_click_fired = True
                        self._two_finger_start_time = None
                        return GestureType.LEFT_CLICK, {"status": "two_finger_click"}
                    return GestureType.IDLE, {"status": "cooldown_blocked"}
                else:
                    return GestureType.IDLE, {"status": "two_finger_confirming"}
            else:
                return GestureType.IDLE, {"status": "two_finger_held"}
        else:
            self._two_finger_start_time = None
            self._two_finger_click_fired = False

        # ── 6. MOVE — only index finger extended ───────────────────────────────
        if index == 1 and middle == 0 and ring == 0 and pinky == 0:
            self._clear_buffer()
            if len(landmarks[8]) == 3:
                cursor_pt = (landmarks[8][1], landmarks[8][2])
            else:
                cursor_pt = (landmarks[8][0], landmarks[8][1])
            return GestureType.MOVE, {"cursor_pt": cursor_pt, "cursor_pos": cursor_pt}

        # ── 7. Neutral / unrecognised pose (no action) ─────────────────────────
        self._clear_buffer()
        return GestureType.IDLE, meta

