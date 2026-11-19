"""Checks for pair symbol validation."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from validation import normalise_symbol, validate_symbol  # noqa: E402


class TestNormalise(unittest.TestCase):
    def test_typed_lowercase_becomes_uppercase(self):
        self.assertEqual(normalise_symbol(" eurusd "), "EURUSD")


class TestValidateSymbol(unittest.TestCase):
    def test_valid_major_pair(self):
        self.assertEqual(validate_symbol("EURUSD"), ("EURUSD", None))

    def test_valid_metal_pair(self):
        self.assertEqual(validate_symbol("xauusd"), ("XAUUSD", None))

    def test_valid_silver_pair(self):
        self.assertEqual(validate_symbol("XAGUSD"), ("XAGUSD", None))

    def test_empty_input_gives_clear_error(self):
        symbol, error = validate_symbol("   ")
        self.assertIsNone(symbol)
        self.assertIn("Enter", error)

    def test_wrong_length_is_rejected(self):
        symbol, error = validate_symbol("EURUS")
        self.assertIsNone(symbol)
        self.assertIn("6", error)

    def test_non_letters_are_rejected(self):
        symbol, error = validate_symbol("EURU5D")
        self.assertIsNone(symbol)
        self.assertIn("letters", error)

    def test_unknown_currency_code_is_rejected(self):
        symbol, error = validate_symbol("ZZZUSD")
        self.assertIsNone(symbol)
        self.assertIn("ZZZ", error)

    def test_same_base_and_quote_is_rejected(self):
        symbol, error = validate_symbol("USDUSD")
        self.assertIsNone(symbol)
        self.assertIn("different", error)

    def test_duplicate_is_rejected(self):
        symbol, error = validate_symbol("eurusd", existing=["GBPUSD", "EURUSD"])
        self.assertIsNone(symbol)
        self.assertIn("already", error)

    def test_duplicate_check_is_case_insensitive(self):
        symbol, error = validate_symbol("EURUSD", existing=["eurusd"])
        self.assertIsNone(symbol)

    def test_different_pair_with_shared_currency_is_allowed(self):
        self.assertEqual(
            validate_symbol("EURGBP", existing=["EURUSD"]),
            ("EURGBP", None),
        )


if __name__ == "__main__":
    unittest.main()
