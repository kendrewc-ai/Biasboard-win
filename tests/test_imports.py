"""Headless import check: catches syntax and import errors in the GUI files."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestGuiModulesImport(unittest.TestCase):
    def test_every_module_imports_without_opening_a_window(self):
        import app  # noqa: F401
        import bias  # noqa: F401
        import board  # noqa: F401
        import geometry  # noqa: F401
        import manage  # noqa: F401
        import models  # noqa: F401
        import slider  # noqa: F401
        import storage  # noqa: F401
        import timeutil  # noqa: F401
        import tooltip  # noqa: F401
        import validation  # noqa: F401


if __name__ == "__main__":
    unittest.main()
