"""Path resolution that works from source or from a frozen executable.

No absolute path is stored in the code. Everything is derived from the
location of this file or, for a packaged app, from the executable.
"""
from __future__ import annotations

import os
import sys

from config import APP_DIR_NAME

PORTABLE_MARKER = "PORTABLE"
PORTABLE_DATA_DIR = "data"


def is_frozen() -> bool:
    """True when running as a PyInstaller-style packaged executable."""
    return bool(getattr(sys, "frozen", False))


def app_root() -> str:
    """Folder that holds the app (project root when running from source)."""
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def portable_marker(root: str | None = None) -> str:
    return os.path.join(root or app_root(), PORTABLE_MARKER)


def is_portable(root: str | None = None) -> bool:
    """Opt-in mode: a PORTABLE file next to the app means data travels with it."""
    return os.path.isfile(portable_marker(root))


def data_directory(root: str | None = None,
                   local_app_data: str | None = None) -> str:
    """Return the folder that holds data.json.

    Default is a per-user application data folder, never the install folder.
    With a PORTABLE marker, use <app>/data so the whole folder can be copied
    to another drive or computer without losing the board's data.
    """
    root = root or app_root()
    if is_portable(root):
        return os.path.join(root, PORTABLE_DATA_DIR)
    base = local_app_data
    if base is None:
        base = (
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or os.path.join(os.path.expanduser("~"), ".pairbiasboard")
        )
    return os.path.join(base, APP_DIR_NAME)


def ensure_data_dir(path: str) -> None:
    """Create a data folder if it does not exist yet."""
    os.makedirs(path, exist_ok=True)
