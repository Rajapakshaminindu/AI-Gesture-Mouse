"""
Hand Tracking and Landmark Detection Module.

Utilizes Google MediaPipe Hands and OpenCV to track 21 3D hand landmarks in real time.
"""

from typing import List, Tuple, Optional, Dict, Any
import math
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

try:
    import numpy as np
except ImportError:
    np = None

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    mp = None
    MEDIAPIPE_AVAILABLE = False


class HandLandmarks:
    """MediaPipe Hand Landmark Indices."""
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    FINGER_TIPS = [THUMB_TIP, INDEX_FINGER_TIP, MIDDLE_FINGER_TIP, RING_FINGER_TIP, PINKY_TIP]
    FINGER_PIPS = [THUMB_IP, INDEX_FINGER_PIP, MIDDLE_FINGER_PIP, RING_FINGER_PIP, PINKY_PIP]


class HandDetector:
    """
    Wrapper for MediaPipe Hands with gesture utility functions.
    """

    def __init__(
        self,
        mode: bool = False,
        max_hands: int = 1,
        detection_con: float = 0.7,
        track_con: float = 0.6
    ):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        self.mp_hands = None
        self.hands = None
        self.mp_draw = None
        self.results = None
        self.landmark_list: List[List[int]] = []

        if MEDIAPIPE_AVAILABLE and mp is not None:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=self.mode,
                max_num_hands=self.max_hands,
                min_detection_confidence=self.detection_con,
                min_tracking_confidence=self.track_con
            )
            self.mp_draw = mp.solutions.drawing_utils

    def find_hands(self, img: Any, draw: bool = True) -> Any:
        """
        Processes image frame to detect hands and draw landmark skeleton.
        """
        if not MEDIAPIPE_AVAILABLE or self.hands is None or cv2 is None:
            return img

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks and draw:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    img,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=(0, 255, 128), thickness=2, circle_radius=3),
                    self.mp_draw.DrawingSpec(color=(255, 200, 0), thickness=2, circle_radius=2)
                )

        return img

    def find_positions(
        self,
        img: Any,
        hand_no: int = 0
    ) -> List[List[int]]:
        """
        Returns a list of 21 landmark positions [id, x, y] in pixel coordinates.
        """
        self.landmark_list = []

        if not MEDIAPIPE_AVAILABLE or self.results is None or not self.results.multi_hand_landmarks:
            return self.landmark_list

        if hand_no < len(self.results.multi_hand_landmarks):
            selected_hand = self.results.multi_hand_landmarks[hand_no]
            h, w, _ = img.shape
            for idx, lm in enumerate(selected_hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.landmark_list.append([idx, cx, cy])

        return self.landmark_list

    def fingers_up(
        self,
        landmarks: Optional[List[List[int]]] = None,
        handedness: str = "Right"
    ) -> List[int]:
        """
        Determines which fingers are raised.
        Returns a list of 5 integers (1 for UP, 0 for DOWN): [Thumb, Index, Middle, Ring, Pinky]
        """
        lm = landmarks if landmarks is not None else self.landmark_list
        if len(lm) < 21:
            return [0, 0, 0, 0, 0]

        fingers = []

        # Thumb: compare X coordinates depending on hand orientation
        # For Right Hand facing camera: tip to the left (smaller x) means open
        if handedness == "Right":
            if lm[HandLandmarks.THUMB_TIP][1] < lm[HandLandmarks.THUMB_IP][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:
            if lm[HandLandmarks.THUMB_TIP][1] > lm[HandLandmarks.THUMB_IP][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        # 4 Fingers: check if tip Y coordinate is above PIP Y coordinate (y is 0 at top)
        for tip_id, pip_id in zip(HandLandmarks.FINGER_TIPS[1:], HandLandmarks.FINGER_PIPS[1:]):
            if lm[tip_id][2] < lm[pip_id][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def find_distance(
        self,
        p1: int,
        p2: int,
        img: Optional[Any] = None,
        landmarks: Optional[List[List[int]]] = None,
        draw: bool = True
    ) -> Tuple[float, List[int], Optional[Any]]:
        """
        Calculates Euclidean distance between two landmarks.
        Returns (distance, [x1, y1, x2, y2, cx, cy], img)
        """
        lm = landmarks if landmarks is not None else self.landmark_list
        if len(lm) < 21:
            return 0.0, [0, 0, 0, 0, 0, 0], img

        x1, y1 = lm[p1][1], lm[p1][2]
        x2, y2 = lm[p2][1], lm[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)

        if img is not None and draw and cv2 is not None:
            cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
            cv2.circle(img, (cx, cy), 6, (0, 255, 255), cv2.FILLED)

        return length, [x1, y1, x2, y2, cx, cy], img
