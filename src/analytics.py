"""
Gesture Analytics & Telemetry Exporter.

Tracks real-time gesture frequency, session duration, average FPS, stroke velocities,
and exports comprehensive session reports to JSON.
"""

from typing import Dict, Any, Optional
import time
import json
import os


class GestureAnalytics:
    """
    Session analytics collector for tracking usage statistics and system telemetry.
    """

    def __init__(self):
        self.session_start = time.time()
        self.total_frames = 0
        self.gesture_counts: Dict[str, int] = {}
        self.fps_samples: list[float] = []
        self.max_velocity = 0.0
        self.total_distance_px = 0.0
        self.last_cursor_pos: Optional[tuple[float, float]] = None

    def log_frame(
        self,
        gesture_type: str,
        fps: float,
        cursor_pos: Optional[tuple[float, float]] = None
    ) -> None:
        """Logs telemetry data for a single frame execution."""
        self.total_frames += 1
        self.gesture_counts[gesture_type] = self.gesture_counts.get(gesture_type, 0) + 1

        if fps > 0:
            self.fps_samples.append(fps)
            if len(self.fps_samples) > 1000:
                self.fps_samples.pop(0)

        if cursor_pos and self.last_cursor_pos:
            dx = cursor_pos[0] - self.last_cursor_pos[0]
            dy = cursor_pos[1] - self.last_cursor_pos[1]
            dist = (dx**2 + dy**2) ** 0.5
            self.total_distance_px += dist
            if dist > self.max_velocity:
                self.max_velocity = dist

        if cursor_pos:
            self.last_cursor_pos = cursor_pos

    def get_summary(self) -> Dict[str, Any]:
        """Generates a summary dictionary of current session telemetry."""
        session_duration = round(time.time() - self.session_start, 2)
        avg_fps = round(sum(self.fps_samples) / max(1, len(self.fps_samples)), 1) if self.fps_samples else 0.0

        return {
            "session_duration_seconds": session_duration,
            "total_frames_processed": self.total_frames,
            "average_fps": avg_fps,
            "gesture_distribution": self.gesture_counts,
            "total_cursor_travel_px": round(self.total_distance_px, 1),
            "max_instantaneous_speed_px": round(self.max_velocity, 1)
        }

    def export_report(self, filepath: str = "analytics_report.json") -> bool:
        """Persists session analytics report to disk."""
        try:
            summary = self.get_summary()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=4)
            print(f"[Analytics] Report successfully exported to {filepath}")
            return True
        except Exception as e:
            print(f"[Analytics Error] Failed to export report: {e}")
            return False
