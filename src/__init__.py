"""
AI Gesture Mouse Package.
"""

from src.config import AppConfig
from src.hand_detector import HandDetector, HandLandmarks
from src.mouse_controller import MouseController
from src.gesture_recognizer import GestureRecognizer, GestureType

__version__ = "1.0.0"
__all__ = [
    "AppConfig",
    "HandDetector",
    "HandLandmarks",
    "MouseController",
    "GestureRecognizer",
    "GestureType"
]
