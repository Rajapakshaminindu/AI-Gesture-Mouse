from src.gesture_recognizer import GestureRecognizer, GestureType


def build_mock_landmarks(thumb_pt=(100, 100), index_pt=(200, 100), middle_pt=(250, 100)):
    """Builds a mock 21-point landmark list with specified key landmark positions."""
    lms = [[i, 0, 0] for i in range(21)]
    lms[4] = [4, thumb_pt[0], thumb_pt[1]]      # THUMB_TIP
    lms[8] = [8, index_pt[0], index_pt[1]]      # INDEX_FINGER_TIP
    lms[12] = [12, middle_pt[0], middle_pt[1]]  # MIDDLE_FINGER_TIP
    return lms


def test_recognize_move():
    recognizer = GestureRecognizer()
    # Pointer pose: only index up: [0, 1, 0, 0, 0]
    lms = build_mock_landmarks(thumb_pt=(50, 200), index_pt=(200, 50))
    gesture, meta = recognizer.recognize([0, 1, 0, 0, 0], lms)
    assert gesture == GestureType.MOVE
    assert meta["cursor_pt"] == (200, 50)


def test_recognize_left_click_cycle():
    recognizer = GestureRecognizer(pinch_click_threshold=40.0, drag_hold_duration=0.5, click_cooldown=0.1)

    # 1. Close pinch (< 40 distance): thumb at (100, 100), index at (110, 100) -> dist = 10
    lms_pinch = build_mock_landmarks(thumb_pt=(100, 100), index_pt=(110, 100))
    t0 = 1000.0

    gesture, _ = recognizer.recognize([1, 1, 0, 0, 0], lms_pinch, current_time=t0)
    assert gesture == GestureType.IDLE  # Pinch started, holding

    # 2. Release pinch after 0.15s (before drag threshold 0.5s)
    t1 = 1000.15
    lms_open = build_mock_landmarks(thumb_pt=(100, 100), index_pt=(190, 100))
    gesture, _ = recognizer.recognize([1, 1, 0, 0, 0], lms_open, current_time=t1)
    assert gesture == GestureType.LEFT_CLICK


def test_recognize_drag_hold():
    recognizer = GestureRecognizer(pinch_click_threshold=40.0, drag_hold_duration=0.3)
    lms_pinch = build_mock_landmarks(thumb_pt=(100, 100), index_pt=(110, 100))

    # Start pinch at t0
    recognizer.recognize([1, 1, 0, 0, 0], lms_pinch, current_time=1000.0)

    # Continue holding pinch at t0 + 0.35s (> 0.3s)
    gesture, meta = recognizer.recognize([1, 1, 0, 0, 0], lms_pinch, current_time=1000.35)
    assert gesture == GestureType.DRAG
    assert meta["drag_duration"] >= 0.3


def test_recognize_right_click():
    recognizer = GestureRecognizer(click_cooldown=0.1)
    # Three fingers raised: [0, 1, 1, 1, 0]
    lms = build_mock_landmarks(thumb_pt=(50, 200), index_pt=(120, 80), middle_pt=(150, 75))
    gesture, _ = recognizer.recognize([0, 1, 1, 1, 0], lms, current_time=1000.0)
    assert gesture == GestureType.RIGHT_CLICK


def test_recognize_scroll():
    recognizer = GestureRecognizer(scroll_sensitivity=2.0)
    # Peace sign: index and middle up: [0, 1, 1, 0, 0]
    lms1 = build_mock_landmarks(index_pt=(150, 200), middle_pt=(170, 200))
    gesture1, _ = recognizer.recognize([0, 1, 1, 0, 0], lms1)
    assert gesture1 == GestureType.SCROLL

    # Next frame, hand moved upwards to y=170 (diff = 30) -> scroll up
    lms2 = build_mock_landmarks(index_pt=(150, 170), middle_pt=(170, 170))
    gesture2, meta = recognizer.recognize([0, 1, 1, 0, 0], lms2)
    assert gesture2 == GestureType.SCROLL
    assert meta["scroll_delta"] > 0
