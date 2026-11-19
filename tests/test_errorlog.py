"""Checks for error logging in the windowed (no console) build."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import errorlog  # noqa: E402


class TestErrorLog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = mock.patch.object(
            errorlog, "data_directory", return_value=self.tmp.name
        )
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_log_path_uses_the_data_directory(self):
        self.assertEqual(
            errorlog.log_path(),
            os.path.join(self.tmp.name, errorlog.LOG_FILE_NAME),
        )

    def test_write_creates_a_timestamped_entry(self):
        path = errorlog.write("something broke")
        self.assertEqual(path, errorlog.log_path())
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("something broke", text)
        self.assertIn("T", text[:32])  # ISO timestamp

    def test_write_includes_traceback_when_given_exception_info(self):
        try:
            raise ValueError("bad value")
        except ValueError as exc:
            info = (type(exc), exc, exc.__traceback__)
            errorlog.write("callback failed", info)
        with open(errorlog.log_path(), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("Traceback", text)
        self.assertIn("ValueError: bad value", text)

    def test_log_rotates_when_it_gets_large(self):
        with mock.patch.object(errorlog, "LOG_MAX_BYTES", 20):
            errorlog.write("first long entry to force rotation")
            errorlog.write("second entry")
        self.assertTrue(os.path.isfile(errorlog.log_path() + ".1"))
        with open(errorlog.log_path(), encoding="utf-8") as handle:
            self.assertIn("second entry", handle.read())

    def test_report_unexpected_logs_the_exception(self):
        with mock.patch.object(errorlog, "_show_error_dialog") as dialog:
            errorlog.report_unexpected(RuntimeError("kaboom"), context="Startup")
        with open(errorlog.log_path(), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("Startup", text)
        self.assertIn("RuntimeError: kaboom", text)
        dialog.assert_called_once()

    def test_tk_handler_is_installed_and_logs(self):
        class FakeRoot:
            pass

        root = FakeRoot()
        with mock.patch.object(errorlog, "_show_error_dialog"):
            errorlog.install_tk_handler(root)
            root.report_callback_exception(
                TypeError, TypeError("bad event"), None
            )
        self.assertTrue(callable(root.report_callback_exception))
        with open(errorlog.log_path(), encoding="utf-8") as handle:
            self.assertIn("Tk callback error", handle.read())


if __name__ == "__main__":
    unittest.main()
