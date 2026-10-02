"""
Unit tests for gesture enhancements:
- Horizontal swipe detection (left & right)
- Per-gesture debounce cooldowns
- Detection confidence threshold filtering
"""

import pytest
from src.gesture_recognizer import GestureRecognizer, GestureType


def create_mock_landmarks(index_x: int = 100, index_y: int = 100) -> list:
    """Helper to generate a 21-landmark list with index fingertip at (index_x, index_y)."""
    landmarks = [[0, 0] for _ in range(21)]
    # Landmark 4: Thumb tip
    landmarks[4] = [200, 200]
    # Landmark 8: Index tip
    landmarks[8] = [index_x, index_y]
    # Landmark 12: Middle tip
    landmarks[12] = [300, 300]
    return landmarks


def test_confidence_threshold_filtering():
    """Verify that frames below the confidence threshold return IDLE immediately."""
    recognizer = GestureRecognizer(confidence_threshold=0.75)
    landmarks = create_mock_landmarks()
    fingers = [0, 1, 0, 0, 0]

    # Frame with low confidence (0.60 < 0.75)
    gesture, meta = recognizer.recognize(
        fingers=fingers,
        landmarks=landmarks,
        confidence=0.60,
        current_time=1.0
    )
    assert gesture == GestureType.IDLE
    assert meta["status"] == "low_confidence"

    # Frame with acceptable confidence (0.85 >= 0.75)
    gesture, meta = recognizer.recognize(
        fingers=fingers,
        landmarks=landmarks,
        confidence=0.85,
        current_time=1.1
    )
    assert gesture == GestureType.MOVE


def test_per_gesture_debounce_cooldown():
    """Verify that repetitive triggers within the cooldown period are blocked."""
    custom_cooldowns = {
        GestureType.LEFT_CLICK.value: 0.50,
        GestureType.RIGHT_CLICK.value: 0.40
    }
    recognizer = GestureRecognizer(cooldowns=custom_cooldowns)
    landmarks = create_mock_landmarks()
    landmarks[4] = [100, 100]  # Pinch thumb & index together
    landmarks[8] = [100, 100]

    # 1. Start pinch at t = 1.0
    recognizer.recognize([1, 1, 0, 0, 0], landmarks, confidence=0.9, current_time=1.0)
    # Release pinch at t = 1.1 (< 0.45s hold -> Left Click)
    landmarks_released = create_mock_landmarks()
    landmarks_released[4] = [150, 150]
    gesture, _ = recognizer.recognize([1, 1, 0, 0, 0], landmarks_released, confidence=0.9, current_time=1.1)
    assert gesture == GestureType.LEFT_CLICK

    # 2. Immediate second pinch release at t = 1.25 (elapsed 0.15s < 0.50s cooldown)
    recognizer.recognize([1, 1, 0, 0, 0], landmarks, confidence=0.9, current_time=1.20)
    gesture_repeat, _ = recognizer.recognize([1, 1, 0, 0, 0], landmarks_released, confidence=0.9, current_time=1.25)
    assert gesture_repeat == GestureType.IDLE  # Blocked by debounce cooldown

    # 3. Third pinch release after cooldown at t = 1.70 (elapsed 0.60s > 0.50s)
    recognizer.recognize([1, 1, 0, 0, 0], landmarks, confidence=0.9, current_time=1.65)
    gesture_after_cooldown, _ = recognizer.recognize([1, 1, 0, 0, 0], landmarks_released, confidence=0.9, current_time=1.70)
    assert gesture_after_cooldown == GestureType.LEFT_CLICK


def test_swipe_left_detection():
    """Verify that rapid leftward horizontal movement triggers SWIPE_LEFT."""
    recognizer = GestureRecognizer(swipe_velocity_threshold=300.0)
    fingers = [0, 1, 0, 0, 0]  # Only index finger up

    # Point 1: x = 400 at t = 1.0
    recognizer.recognize(fingers, create_mock_landmarks(index_x=400), confidence=0.9, current_time=1.0)

    # Point 2: x = 200 at t = 1.1 (moved left by 200px in 0.1s -> velocity = -2000px/s)
    gesture, _ = recognizer.recognize(
        fingers,
        create_mock_landmarks(index_x=200),
        confidence=0.9,
        current_time=1.1
    )
    assert gesture == GestureType.SWIPE_LEFT


def test_swipe_right_detection():
    """Verify that rapid rightward horizontal movement triggers SWIPE_RIGHT."""
    recognizer = GestureRecognizer(swipe_velocity_threshold=300.0)
    fingers = [0, 1, 0, 0, 0]  # Only index finger up

    # Point 1: x = 100 at t = 1.0
    recognizer.recognize(fingers, create_mock_landmarks(index_x=100), confidence=0.9, current_time=1.0)

    # Point 2: x = 300 at t = 1.1 (moved right by 200px in 0.1s -> velocity = +2000px/s)
    gesture, _ = recognizer.recognize(
        fingers,
        create_mock_landmarks(index_x=300),
        confidence=0.9,
        current_time=1.1
    )
    assert gesture == GestureType.SWIPE_RIGHT
