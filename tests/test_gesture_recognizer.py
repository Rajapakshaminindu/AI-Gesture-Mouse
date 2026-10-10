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


def test_recognize_two_finger_one_shot_left_click():
    recognizer = GestureRecognizer(click_cooldown=0.1)
    lms = build_mock_landmarks(thumb_pt=(50, 200), index_pt=(200, 100), middle_pt=(250, 100))
    # Make sure ring (16) and pinky (20) are curled down
    lms[14] = [14, 280, 200]
    lms[16] = [16, 280, 250]
    lms[18] = [18, 300, 200]
    lms[20] = [20, 300, 250]

    # 1. User raises Index + Middle fingers: [0, 1, 1, 0, 0] at t0 (start confirming)
    g1, meta1 = recognizer.recognize([0, 1, 1, 0, 0], lms, current_time=1000.0)
    assert g1 == GestureType.IDLE
    assert meta1.get("status") == "two_finger_confirming"

    # 2. Stable hold after 31ms (> 30ms threshold) at t0 + 0.031s -> Fires LEFT_CLICK!
    g2, meta2 = recognizer.recognize([0, 1, 1, 0, 0], lms, current_time=1000.031)
    assert g2 == GestureType.LEFT_CLICK
    assert meta2.get("status") == "two_finger_click"

    # 3. User continues holding the two fingers up at t0 + 0.2s -> Stays latched IDLE
    g3, meta3 = recognizer.recognize([0, 1, 1, 0, 0], lms, current_time=1000.2)
    assert g3 == GestureType.IDLE
    assert meta3.get("status") == "two_finger_held"

    # 4. User lowers middle finger back to 1 finger (pointing) at t0 + 0.6s
    g4, _ = recognizer.recognize([0, 1, 0, 0, 0], lms, current_time=1000.6)
    assert g4 == GestureType.MOVE

    # 5. User raises middle finger again (fresh 2 fingers) at t0 + 0.8s
    recognizer.recognize([0, 1, 1, 0, 0], lms, current_time=1000.80)
    g5, meta5 = recognizer.recognize([0, 1, 1, 0, 0], lms, current_time=1000.85)
    assert g5 == GestureType.LEFT_CLICK


def test_raising_three_fingers_for_scroll_never_fires_left_click():
    """Verify that transitioning from 1 finger to 3 fingers to scroll does NOT fire a left click."""
    recognizer = GestureRecognizer()

    # Step 1: User is pointing with index finger (t = 1000.0)
    lms1 = [[i, 0, 0] for i in range(21)]
    lms1[6] = [6, 200, 200]
    lms1[8] = [8, 200, 100]  # index up
    lms1[10] = [10, 250, 200]; lms1[12] = [12, 250, 250]  # middle down
    lms1[14] = [14, 280, 200]; lms1[16] = [16, 280, 250]  # ring down
    lms1[18] = [18, 300, 200]; lms1[20] = [20, 300, 250]  # pinky down
    g1, _ = recognizer.recognize([0, 1, 0, 0, 0], lms1, current_time=1000.0)
    assert g1 == GestureType.MOVE

    # Step 2: During lifting hand to 3 fingers, middle finger appears for 15ms (t = 1000.015)
    lms2 = [[i, 0, 0] for i in range(21)]
    lms2[6] = [6, 200, 200]; lms2[8] = [8, 200, 100]      # index up
    lms2[10] = [10, 250, 200]; lms2[12] = [12, 250, 100]  # middle up
    lms2[14] = [14, 280, 200]; lms2[16] = [16, 280, 250]  # ring still down
    lms2[18] = [18, 300, 200]; lms2[20] = [20, 300, 250]  # pinky down
    g2, _ = recognizer.recognize([0, 1, 1, 0, 0], lms2, current_time=1000.015)
    # Must NOT fire LEFT_CLICK! (Still within 23ms transition window)
    assert g2 != GestureType.LEFT_CLICK

    # Step 3: Ring finger is now up (3 fingers for scroll, t = 1000.03)
    lms3 = [[i, 0, 0] for i in range(21)]
    lms3[6] = [6, 200, 200]; lms3[8] = [8, 200, 100]      # index up
    lms3[10] = [10, 250, 200]; lms3[12] = [12, 250, 100]  # middle up
    lms3[14] = [14, 280, 200]; lms3[16] = [16, 280, 100]  # ring up
    lms3[18] = [18, 300, 200]; lms3[20] = [20, 300, 250]  # pinky down
    g3, _ = recognizer.recognize([0, 1, 1, 1, 0], lms3, current_time=1000.03)
    assert g3 == GestureType.SCROLL
    assert g3 != GestureType.LEFT_CLICK


