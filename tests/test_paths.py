"""Checks for portable path resolution."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import APP_DIR_NAME  # noqa: E402
from paths import (  # noqa: E402
    PORTABLE_MARKER,
    app_root,
    data_directory,
    ensure_data_dir,
    is_frozen,
    is_portable,
)


class TestAppRoot(unittest.TestCase):
    def test_root_is_discovered_from_source_location(self):
        self.assertTrue(os.path.isfile(os.path.join(app_root(), "main.py")))

    def test_root_contains_the_src_package(self):
        self.assertTrue(os.path.isdir(os.path.join(app_root(), "src")))

    def test_frozen_flag_is_a_boolean(self):
        self.assertIsInstance(is_frozen(), bool)


class TestPortableMode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_storage_uses_user_app_data(self):
        result = data_directory(root=self.root, local_app_data="X:/Users/Me/AppData")
        self.assertEqual(result, os.path.join("X:/Users/Me/AppData", APP_DIR_NAME))

    def test_no_marker_means_not_portable(self):
        self.assertFalse(is_portable(self.root))

    def test_marker_enables_portable_storage_in_app_folder(self):
        with open(os.path.join(self.root, PORTABLE_MARKER), "w") as handle:
            handle.write("")
        self.assertTrue(is_portable(self.root))
        result = data_directory(root=self.root, local_app_data="X:/Users/Me/AppData")
        self.assertEqual(result, os.path.join(self.root, "data"))

    def test_marker_is_ignored_in_a_different_folder(self):
        with open(os.path.join(self.root, PORTABLE_MARKER), "w") as handle:
            handle.write("")
        other = tempfile.mkdtemp()
        self.assertFalse(is_portable(other))
        result = data_directory(root=other, local_app_data="X:/Users/Me/AppData")
        self.assertEqual(result, os.path.join("X:/Users/Me/AppData", APP_DIR_NAME))

    def test_missing_directory_is_created(self):
        target = os.path.join(self.root, "nested", "data")
        ensure_data_dir(target)
        self.assertTrue(os.path.isdir(target))


if __name__ == "__main__":
    unittest.main()
