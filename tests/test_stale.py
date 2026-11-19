"""Checks for stale-bias logic and age display."""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import STALE_AFTER_HOURS  # noqa: E402
from timeutil import age_text, is_stale, parse_iso, to_iso  # noqa: E402

NOW = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)


def ago(**kwargs):
    return to_iso(NOW - timedelta(**kwargs))


class TestParseAndFormat(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(parse_iso(to_iso(NOW)), NOW)

    def test_missing_timezone_is_treated_as_utc(self):
        parsed = parse_iso("2026-01-02T12:00:00")
        self.assertEqual(parsed, NOW)

    def test_invalid_text_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_iso("not a date")


class TestStaleRule(unittest.TestCase):
    def test_threshold_constant_is_24_hours(self):
        self.assertEqual(STALE_AFTER_HOURS, 24)

    def test_two_hours_old_is_fresh(self):
        self.assertFalse(is_stale(ago(hours=2), now=NOW))

    def test_exactly_24_hours_is_not_yet_stale(self):
        self.assertFalse(is_stale(ago(hours=24), now=NOW))

    def test_more_than_24_hours_is_stale(self):
        self.assertTrue(is_stale(ago(hours=24, minutes=1), now=NOW))

    def test_custom_threshold_is_honoured(self):
        self.assertTrue(is_stale(ago(hours=2), now=NOW, hours=1))

    def test_unreadable_timestamp_is_treated_as_stale(self):
        self.assertTrue(is_stale("broken", now=NOW))

    def test_future_timestamp_is_not_stale(self):
        self.assertFalse(is_stale(to_iso(NOW + timedelta(hours=1)), now=NOW))


class TestAgeText(unittest.TestCase):
    def test_minutes(self):
        self.assertEqual(age_text(ago(minutes=5), now=NOW), "5m")

    def test_hours(self):
        self.assertEqual(age_text(ago(hours=3), now=NOW), "3h")

    def test_just_now(self):
        self.assertEqual(age_text(to_iso(NOW), now=NOW), "now")

    def test_future_time_shows_now(self):
        self.assertEqual(age_text(to_iso(NOW + timedelta(minutes=5)), now=NOW), "now")

    def test_stale_rows_show_warning(self):
        self.assertEqual(age_text(ago(hours=30), now=NOW), "⚠ STALE")

    def test_bad_timestamp_shows_warning(self):
        self.assertEqual(age_text("broken", now=NOW), "⚠ STALE")

    def test_days_with_a_larger_custom_threshold(self):
        self.assertEqual(
            age_text(ago(hours=50), now=NOW, hours=72),
            "2d",
        )


if __name__ == "__main__":
    unittest.main()