def test_recognize_scroll():
    recognizer = GestureRecognizer(scroll_sensitivity=2.0)
    # Three fingers up: index, middle, ring up: [0, 1, 1, 1, 0]
    lms1 = [[i, 0, 0] for i in range(21)]
    lms1[8] = [8, 150, 200]
    lms1[12] = [12, 170, 200]
    lms1[16] = [16, 190, 200]
    gesture1, _ = recognizer.recognize([0, 1, 1, 1, 0], lms1)
    assert gesture1 == GestureType.SCROLL

    # Next frame, hand moved upwards to y=170 (diff = 30) -> scroll up
    lms2 = [[i, 0, 0] for i in range(21)]
    lms2[8] = [8, 150, 170]
    lms2[12] = [12, 170, 170]
    lms2[16] = [16, 190, 170]
    gesture2, meta = recognizer.recognize([0, 1, 1, 1, 0], lms2)
    assert gesture2 == GestureType.SCROLL
    assert meta["scroll_delta"] > 0


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
    # 1. Active 3-finger scroll frame
    lms_scroll = [[i, 0, 0] for i in range(21)]
    lms_scroll[8] = [8, 150, 200]
    lms_scroll[12] = [12, 170, 200]
    lms_scroll[16] = [16, 190, 200]
    recognizer.recognize([0, 1, 1, 1, 0], lms_scroll, current_time=1000.0)

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


def test_pointing_index_finger_moving_never_fires_left_click():
    """Verifies that moving index finger around (pointing) does NOT fire accidental clicks."""
    recognizer = GestureRecognizer(pinch_click_threshold=40.0)
    # Index finger extended (thumb separated > 60px)
    lms1 = build_mock_landmarks(thumb_pt=(80, 200), index_pt=(200, 100))
    g1, _ = recognizer.recognize([0, 1, 0, 0, 0], lms1, current_time=1000.0)
    assert g1 == GestureType.MOVE

    # Hand moves gently across screen
    lms2 = build_mock_landmarks(thumb_pt=(85, 205), index_pt=(215, 105))
    g2, _ = recognizer.recognize([0, 1, 0, 0, 0], lms2, current_time=1000.1)
    assert g2 == GestureType.MOVE

    # Hand moves again
    lms3 = build_mock_landmarks(thumb_pt=(90, 210), index_pt=(230, 110))
    g3, _ = recognizer.recognize([0, 1, 0, 0, 0], lms3, current_time=1000.2)
    assert g3 == GestureType.MOVE
    assert g3 != GestureType.LEFT_CLICK


def test_opening_hand_does_not_fire_left_click():
    recognizer = GestureRecognizer(confirm_frames=1, pinch_click_threshold=40.0)
    # Step 1: Hand was pointing, thumb close to index (<40px)
    lms_close = build_mock_landmarks(thumb_pt=(100, 100), index_pt=(120, 100))
    g1, _ = recognizer.recognize([1, 1, 0, 0, 0], lms_close, current_time=1000.0)

    # Step 2: User opens hand to 5 fingers (all 5 fingers up)
    lms_open = [[i, 0, 0] for i in range(21)]
    lms_open[0] = [0, 300, 400]
    lms_open[5] = [5, 260, 250]
    lms_open[17] = [17, 340, 270]
    lms_open[4] = [4, 200, 250]
    lms_open[8] = [8, 260, 100]
    g2, _ = recognizer.recognize([1, 1, 1, 1, 1], lms_open, current_time=1000.1)

    # Must NOT be LEFT_CLICK!
    assert g2 != GestureType.LEFT_CLICK


def test_drag_and_idle_removed_from_controls():
    """Verify Drag and Idle are excluded from controls and all entries have symbol badges."""
    from src.launcher_ui import GESTURES
    names = [name for _, name, _, _ in GESTURES]
    assert "Drag" not in names
    assert "Idle" not in names
    assert len(GESTURES) == 5

    # Check symbols are present
    symbols = [sym for sym, _, _, _ in GESTURES]
    expected_symbols = ["☝️", "✌️", "👍", "🖐️", "3️⃣"]
    assert symbols == expected_symbols


def test_pinch_does_not_trigger_drag():
    """Verify that pinching thumb and index does not trigger DRAG gesture."""
    recognizer = GestureRecognizer()
    # Mock tight pinch
    lms_pinch = build_mock_landmarks(thumb_pt=(100, 100), index_pt=(102, 100))
    # Holding pinch for > 0.5s
    for dt in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        g, _ = recognizer.recognize([0, 0, 0, 0, 0], lms_pinch, current_time=1000.0 + dt)
        assert g != GestureType.DRAG


