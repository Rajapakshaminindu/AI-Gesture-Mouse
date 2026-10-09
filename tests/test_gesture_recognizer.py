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


def test_recognize_five_finger_palm_right_click():
    recognizer = GestureRecognizer(confirm_frames=1)
    # Right hand mirrored with palm facing camera:
    # wrist = (300, 400), index_mcp = (260, 250), pinky_mcp = (340, 270)
    # cross product > 0 -> PALM
    lms = [[i, 0, 0] for i in range(21)]
    lms[0] = [0, 300, 400]
    lms[5] = [5, 260, 250]
    lms[17] = [17, 340, 270]
    lms[4] = [4, 200, 250]
    lms[8] = [8, 260, 100]
    gesture, meta = recognizer.recognize([1, 1, 1, 1, 1], lms, current_time=1000.0)
    assert gesture == GestureType.RIGHT_CLICK
    assert meta.get("palm_orientation") == "PALM"


def test_recognize_five_finger_back_double_click():
    recognizer = GestureRecognizer(confirm_frames=1)
    # Right hand mirrored with back facing camera:
    # wrist = (300, 400), index_mcp = (340, 250), pinky_mcp = (260, 270)
    # cross product < 0 -> BACK
    lms = [[i, 0, 0] for i in range(21)]
    lms[0] = [0, 300, 400]
    lms[5] = [5, 340, 250]
    lms[17] = [17, 260, 270]
    lms[4] = [4, 400, 250]
    lms[8] = [8, 340, 100]
    gesture, meta = recognizer.recognize([1, 1, 1, 1, 1], lms, current_time=1000.0)
    assert gesture == GestureType.DOUBLE_CLICK
    assert meta.get("palm_orientation") == "BACK"


def test_scroll_guard_prevents_accidental_double_click():
    recognizer = GestureRecognizer(confirm_frames=1)
    # 1. Active scroll frame
    lms_scroll = build_mock_landmarks(index_pt=(150, 200), middle_pt=(170, 200))
    recognizer.recognize([0, 1, 1, 0, 0], lms_scroll, current_time=1000.0)

    # 2. Immediately next frame (0.1s later), hand opens into 5 fingers back
    lms_back = [[i, 0, 0] for i in range(21)]
    lms_back[0] = [0, 300, 400]
    lms_back[5] = [5, 340, 250]
    lms_back[17] = [17, 260, 270]
    lms_back[4] = [4, 400, 250]
    lms_back[8] = [8, 340, 100]
    gesture, _ = recognizer.recognize([1, 1, 1, 1, 1], lms_back, current_time=1000.1)
    # Must be blocked by scroll guard to prevent accidentally minimizing windows
    assert gesture != GestureType.DOUBLE_CLICK


def test_opening_hand_for_right_click_does_not_fire_left_click():
    recognizer = GestureRecognizer(confirm_frames=1, pinch_click_threshold=40.0)
    # Step 1: Hand was pointing, thumb close to index (<40px)
    lms_close = build_mock_landmarks(thumb_pt=(100, 100), index_pt=(120, 100))
    g1, _ = recognizer.recognize([1, 1, 0, 0, 0], lms_close, current_time=1000.0)

    # Step 2: User opens hand to 5-finger palm (thumb and index separate >40px, all 5 fingers up)
    lms_palm = [[i, 0, 0] for i in range(21)]
    lms_palm[0] = [0, 300, 400]
    lms_palm[5] = [5, 260, 250]
    lms_palm[17] = [17, 340, 270]
    lms_palm[4] = [4, 200, 250]
    lms_palm[8] = [8, 260, 100]
    g2, _ = recognizer.recognize([1, 1, 1, 1, 1], lms_palm, current_time=1000.1)

    # Must NOT be LEFT_CLICK! Must be RIGHT_CLICK!
    assert g2 != GestureType.LEFT_CLICK
    assert g2 == GestureType.RIGHT_CLICK


def test_recognize_index_finger_tap_left_click():
    recognizer = GestureRecognizer(drag_hold_duration=0.5, click_cooldown=0.1)
    # Step 1: Index finger bent down (tapped) at t=1000.0
    # MCP (5) at (100, 300), PIP (6) at (100, 240), TIP (8) bent down at (100, 250)
    lms_bent = [[i, 0, 0] for i in range(21)]
    lms_bent[5] = [5, 100, 300]
    lms_bent[6] = [6, 100, 240]
    lms_bent[8] = [8, 100, 250]
    g1, _ = recognizer.recognize([0, 0, 0, 0, 0], lms_bent, current_time=1000.0)
    assert g1 == GestureType.IDLE  # Pressing down

    # Step 2: Index finger unbends back up at t=1000.15 (<0.5s)
    # TIP (8) now extended straight at (100, 150)
    lms_up = [[i, 0, 0] for i in range(21)]
    lms_up[5] = [5, 100, 300]
    lms_up[6] = [6, 100, 240]
    lms_up[8] = [8, 100, 150]
    g2, _ = recognizer.recognize([0, 1, 0, 0, 0], lms_up, current_time=1000.15)
    assert g2 == GestureType.LEFT_CLICK

