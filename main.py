"""Pair Bias Board - entry point.

Run from this folder with:  python main.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if os.path.isdir(SRC) and SRC not in sys.path:
    # Source checkout: import from the folder next to this script.
    # A frozen executable already has its modules bundled, so skip this.
    sys.path.insert(0, SRC)

from config import APP_USER_MODEL_ID  # noqa: E402
import errorlog  # noqa: E402
from app import App  # noqa: E402


def _set_windows_app_id() -> None:
    """Group the window under one taskbar/Start entry on Windows."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID
        )
    except Exception:
        pass  # cosmetic only; never block startup


def main() -> int:
    errorlog.install_global_handler()
    _set_windows_app_id()
    try:
        app = App()
    except Exception as exc:
        errorlog.report_unexpected(exc, context="Could not start the app")
        return 1

    errorlog.install_tk_handler(app.root)
    try:
        app.run()
    except Exception as exc:
        errorlog.report_unexpected(exc, context="The app stopped unexpectedly")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

