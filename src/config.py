"""
Configuration Module for AI Gesture Mouse.

Handles runtime parameters, default bindings, adaptive smoothing options,
and JSON serialization.
"""

from dataclasses import dataclass, asdict, field, fields
from typing import Tuple, Dict, Any
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
    detection_confidence: float = 0.55  # Lower = faster initial detection
    tracking_confidence: float = 0.45   # Lower = better tracking continuity

    # Coordinate mapping & cursor dynamics
    frame_margin: int = 70              # Horizontal margin for reaching left/right edges
    frame_margin_top: int = 60          # Top margin for reaching titlebars/tabs easily
    frame_margin_bottom: int = 150      # Bottom margin: accounts for upright hand posture so taskbar is reached comfortably
    smoothing_factor: float = 5.0       # Smooth cursor movement
    deadzone: float = 1.8               # Sub-pixel deadzone; eliminates idle drift
    enable_adaptive_smoothing: bool = True

    # Gesture thresholds
    pinch_threshold: float = 38.0       # Pinch threshold for left click
    drag_hold_duration: float = 0.40    # Hold 0.4s to enter drag mode
    click_cooldown: float = 0.20        # Fast click response
    scroll_sensitivity: float = 2.5

    # Analytics & Features
    enable_analytics: bool = True

    # Custom Action Mappings
    action_bindings: Dict[str, Any] = field(default_factory=dict)

    # Display & HUD
    show_fps: bool = True
    show_hud: bool = True
    draw_landmarks: bool = True
    primary_color: Tuple[int, int, int] = (0, 255, 128)  # BGR
    accent_color: Tuple[int, int, int] = (255, 200, 0)   # BGR

    def validate(self) -> "AppConfig":
        """Clamps and validates configuration parameters to safe bounds."""
        self.camera_index = max(0, int(self.camera_index))
        self.detection_confidence = max(0.0, min(1.0, float(self.detection_confidence)))
        self.tracking_confidence = max(0.0, min(1.0, float(self.tracking_confidence)))
        self.frame_width = max(100, int(self.frame_width))
        self.frame_height = max(100, int(self.frame_height))
        self.frame_margin = max(0, int(self.frame_margin))
        self.frame_margin_top = max(0, int(self.frame_margin_top))
        self.frame_margin_bottom = max(0, int(self.frame_margin_bottom))
        self.smoothing_factor = max(1.0, float(self.smoothing_factor))
        self.deadzone = max(0.0, float(self.deadzone))
        self.pinch_threshold = max(5.0, float(self.pinch_threshold))
        self.drag_hold_duration = max(0.1, float(self.drag_hold_duration))
        self.click_cooldown = max(0.05, float(self.click_cooldown))
        self.scroll_sensitivity = max(0.1, float(self.scroll_sensitivity))

        if isinstance(self.primary_color, (list, tuple)):
            self.primary_color = tuple(int(c) for c in self.primary_color[:3])
        if isinstance(self.accent_color, (list, tuple)):
            self.accent_color = tuple(int(c) for c in self.accent_color[:3])

        return self

    @classmethod
    def load(cls, filepath: str = "config.json") -> "AppConfig":
        """Loads configuration from JSON file or returns defaults."""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                valid_keys = {f.name for f in fields(cls)}
                filtered_data = {k: v for k, v in data.items() if k in valid_keys}
                config = cls(**filtered_data)
                return config.validate()
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
