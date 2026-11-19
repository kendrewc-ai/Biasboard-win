"""Checks for the off-white minimalist design tokens."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import FONT_MONO, FONT_UI, THEME  # noqa: E402
from states import STATES  # noqa: E402


def luminance(hex_colour):
    parts = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


class TestLightPalette(unittest.TestCase):
    def test_canvas_is_off_white_not_dark(self):
        self.assertGreater(luminance(THEME["bg"]), 0.85)

    def test_card_surface_is_white(self):
        self.assertGreater(luminance(THEME["panel"]), 0.95)

    def test_primary_text_is_dark(self):
        self.assertLess(luminance(THEME["text"]), 0.2)

    def test_only_one_saturated_accent(self):
        accent = THEME["accent"].lstrip("#")
        r, g, b = (int(accent[i:i + 2], 16) for i in (0, 2, 4))
        self.assertGreater(b, r + 60)
        self.assertGreater(b, g)

    def test_required_theme_keys_exist(self):
        for key in ("bg", "panel", "panel_alt", "border", "text", "muted",
                    "accent", "error", "warning", "track", "knob"):
            self.assertIn(key, THEME)

    def test_ui_and_mono_fonts_are_windows_system_fonts(self):
        self.assertIn("Segoe UI", FONT_UI)
        self.assertIn("Consolas", FONT_MONO)

    def test_state_colours_are_distinct_and_muted(self):
        colours = [state["color"] for state in STATES]
        self.assertEqual(len(set(colours)), 6)
        for colour in colours:
            light = luminance(colour)
            self.assertGreater(light, 0.05)
            self.assertLess(light, 0.55)


if __name__ == "__main__":
    unittest.main()
