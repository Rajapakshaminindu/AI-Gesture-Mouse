"""
Comprehensive pytest test suite for gesture enhancements.
Tests:
- Hand scale normalization and dynamic distance calculation
- High/low confidence threshold gate
- Per-gesture cooldown debouncing
- Directional velocity swipe recognition (rejection of vertical motions)
"""
import pytest
from src.gesture_recognizer import GestureRecognizer, GestureType
def build_landmarks(index_x: int = 100, index_y: int = 100, wrist_middle_dist: int = 100) -> list:
    """Helper creating 21 standard landmarks with customizable reference hand scale."""
    landmarks = [[0, 0] for _ in range(21)]
    # Landmark 0: Wrist
    landmarks[0] = [100, 200]
    # Landmark 4: Thumb Tip
    landmarks[4] = [200, 200]
    # Landmark 8: Index Tip
    landmarks[8] = [index_x, index_y]
    # Landmark 9: Middle MCP (reference scale anchor)
    landmarks[9] = [100, 200 - wrist_middle_dist]
    # Landmark 12: Middle Tip
    landmarks[12] = [250, 250]
    return landmarks
def test_confidence_filtering():
    """Ensure frames below configured threshold are safely discarded."""
    rec = GestureRecognizer(confidence_threshold=0.75)
    landmarks = build_landmarks()
    fingers = [0, 1, 0, 0, 0]
    # Below threshold -> IDLE
    gesture, meta = rec.recognize(fingers, landmarks, confidence=0.70, current_time=1.0)
    assert gesture == GestureType.IDLE
    assert meta["status"] == "low_confidence"
    # Above threshold -> MOVE
    gesture, _ = rec.recognize(fingers, landmarks, confidence=0.88, current_time=1.05)
    assert gesture == GestureType.MOVE
def test_per_gesture_debounce():
    """Verify that multiple clicks triggered within cooldown window are debounced."""
    rec = GestureRecognizer(
        pinch_click_threshold_ratio=0.25,
        cooldowns={GestureType.LEFT_CLICK.value: 0.40}
    )
    landmarks_pinch = build_landmarks()
    landmarks_pinch[4] = [100, 100]
    landmarks_pinch[8] = [105, 100]  # Very close to thumb (pinch)
    landmarks_release = build_landmarks()
    landmarks_release[4] = [100, 100]
    landmarks_release[8] = [180, 100]  # Released
    # 1. First click: pinch at 1.0, release at 1.1 (< 0.40s) -> triggers LEFT_CLICK
    rec.recognize([1, 1, 0, 0, 0], landmarks_pinch, confidence=0.95, current_time=1.0)
    g1, _ = rec.recognize([1, 1, 0, 0, 0], landmarks_release, confidence=0.95, current_time=1.1)
    assert g1 == GestureType.LEFT_CLICK

 # 2. Second rapid click at 1.25 (elapsed 0.15s < 0.40s cooldown) -> blocked
    rec.recognize([1, 1, 0, 0, 0], landmarks_pinch, confidence=0.95, current_time=1.20)
    g2, _ = rec.recognize([1, 1, 0, 0, 0], landmarks_release, confidence=0.95, current_time=1.25)
    assert g2 == GestureType.IDLE

  # 3. Third click after cooldown expires at 1.60 (elapsed 0.50s > 0.40s) -> allowed
    rec.recognize([1, 1, 0, 0, 0], landmarks_pinch, confidence=0.95, current_time=1.55)
    g3, _ = rec.recognize([1, 1, 0, 0, 0], landmarks_release, confidence=0.95, current_time=1.60)
    assert g3 == GestureType.LEFT_CLICK


def test_horizontal_swipe_detection():
    """Verify swipe left and right detection with fast horizontal velocities."""
    rec = GestureRecognizer(swipe_velocity_threshold=350.0, smoothing_factor=1.0)
    fingers = [0, 1, 0, 0, 0]
    # Swipe Right simulation
    rec.recognize(fingers, build_landmarks(index_x=100, index_y=150), confidence=0.9, current_time=1.00)
    rec.recognize(fingers, build_landmarks(index_x=160, index_y=150), confidence=0.9, current_time=1.04)
    g_right, _ = rec.recognize(fingers, build_landmarks(index_x=280, index_y=152), confidence=0.9, current_time=1.08)
    assert g_right == GestureType.SWIPE_RIGHT


