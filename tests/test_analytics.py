import unittest
import os
import tempfile
from src.analytics import GestureAnalytics


class TestAnalytics(unittest.TestCase):

    def test_analytics_logging_and_export(self):
        analytics = GestureAnalytics()
        analytics.log_frame("MOVE", fps=30.0, cursor_pos=(100, 100))
        analytics.log_frame("MOVE", fps=32.0, cursor_pos=(150, 100))
        analytics.log_frame("LEFT_CLICK", fps=29.0, cursor_pos=(150, 100))

        summary = analytics.get_summary()
        self.assertEqual(summary["total_frames_processed"], 3)
        self.assertEqual(summary["gesture_distribution"]["MOVE"], 2)
        self.assertEqual(summary["gesture_distribution"]["LEFT_CLICK"], 1)
        self.assertEqual(summary["total_cursor_travel_px"], 50.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_report.json")
            success = analytics.export_report(filepath)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(filepath))


if __name__ == "__main__":
    unittest.main()
