"""Checks for local JSON persistence and the pair record."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import Pair  # noqa: E402
from storage import StorageError, default_data, load_data, save_data  # noqa: E402


class TestPair(unittest.TestCase):
    def test_new_pair_starts_neutral_and_visible(self):
        item = Pair.new("EURUSD")
        self.assertEqual(item.symbol, "EURUSD")
        self.assertEqual(item.state, "N")
        self.assertTrue(item.visible)

    def test_each_pair_gets_a_unique_id(self):
        self.assertNotEqual(Pair.new("EURUSD").id, Pair.new("GBPUSD").id)

    def test_dict_round_trip(self):
        item = Pair.new("USDJPY")
        item.note = "waiting for FVG"
        item.state = "Bu"
        item.visible = False
        self.assertEqual(Pair.from_dict(item.to_dict()).to_dict(), item.to_dict())

    def test_bad_state_in_loaded_record_falls_back_to_neutral(self):
        raw = Pair.new("EURUSD").to_dict()
        raw["state"] = "GARBAGE"
        self.assertEqual(Pair.from_dict(raw).state, "N")


class TestDefaultData(unittest.TestCase):
    def test_first_launch_has_only_usdjpy(self):
        data = default_data()
        self.assertEqual([p.symbol for p in data["pairs"]], ["USDJPY"])
        self.assertEqual(data["pairs"][0].state, "N")

    def test_defaults_have_no_topmost_and_no_geometry(self):
        data = default_data()
        self.assertFalse(data["settings"]["always_on_top"])
        self.assertEqual(data["settings"]["geometry"], "")


class TestSaveAndLoad(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "data.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_file_gives_defaults_without_warning(self):
        data, warning = load_data(self.path)
        self.assertEqual([p.symbol for p in data["pairs"]], ["USDJPY"])
        self.assertIsNone(warning)

    def test_round_trip_keeps_order_notes_visibility_and_settings(self):
        data = default_data()
        data["pairs"].append(Pair.new("EURUSD"))
        data["pairs"][0].note = "5h level"
        data["pairs"][1].visible = False
        data["pairs"][1].state = "VBu"
        data["settings"]["always_on_top"] = True
        data["settings"]["geometry"] = "900x420+40+60"

        save_data(data, self.path)
        loaded, warning = load_data(self.path)

        self.assertIsNone(warning)
        self.assertEqual([p.symbol for p in loaded["pairs"]], ["USDJPY", "EURUSD"])
        self.assertEqual(loaded["pairs"][0].note, "5h level")
        self.assertFalse(loaded["pairs"][1].visible)
        self.assertEqual(loaded["pairs"][1].state, "VBu")
        self.assertTrue(loaded["settings"]["always_on_top"])
        self.assertEqual(loaded["settings"]["geometry"], "900x420+40+60")

    def test_corrupt_file_is_backed_up_and_defaults_are_used(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{ this is not json ")

        data, warning = load_data(self.path)

        self.assertEqual([p.symbol for p in data["pairs"]], ["USDJPY"])
        self.assertIsNotNone(warning)
        self.assertIn("backup", warning.lower())
        backups = [n for n in os.listdir(self.tmp.name) if "corrupt" in n]
        self.assertEqual(len(backups), 1)
        with open(os.path.join(self.tmp.name, backups[0]), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "{ this is not json ")

    def test_duplicate_symbols_are_dropped_on_load(self):
        raw = default_data()
        raw["pairs"].append(Pair.new("USDJPY"))
        raw["pairs"].append(Pair.new("GBPUSD"))
        save_data(raw, self.path)

        loaded, _ = load_data(self.path)
        self.assertEqual([p.symbol for p in loaded["pairs"]], ["USDJPY", "GBPUSD"])

    def test_missing_settings_use_defaults(self):
        raw = default_data()
        raw.pop("settings")
        save_data(raw, self.path)
        loaded, _ = load_data(self.path)
        self.assertFalse(loaded["settings"]["always_on_top"])

    def test_failed_save_raises_storage_error(self):
        data = default_data()
        with self.assertRaises(StorageError):
            save_data(data, self.tmp.name)  # a directory, not a file

    def test_saved_file_is_valid_json(self):
        save_data(default_data(), self.path)
        with open(self.path, encoding="utf-8") as handle:
            content = json.load(handle)
        self.assertEqual(content["version"], 1)


if __name__ == "__main__":
    unittest.main()
