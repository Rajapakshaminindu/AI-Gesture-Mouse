from src.hand_detector import HandDetector, HandLandmarks


def test_hand_landmarks_constants():
    assert HandLandmarks.WRIST == 0
    assert HandLandmarks.THUMB_TIP == 4
    assert HandLandmarks.INDEX_FINGER_TIP == 8
    assert HandLandmarks.MIDDLE_FINGER_TIP == 12
    assert HandLandmarks.RING_FINGER_TIP == 16
    assert HandLandmarks.PINKY_TIP == 20


def test_fingers_up_empty():
    detector = HandDetector()
    assert detector.fingers_up([]) == [0, 0, 0, 0, 0]


def test_fingers_up_mock_raised():
    detector = HandDetector()
    # In image coordinates, y=0 is TOP. A finger is raised if tip y < pip y
    lms = [[i, 100, 200] for i in range(21)]

    # Set right thumb open (tip x < ip x)
    lms[HandLandmarks.THUMB_TIP][1] = 50
    lms[HandLandmarks.THUMB_IP][1] = 80

    # Index finger up (tip y = 50 < pip y = 120)
    lms[HandLandmarks.INDEX_FINGER_TIP][2] = 50
    lms[HandLandmarks.INDEX_FINGER_PIP][2] = 120

    # Middle finger down (tip y = 150 > pip y = 120)
    lms[HandLandmarks.MIDDLE_FINGER_TIP][2] = 150
    lms[HandLandmarks.MIDDLE_FINGER_PIP][2] = 120

    # Ring finger down
    lms[HandLandmarks.RING_FINGER_TIP][2] = 150
    lms[HandLandmarks.RING_FINGER_PIP][2] = 120

    # Pinky finger down
    lms[HandLandmarks.PINKY_TIP][2] = 150
    lms[HandLandmarks.PINKY_PIP][2] = 120

    result = detector.fingers_up(lms, handedness="Right")
    assert result == [1, 1, 0, 0, 0]


def test_find_distance():
    detector = HandDetector()
    lms = [[i, 0, 0] for i in range(21)]
    lms[4] = [4, 0, 0]
    lms[8] = [8, 30, 40]

    dist, info, _ = detector.find_distance(4, 8, landmarks=lms, draw=False)
    assert dist == 50.0  # 3-4-5 triangle
    assert info == [0, 0, 30, 40, 15, 20]
