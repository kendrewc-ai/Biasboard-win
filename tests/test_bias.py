"""Checks for the currency bias summary and conflict flags."""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bias import currency_bias_summary  # noqa: E402
from timeutil import to_iso  # noqa: E402

NOW = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
FRESH = to_iso(NOW)


def pair(symbol, state, updated_at=FRESH):
    return {"symbol": symbol, "state": state, "updated_at": updated_at}


class TestCurrencyBiasSummary(unittest.TestCase):
    def test_bullish_eurusd_scores_eur_plus_one_usd_minus_one(self):
        out = currency_bias_summary([pair("EURUSD", "Bu")], now=NOW)
        self.assertEqual(out["currencies"]["EUR"]["net"], 1)
        self.assertEqual(out["currencies"]["USD"]["net"], -1)

    def test_very_bullish_usdchf_scores_usd_plus_two_chf_minus_two(self):
        out = currency_bias_summary([pair("USDCHF", "VBu")], now=NOW)
        self.assertEqual(out["currencies"]["USD"]["net"], 2)
        self.assertEqual(out["currencies"]["CHF"]["net"], -2)

    def test_example_from_the_spec_creates_a_usd_conflict(self):
        out = currency_bias_summary(
            [pair("EURUSD", "Bu"), pair("USDCHF", "VBu")], now=NOW
        )
        self.assertIn("USD", out["conflicts"])
        self.assertEqual(out["currencies"]["USD"]["net"], 1)
        self.assertEqual(
            set(out["currencies"]["USD"]["conflict_pairs"]),
            {"EURUSD", "USDCHF"},
        )

    def test_bearish_and_very_bearish_signs(self):
        out = currency_bias_summary(
            [pair("USDJPY", "B"), pair("EURUSD", "VB")], now=NOW
        )
        # USD -1 from USDJPY, +2 from EURUSD = +1 (and that is a conflict).
        self.assertEqual(out["currencies"]["USD"]["net"], 1)
        self.assertIn("USD", out["conflicts"])
        self.assertEqual(out["currencies"]["JPY"]["net"], 1)
        self.assertEqual(out["currencies"]["EUR"]["net"], -2)

    def test_neutral_pairs_are_ignored(self):
        out = currency_bias_summary([pair("EURUSD", "N")], now=NOW)
        self.assertEqual(out["currencies"], {})

    def test_no_trade_pairs_are_ignored(self):
        out = currency_bias_summary([pair("EURUSD", "NT")], now=NOW)
        self.assertEqual(out["currencies"], {})

    def test_stale_pairs_are_ignored(self):
        old = to_iso(NOW - timedelta(hours=25))
        out = currency_bias_summary([pair("EURUSD", "Bu", old)], now=NOW)
        self.assertEqual(out["currencies"], {})
        self.assertIn("EURUSD", out["ignored"])

    def test_three_same_direction_pairs_flag_concentration(self):
        out = currency_bias_summary(
            [pair("USDCHF", "Bu"), pair("USDCAD", "Bu"), pair("USDJPY", "Bu")],
            now=NOW,
        )
        self.assertEqual(out["currencies"]["USD"]["net"], 3)
        self.assertTrue(out["currencies"]["USD"]["concentration"])
        self.assertIn("USD", out["concentrated"])

    def test_net_two_is_not_concentration(self):
        out = currency_bias_summary(
            [pair("USDCHF", "Bu"), pair("USDCAD", "Bu")], now=NOW
        )
        self.assertEqual(out["currencies"]["USD"]["net"], 2)
        self.assertFalse(out["currencies"]["USD"]["concentration"])

    def test_currencies_are_sorted_for_stable_display(self):
        out = currency_bias_summary(
            [pair("USDCHF", "Bu"), pair("EURUSD", "Bu")], now=NOW
        )
        self.assertEqual(list(out["currencies"]), ["CHF", "EUR", "USD"])

    def test_metal_code_is_included(self):
        out = currency_bias_summary([pair("XAUUSD", "VBu")], now=NOW)
        self.assertEqual(out["currencies"]["XAU"]["net"], 2)
        self.assertEqual(out["currencies"]["USD"]["net"], -2)

    def test_contribution_symbols_are_kept(self):
        out = currency_bias_summary([pair("EURUSD", "Bu")], now=NOW)
        self.assertEqual(out["currencies"]["EUR"]["contributions"],
                         [("EURUSD", 1)])

    def test_accepts_pair_objects_from_the_app(self):
        from models import Pair
        item = Pair.new("EURUSD")
        item.state = "Bu"
        item.updated_at = FRESH
        out = currency_bias_summary([item], now=NOW)
        self.assertEqual(out["currencies"]["EUR"]["net"], 1)

    def test_empty_board_gives_empty_summary(self):
        self.assertEqual(
            currency_bias_summary([], now=NOW),
            {"currencies": {}, "conflicts": [], "concentrated": [], "ignored": []},
        )


if __name__ == "__main__":
    unittest.main()
