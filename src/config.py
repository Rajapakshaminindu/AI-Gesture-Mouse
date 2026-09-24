"""
Configuration Module for AI Gesture Mouse.

Handles runtime parameters, defaults, and JSON serialization.
"""

from dataclasses import dataclass, asdict
from typing import Tuple
import json
import os


@dataclass
class AppConfig:
    # Camera settings
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    flip_horizontal: bool = True

    # Tracking confidence
    detection_confidence: float = 0.7
    tracking_confidence: float = 0.6

    # Coordinate mapping & cursor dynamics
    frame_margin: int = 90
    smoothing_factor: float = 5.0
    deadzone: float = 3.5

    # Gesture thresholds
    pinch_threshold: float = 38.0
    drag_hold_duration: float = 0.45
    click_cooldown: float = 0.35
    scroll_sensitivity: float = 2.0

    # Display & HUD
    show_fps: bool = True
    show_hud: bool = True
    draw_landmarks: bool = True
    primary_color: Tuple[int, int, int] = (0, 255, 128)  # BGR
    accent_color: Tuple[int, int, int] = (255, 200, 0)   # BGR

    @classmethod
    def load(cls, filepath: str = "config.json") -> "AppConfig":
        """Loads configuration from JSON file or returns defaults."""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"[Warning] Failed to load config from {filepath}: {e}. Using defaults.")
        return cls()

    def save(self, filepath: str = "config.json") -> None:
        """Persists current configuration to JSON file."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4)
            print(f"[Info] Configuration saved successfully to {filepath}")
        except Exception as e:
            print(f"[Error] Failed to save config to {filepath}: {e}")
