"""
Configuration Module for AI Gesture Mouse.

Handles runtime parameters, defaults, and JSON serialization.
"""

from dataclasses import dataclass, asdict, fields
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

    def validate(self) -> "AppConfig":
        """Ensures all config fields are within valid boundaries and proper types."""
        self.camera_index = max(0, int(self.camera_index))
        self.frame_width = max(100, int(self.frame_width))
        self.frame_height = max(100, int(self.frame_height))

        self.detection_confidence = max(0.0, min(1.0, float(self.detection_confidence)))
        self.tracking_confidence = max(0.0, min(1.0, float(self.tracking_confidence)))

        self.frame_margin = max(0, int(self.frame_margin))
        self.smoothing_factor = max(1.0, float(self.smoothing_factor))
        self.deadzone = max(0.0, float(self.deadzone))

        self.pinch_threshold = max(1.0, float(self.pinch_threshold))
        self.drag_hold_duration = max(0.05, float(self.drag_hold_duration))
        self.click_cooldown = max(0.0, float(self.click_cooldown))
        self.scroll_sensitivity = max(0.1, float(self.scroll_sensitivity))

        if isinstance(self.primary_color, (list, tuple)) and len(self.primary_color) == 3:
            self.primary_color = (int(self.primary_color[0]), int(self.primary_color[1]), int(self.primary_color[2]))

        if isinstance(self.accent_color, (list, tuple)) and len(self.accent_color) == 3:
            self.accent_color = (int(self.accent_color[0]), int(self.accent_color[1]), int(self.accent_color[2]))

        return self

    @classmethod
    def load(cls, filepath: str = "config.json") -> "AppConfig":
        """Loads configuration from JSON file with schema filtering and parameter validation."""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if not isinstance(data, dict):
                    print(f"[Warning] Config file {filepath} does not contain a JSON dictionary. Using defaults.")
                    return cls().validate()

                valid_fields = {f.name for f in fields(cls)}
                filtered_data = {}
                unknown_keys = []

                for k, v in data.items():
                    if k in valid_fields:
                        filtered_data[k] = v
                    else:
                        unknown_keys.append(k)

                if unknown_keys:
                    print(f"[Warning] Ignored unknown config parameters in {filepath}: {unknown_keys}")

                instance = cls(**filtered_data)
                return instance.validate()
            except Exception as e:
                print(f"[Warning] Failed to load config from {filepath}: {e}. Using defaults.")

        return cls().validate()

    def save(self, filepath: str = "config.json") -> None:
        """Persists current configuration to JSON file."""
        try:
            self.validate()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4)
            print(f"[Info] Configuration saved successfully to {filepath}")
        except Exception as e:
            print(f"[Error] Failed to save config to {filepath}: {e}")
