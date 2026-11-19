"""Checks for the six fixed bias states."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from states import (  # noqa: E402
    STATES,
    STATE_KEYS,
    STATE_COUNT,
    DEFAULT_STATE,
    state_by_key,
    state_at_index,
    index_of_key,
    key_at_index,
)


class TestSixStates(unittest.TestCase):
    def test_there_are_exactly_six_states(self):
        self.assertEqual(STATE_COUNT, 6)
        self.assertEqual(len(STATES), 6)

    def test_order_is_exactly_as_requested(self):
        self.assertEqual(
            list(STATE_KEYS),
            ["VB", "B", "N", "Bu", "VBu", "NT"],
        )

    def test_full_names(self):
        self.assertEqual(
            [s["name"] for s in STATES],
            [
                "Very Bearish",
                "Bearish",
                "Neutral",
                "Bullish",
                "Very Bullish",
                "No Trade",
            ],
        )

    def test_scores_for_bias_summary(self):
        self.assertEqual([s["score"] for s in STATES], [-2, -1, 0, 1, 2, None])

    def test_default_is_neutral(self):
        self.assertEqual(DEFAULT_STATE, "N")
        self.assertEqual(state_by_key(DEFAULT_STATE)["name"], "Neutral")

    def test_key_to_index_and_back(self):
        for key in STATE_KEYS:
            self.assertEqual(key_at_index(index_of_key(key)), key)

    def test_state_at_index_matches_key(self):
        for i, key in enumerate(STATE_KEYS):
            self.assertEqual(state_at_index(i)["key"], key)

    def test_unknown_key_raises_value_error(self):
        with self.assertRaises(ValueError):
            index_of_key("NOT_A_STATE")

    def test_index_out_of_range_raises_index_error(self):
        with self.assertRaises(IndexError):
            state_at_index(6)

    def test_each_state_has_a_distinct_colour(self):
        colours = [s["color"] for s in STATES]
        self.assertEqual(len(set(colours)), 6)

    def test_no_trade_is_its_own_kind(self):
        self.assertEqual(state_by_key("NT")["kind"], "no_trade")
        self.assertEqual(state_by_key("N")["kind"], "neutral")
        self.assertEqual(state_by_key("VB")["kind"], "bearish")
        self.assertEqual(state_by_key("Bu")["kind"], "bullish")


if __name__ == "__main__":
    unittest.main()
