"""
Action Mapper & Custom Keybinding Module.

Maps recognized hand gestures to OS actions, keyboard shortcuts, system media controls,
and user-defined custom command triggers.
"""

from typing import Dict, Any, List, Optional, Callable
import time

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False


class ActionMapper:
    """
    Translates gesture events into system actions or hotkeys with custom mapping support.
    """

    DEFAULT_BINDINGS = {
        "PALM_STOP": {"type": "system", "action": "pause_tracking"},
        "SWIPE_LEFT": {"type": "hotkey", "keys": ["alt", "left"]},
        "SWIPE_RIGHT": {"type": "hotkey", "keys": ["alt", "right"]},
        "ZOOM_IN": {"type": "hotkey", "keys": ["ctrl", "+"]},
        "ZOOM_OUT": {"type": "hotkey", "keys": ["ctrl", "-"]},
        "VOLUME_UP": {"type": "hotkey", "keys": ["volumeup"]},
        "VOLUME_DOWN": {"type": "hotkey", "keys": ["volumedown"]},
    }

    def __init__(self, custom_bindings: Optional[Dict[str, Any]] = None):
        self.bindings = dict(self.DEFAULT_BINDINGS)
        if custom_bindings:
            self.bindings.update(custom_bindings)

        self.last_execution_time: Dict[str, float] = {}
        self.cooldown_seconds: float = 0.4
        self.tracking_paused: bool = False
        self.custom_callbacks: Dict[str, Callable[[], None]] = {}

    def register_callback(self, gesture_name: str, callback: Callable[[], None]) -> None:
        """Registers a custom Python callback function for a specific gesture."""
        self.custom_callbacks[gesture_name] = callback

    def set_binding(self, gesture_name: str, binding_config: Dict[str, Any]) -> None:
        """Updates or adds a new gesture binding rule."""
        self.bindings[gesture_name] = binding_config

    def trigger_action(self, gesture_name: str, current_time: Optional[float] = None) -> bool:
        """
        Executes the action mapped to the given gesture name if outside cooldown period.
        Returns True if action was executed, False otherwise.
        """
        now = time.time() if current_time is None else current_time

        # Handle custom callbacks first
        if gesture_name in self.custom_callbacks:
            last = self.last_execution_time.get(gesture_name, 0.0)
            if now - last >= self.cooldown_seconds:
                self.last_execution_time[gesture_name] = now
                self.custom_callbacks[gesture_name]()
                return True

        if gesture_name not in self.bindings:
            return False

        last = self.last_execution_time.get(gesture_name, 0.0)
        if now - last < self.cooldown_seconds:
            return False

        binding = self.bindings[gesture_name]
        binding_type = binding.get("type")

        if binding_type == "system":
            action = binding.get("action")
            if action == "pause_tracking":
                self.tracking_paused = not self.tracking_paused
                self.last_execution_time[gesture_name] = now
                return True

        elif binding_type == "hotkey":
            keys = binding.get("keys", [])
            if keys and PYAUTOGUI_AVAILABLE and pyautogui is not None:
                try:
                    pyautogui.hotkey(*keys)
                    self.last_execution_time[gesture_name] = now
                    return True
                except Exception as e:
                    print(f"[ActionMapper Warning] Hotkey execution failed for {keys}: {e}")

        elif binding_type == "key":
            key = binding.get("key")
            if key and PYAUTOGUI_AVAILABLE and pyautogui is not None:
                try:
                    pyautogui.press(key)
                    self.last_execution_time[gesture_name] = now
                    return True
                except Exception as e:
                    print(f"[ActionMapper Warning] Key press failed for {key}: {e}")

        return False
