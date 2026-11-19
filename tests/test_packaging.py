"""Regression checks for the icon and the windowed build configuration."""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _source(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as handle:
        return handle.read()


class TestIconAssets(unittest.TestCase):
    def test_original_png_is_kept(self):
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "icon.png")))

    def test_ico_exists_and_has_a_valid_header(self):
        path = os.path.join(ROOT, "icon.ico")
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as handle:
            header = handle.read(6)
        self.assertEqual(header[:4], b"\x00\x00\x01\x00")  # ICO format
        self.assertGreater(header[4], 0)  # at least one image entry


class TestBuildConfiguration(unittest.TestCase):
    def test_build_script_uses_windowed_onefile_and_icon(self):
        source = _source("build.py")
        self.assertIn('"--onefile"', source)
        self.assertIn('"--windowed"', source)
        self.assertIn('"--icon"', source)
        self.assertIn('"--add-data"', source)
        self.assertIn('"--paths"', source)

    def test_build_script_uses_project_relative_paths(self):
        source = _source("build.py")
        self.assertIn("Path(__file__).resolve().parent", source)
        self.assertNotIn("C:\\\\", source)

    def test_entry_point_logs_errors_instead_of_printing_them(self):
        source = _source("main.py")
        self.assertIn("errorlog.install_global_handler()", source)
        self.assertIn("errorlog.install_tk_handler", source)
        self.assertIn("errorlog.report_unexpected", source)

    def test_window_sets_the_ico_icon(self):
        source = _source(os.path.join("src", "app.py"))
        self.assertIn("resource_path(ICON_FILE_NAME)", source)
        self.assertIn("iconbitmap", source)


if __name__ == "__main__":
    unittest.main()
