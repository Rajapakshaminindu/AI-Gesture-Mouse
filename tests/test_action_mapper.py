import unittest
from src.action_mapper import ActionMapper


class TestActionMapper(unittest.TestCase):

    def test_default_bindings(self):
        mapper = ActionMapper()
        self.assertIn("PALM_STOP", mapper.bindings)
        self.assertIn("SWIPE_LEFT", mapper.bindings)
        self.assertIn("SWIPE_RIGHT", mapper.bindings)

    def test_system_pause_toggle(self):
        mapper = ActionMapper()
        self.assertFalse(mapper.tracking_paused)

        # Trigger PALM_STOP action at t = 100.0
        result = mapper.trigger_action("PALM_STOP", current_time=100.0)
        self.assertTrue(result)
        self.assertTrue(mapper.tracking_paused)

        # Trigger again outside cooldown
        result2 = mapper.trigger_action("PALM_STOP", current_time=101.0)
        self.assertTrue(result2)
        self.assertFalse(mapper.tracking_paused)

    def test_custom_callback(self):
        mapper = ActionMapper()
        called = {"status": False}

        def my_callback():
            called["status"] = True

        mapper.register_callback("TEST_GESTURE", my_callback)
        result = mapper.trigger_action("TEST_GESTURE", current_time=100.0)
        self.assertTrue(result)
        self.assertTrue(called["status"])


if __name__ == "__main__":
    unittest.main()
