import unittest
from src.mouse_controller import MouseController


class TestAdaptiveSmoothing(unittest.TestCase):

    def test_mouse_controller_adaptive_scaling(self):
        # Create controller with 640x480 frame size and screen 1920x1080
        mouse = MouseController(
            screen_size=(1920, 1080),
            frame_size=(640, 480),
            frame_margin=0,
            smoothing_factor=10.0,
            deadzone=0.0,
            enable_adaptive_smoothing=True
        )

        # Initial position: x=0, y=0 -> maps to screen center (960, 540)
        mouse.prev_x = 960.0
        mouse.prev_y = 540.0

        # Small movement (slow speed)
        x1, y1 = mouse.map_coordinates(325, 240)
        slow_velocity = mouse.last_velocity

        # Large jump (high speed)
        x2, y2 = mouse.map_coordinates(600, 400)
        fast_velocity = mouse.last_velocity

        self.assertGreater(fast_velocity, slow_velocity)

    def test_drag_and_scroll_state(self):
        mouse = MouseController(screen_size=(1920, 1080))
        self.assertFalse(mouse.is_dragging)
        mouse.start_drag()
        self.assertTrue(mouse.is_dragging)
        mouse.end_drag()
        self.assertFalse(mouse.is_dragging)


if __name__ == "__main__":
    unittest.main()
