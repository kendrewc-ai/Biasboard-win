"""Checks for window-position repair, note fitting and slider geometry."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from geometry import (  # noqa: E402
    clamp_geometry,
    ease_out,
    fit_text,
    format_geometry,
    nearest_index,
    parse_geometry,
    position_x,
)


class FakeFont:
    """Just enough of a Tk font for the pure fitting logic."""

    def measure(self, text):
        return len(text) * 10


class TestGeometryText(unittest.TestCase):
    def test_parse_and_format_round_trip(self):
        self.assertEqual(parse_geometry("900x420+40+60"), (900, 420, 40, 60))
        self.assertEqual(format_geometry(900, 420, 40, 60), "900x420+40+60")

    def test_invalid_geometry_parses_as_none(self):
        self.assertIsNone(parse_geometry("not a geometry"))

    def test_off_screen_right_position_is_brought_back(self):
        result = clamp_geometry("800x400+5000+100", 1920, 1080, 760, 360)
        w, h, x, y = parse_geometry(result)
        self.assertLessEqual(x + w, 1920)
        self.assertGreaterEqual(x, 0)

    def test_negative_position_is_brought_back(self):
        _, _, x, y = parse_geometry(
            clamp_geometry("800x400-900-900", 1920, 1080, 760, 360)
        )
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)

    def test_oversized_window_is_shrunk_to_screen(self):
        w, h, _, _ = parse_geometry(
            clamp_geometry("4000x3000+10+10", 1920, 1080, 760, 360)
        )
        self.assertLessEqual(w, 1920)
        self.assertLessEqual(h, 1080)

    def test_invalid_saved_geometry_returns_empty_string(self):
        self.assertEqual(clamp_geometry("oops", 1920, 1080, 760, 360), "")

    def test_fit_text_leaves_short_text_alone(self):
        self.assertEqual(fit_text("5h level", FakeFont(), 240), "5h level")

    def test_fit_text_truncates_with_ellipsis(self):
        out = fit_text("a very long note that will not fit", FakeFont(), 100)
        self.assertTrue(out.endswith("…"))
        self.assertLessEqual(FakeFont().measure(out), 100)


class TestSliderMath(unittest.TestCase):
    def test_six_positions_are_evenly_spaced(self):
        xs = [position_x(i, 260, 20) for i in range(6)]
        gaps = [xs[i + 1] - xs[i] for i in range(5)]
        self.assertEqual(len(set(gaps)), 1)
        self.assertEqual(xs[0], 20)
        self.assertEqual(xs[5], 240)

    def test_nearest_index_round_trip(self):
        for i in range(6):
            self.assertEqual(nearest_index(position_x(i, 260, 20), 260, 20), i)

    def test_midpoint_choice(self):
        midpoint = (position_x(1, 260, 20) + position_x(2, 260, 20)) / 2
        self.assertEqual(nearest_index(midpoint, 260, 20), 2)

    def test_nearest_index_clamps_to_ends(self):
        self.assertEqual(nearest_index(-500, 260, 20), 0)
        self.assertEqual(nearest_index(9999, 260, 20), 5)

    def test_easing_stays_between_zero_and_one(self):
        for step in range(11):
            value = ease_out(step / 10)
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

    def test_easing_is_monotonic(self):
        values = [ease_out(i / 10) for i in range(11)]
        self.assertEqual(values, sorted(values))
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[-1], 1.0)


if __name__ == "__main__":
    unittest.main()