def test_right_click_transition_to_move_does_not_fire_left_click():
    """Verifies that transitioning from thumbs-up right click back to pointing never misfires left click."""
    recognizer = GestureRecognizer(confirm_frames=1)

    # 1. Thumbs-up gesture at t = 1000.0
    # wrist (0, 300), thumb_mcp (100, 200), thumb_tip (100, 100), index_tip (150, 250)
    lms_thumb = [[i, 0, 0] for i in range(21)]
    lms_thumb[0] = [0, 100, 300]
    lms_thumb[2] = [2, 100, 200]
    lms_thumb[4] = [4, 100, 100]  # thumb straight up
    # All fingers curled down: tips below PIPs
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        lms_thumb[pip] = [pip, 150, 200]
        lms_thumb[tip] = [tip, 150, 250]

    g_rc, _ = recognizer.recognize([1, 0, 0, 0, 0], lms_thumb, current_time=1000.0)
    assert g_rc == GestureType.RIGHT_CLICK

    # 2. Transition frame 100ms later: fingers uncurling, thumb still partly up [1, 1, 1, 0, 0]
    g_trans, _ = recognizer.recognize([1, 1, 1, 0, 0], lms_thumb, current_time=1000.1)
    assert g_trans != GestureType.LEFT_CLICK

    # 3. Transition frame 200ms later: two fingers appear during hand reshape
    lms_two = build_mock_landmarks(thumb_pt=(50, 200), index_pt=(200, 100), middle_pt=(250, 100))
    lms_two[14] = [14, 280, 200]; lms_two[16] = [16, 280, 250]
    lms_two[18] = [18, 300, 200]; lms_two[20] = [20, 300, 250]
    g_two, _ = recognizer.recognize([0, 1, 1, 0, 0], lms_two, current_time=1000.2)
    # Blocked by right click guard duration (0.65s) -> Must NOT fire left click!
    assert g_two != GestureType.LEFT_CLICK

    # 4. Pointing index finger (MOVE) at t = 1000.3
    g_move, _ = recognizer.recognize([0, 1, 0, 0, 0], lms_two, current_time=1000.3)
    assert g_move == GestureType.MOVE


def test_long_held_right_click_transition_does_not_fire_left_click():
    """Verifies that holding right click for 2.0s and releasing never misfires left click."""
    recognizer = GestureRecognizer(confirm_frames=1)

    lms_thumb = [[i, 0, 0] for i in range(21)]
    lms_thumb[0] = [0, 100, 300]
    lms_thumb[2] = [2, 100, 200]
    lms_thumb[4] = [4, 100, 100]
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        lms_thumb[pip] = [pip, 150, 200]
        lms_thumb[tip] = [tip, 150, 250]

    # Fires at t = 1000.0
    g, _ = recognizer.recognize([1, 0, 0, 0, 0], lms_thumb, current_time=1000.0)
    assert g == GestureType.RIGHT_CLICK

    # User holds thumbs-up for 2 seconds (menu is visible)
    for t_step in [1000.5, 1001.0, 1001.5, 1002.0]:
        g_held, meta_held = recognizer.recognize([1, 0, 0, 0, 0], lms_thumb, current_time=t_step)
        assert g_held == GestureType.IDLE
        assert meta_held.get("status") == "thumbs_up_held"

    # User releases thumbs-up at t = 1002.1 and hand momentarily flashes 2 fingers during uncurl
    lms_two = build_mock_landmarks(thumb_pt=(50, 200), index_pt=(200, 100), middle_pt=(250, 100))
    lms_two[14] = [14, 280, 200]; lms_two[16] = [16, 280, 250]
    lms_two[18] = [18, 300, 200]; lms_two[20] = [20, 300, 250]
    g_exit, _ = recognizer.recognize([0, 1, 1, 0, 0], lms_two, current_time=1002.15)
    # MUST NOT fire left click (guard remains active after releasing held thumbs-up)!
    assert g_exit != GestureType.LEFT_CLICK

    # Reaching MOVE state smoothly
    g_move, _ = recognizer.recognize([0, 1, 0, 0, 0], lms_two, current_time=1002.3)
    assert g_move == GestureType.MOVE


def test_open_hand_triggers_double_click_cleanly():
    """Verifies that an open hand (4 or 5 fingers up) triggers double click promptly."""
    recognizer = GestureRecognizer(confirm_frames=1)
    lms_open = [[i, 0, 0] for i in range(21)]
    lms_open[0] = [0, 300, 400]
    lms_open[5] = [5, 300, 250]
    lms_open[17] = [17, 300, 250]
    lms_open[4] = [4, 400, 250]
    lms_open[8] = [8, 300, 100]

    gesture, meta = recognizer.recognize([1, 1, 1, 1, 1], lms_open, current_time=1000.0)
    assert gesture == GestureType.DOUBLE_CLICK




