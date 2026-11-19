"""Checks for window-position repair, note fitting and slider geometry."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import MIN_WINDOW_SIZE  # noqa: E402
from geometry import (  # noqa: E402
    clamp_geometry,
    ease_out,
    fill_span,
    format_geometry,
    nearest_index,
    parse_geometry,
    position_x,
    scrollbar_thumb,
)


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


class TestWindowLimits(unittest.TestCase):
    def test_resize_floor_is_small(self):
        self.assertLessEqual(MIN_WINDOW_SIZE[0], 300)
        self.assertLessEqual(MIN_WINDOW_SIZE[1], 200)


class TestSliderFillFromNeutral(unittest.TestCase):
    def test_neutral_has_no_fill(self):
        start, end = fill_span(2, 260, 20)
        self.assertEqual(start, end)

    def test_bearish_fill_goes_left_from_neutral(self):
        start, end = fill_span(0, 260, 20)
        self.assertLess(end, start)
        self.assertEqual(start, position_x(2, 260, 20))

    def test_bullish_fill_goes_right_from_neutral(self):
        start, end = fill_span(4, 260, 20)
        self.assertGreater(end, start)
        self.assertEqual(start, position_x(2, 260, 20))

    def test_no_trade_fill_reaches_far_right(self):
        start, end = fill_span(5, 260, 20)
        self.assertEqual(end, position_x(5, 260, 20))


class TestMinimalScrollbar(unittest.TestCase):
    def test_full_content_gives_full_height_thumb(self):
        top, bottom = scrollbar_thumb(200, 0.0, 1.0)
        self.assertEqual((top, bottom), (0, 200))

    def test_partial_view_gives_short_thumb(self):
        top, bottom = scrollbar_thumb(200, 0.5, 1.0)
        self.assertLess(bottom - top, 200)
        self.assertGreater(bottom - top, 20)

    def test_thumb_stays_inside_track(self):
        for start, end in ((0.0, 0.2), (0.4, 0.6), (0.8, 1.0)):
            top, bottom = scrollbar_thumb(200, start, end)
            self.assertGreaterEqual(top, 0)
            self.assertLessEqual(bottom, 200)

    def test_thumb_never_becomes_tiny(self):
        top, bottom = scrollbar_thumb(200, 0.49, 0.51)
        self.assertGreaterEqual(bottom - top, 20)


if __name__ == "__main__":
    unittest.main()
