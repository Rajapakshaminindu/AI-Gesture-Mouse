"""
Hand Tracking and Landmark Detection Module.

Utilizes Google MediaPipe Hands and OpenCV to track 21 3D hand landmarks in real time.
Optimized for faster detection and improved responsiveness.
"""

from typing import List, Tuple, Optional, Dict, Any
import math

# Check for cv2 availability
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

# Check for numpy availability
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

# Check for mediapipe availability
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

    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),        # thumb
        (0, 5), (5, 6), (6, 7), (7, 8),        # index
        (5, 9), (9, 10), (10, 11), (11, 12),   # middle
        (9, 13), (13, 14), (14, 15), (15, 16), # ring
        (13, 17), (17, 18), (18, 19), (19, 20),# pinky
        (0, 17)                                # palm
    ]


class HandDetector:
    """
    Wrapper for MediaPipe Hands with gesture utility functions.
    Supports both legacy mediapipe.solutions.hands and modern MediaPipe Tasks API.
    
    Optimizations:
    - Lower detection confidence for faster response
    - Continuous tracking mode for smoother results
    - Optimized landmark processing pipeline
    """

    def __init__(
        self,
        mode: bool = False,
        max_hands: int = 1,
        detection_con: float = 0.5,  # Reduced from 0.7 for faster detection
        track_con: float = 0.5       # Reduced from 0.6 for faster tracking
    ):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        self.mp_hands = None
        self.hands = None
        self.mp_draw = None
        self.task_detector = None
        self.use_tasks_api = False
        self.results = None
        self.landmark_list: List[List[int]] = []

        if MEDIAPIPE_AVAILABLE and mp is not None:
            # 1. Try legacy solutions API first
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
                try:
                    self.mp_hands = mp.solutions.hands
                    self.hands = self.mp_hands.Hands(
                        static_image_mode=self.mode,
                        max_num_hands=self.max_hands,
                        min_detection_confidence=self.detection_con,
                        min_tracking_confidence=self.track_con
                    )
                    self.mp_draw = mp.solutions.drawing_utils
                except Exception:
                    self.hands = None

            # 2. If legacy API is unavailable (e.g. MediaPipe >= 0.10.30 or Python 3.13), use Tasks API
            if self.hands is None:
                try:
                    import os
                    import urllib.request
                    from mediapipe.tasks import python as mp_python
                    from mediapipe.tasks.python import vision as mp_vision

                    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
                    os.makedirs(model_dir, exist_ok=True)
                    model_path = os.path.join(model_dir, "hand_landmarker.task")

                    if not os.path.exists(model_path) or os.path.getsize(model_path) < 1000:
                        url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                        urllib.request.urlretrieve(url, model_path)

                    base_options = mp_python.BaseOptions(model_asset_path=model_path)
                    options = mp_vision.HandLandmarkerOptions(
                        base_options=base_options,
                        running_mode=mp_vision.RunningMode.IMAGE,
                        num_hands=self.max_hands,
                        min_hand_detection_confidence=self.detection_con,
                        min_tracking_confidence=self.track_con
                    )
                    self.task_detector = mp_vision.HandLandmarker.create_from_options(options)
                    self.use_tasks_api = True
                except Exception as e:
                    import warnings
                    warnings.warn(
                        f"MediaPipe hand tracking could not be initialized: {e}. Hand tracking will be unavailable.",
                        RuntimeWarning,
                        stacklevel=2
                    )
                    self.task_detector = None
        else:
            import warnings
            warnings.warn(
                "MediaPipe is not installed. Hand detection will be unavailable. "
                "Please install: pip install mediapipe",
                RuntimeWarning,
                stacklevel=2
            )

    def find_hands(self, img: Any, draw: bool = True) -> Any:
        """
        Processes image frame to detect hands and draw landmark skeleton.
        Optimized for speed and responsiveness.
        """
        if not MEDIAPIPE_AVAILABLE or not CV2_AVAILABLE or cv2 is None or img is None:
            return img

        if not self.use_tasks_api and self.hands is None:
            return img

        if self.use_tasks_api and self.task_detector is None:
            return img

        try:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            if self.use_tasks_api:
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
                self.results = self.task_detector.detect(mp_img)

                if self.results and hasattr(self.results, "hand_landmarks") and self.results.hand_landmarks and draw:
                    h, w, _ = img.shape
                    for hand_landmarks in self.results.hand_landmarks:
                        coords = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]
                        for start_idx, end_idx in HandLandmarks.HAND_CONNECTIONS:
                            if start_idx < len(coords) and end_idx < len(coords):
                                cv2.line(img, coords[start_idx], coords[end_idx], (0, 255, 128), 2)
                        for cx, cy in coords:
                            cv2.circle(img, (cx, cy), 4, (255, 200, 0), cv2.FILLED)
                            cv2.circle(img, (cx, cy), 2, (0, 255, 128), cv2.FILLED)
            else:
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
        except Exception as e:
            print(f"[Warning] Error in hand detection: {e}")
            return img

        return img

    def find_positions(
        self,
        img: Any,
        hand_no: int = 0
    ) -> List[List[int]]:
        """
        Returns a list of 21 landmark positions [id, x, y] in pixel coordinates.
        Optimized for fast processing.
        """
        self.landmark_list = []

        if not MEDIAPIPE_AVAILABLE or self.results is None or img is None:
            return self.landmark_list

        try:
            h, w, _ = img.shape
            if self.use_tasks_api:
                if hasattr(self.results, "hand_landmarks") and self.results.hand_landmarks:
                    if hand_no < len(self.results.hand_landmarks):
                        selected_hand = self.results.hand_landmarks[hand_no]
                        for idx, lm in enumerate(selected_hand):
                            cx, cy = int(lm.x * w), int(lm.y * h)
                            self.landmark_list.append([idx, cx, cy])
            else:
                if hasattr(self.results, "multi_hand_landmarks") and self.results.multi_hand_landmarks:
                    if hand_no < len(self.results.multi_hand_landmarks):
                        selected_hand = self.results.multi_hand_landmarks[hand_no]
                        for idx, lm in enumerate(selected_hand.landmark):
                            cx, cy = int(lm.x * w), int(lm.y * h)
                            self.landmark_list.append([idx, cx, cy])
        except Exception as e:
            print(f"[Warning] Error extracting landmark positions: {e}")

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

        try:
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
        except (IndexError, TypeError) as e:
            print(f"[Warning] Error detecting finger states: {e}")
            return [0, 0, 0, 0, 0]

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

        try:
            x1, y1 = lm[p1][1], lm[p1][2]
            x2, y2 = lm[p2][1], lm[p2][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            length = math.hypot(x2 - x1, y2 - y1)

            if img is not None and draw and CV2_AVAILABLE and cv2 is not None:
                cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
                cv2.circle(img, (cx, cy), 6, (0, 255, 255), cv2.FILLED)

            return length, [x1, y1, x2, y2, cx, cy], img
        except (IndexError, TypeError, ValueError) as e:
            print(f"[Warning] Error calculating distance: {e}")
            return 0.0, [0, 0, 0, 0, 0, 0], img
