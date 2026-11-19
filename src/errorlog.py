"""Unexpected-error logging for a windowed (no console) build.

The log is written next to data.json, so it works both in normal mode
(%LOCALAPPDATA%\\PairBiasBoard) and in portable mode (<app folder>\\data).
Logging must never make the application crash: all I/O errors are swallowed.
"""
from __future__ import annotations

import os
import sys
import threading
import traceback
from datetime import datetime

from config import LOG_FILE_NAME, LOG_MAX_BYTES
from paths import data_directory, ensure_data_dir

_LOCK = threading.Lock()


def log_path() -> str:
    """Return the log file path for the current storage mode."""
    return os.path.join(data_directory(), LOG_FILE_NAME)


def write(message: str, exc_info=None) -> str | None:
    """Append a timestamped entry (and optional traceback). Return its path.

    Returns None if the log could not be written; callers must still be able
    to continue or exit quietly. ``exc_info`` is a (type, value, tb) tuple.
    """
    lines = [f"{datetime.now().isoformat(timespec='seconds')} {message.strip()}"]
    if exc_info is not None:
        lines.append("".join(traceback.format_exception(*exc_info)).rstrip())
    path = log_path()
    try:
        ensure_data_dir(os.path.dirname(os.path.abspath(path)))
        with _LOCK:
            if os.path.isfile(path) and os.path.getsize(path) > LOG_MAX_BYTES:
                try:
                    os.replace(path, path + ".1")
                except OSError:
                    pass  # keep appending to the existing log if rotation fails
            with open(path, "a", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n\n")
        return path
    except (OSError, ValueError):
        return None


def _show_error_dialog(message: str, path: str | None) -> None:
    """Best-effort dialog so a silent windowed crash is still visible."""
    try:
        from tkinter import messagebox
        detail = f"\n\nLog file:\n{path}" if path else "\n\nNo log file could be written."
        messagebox.showerror("Pair Bias Board - unexpected error", message + detail)
    except Exception:
        pass  # no display available: the log entry is the fallback


def report_unexpected(exc: BaseException, context: str = "Unexpected error") -> None:
    """Log an exception and tell the user, without a console window."""
    info = (type(exc), exc, exc.__traceback__)
    path = write(f"{context}: {type(exc).__name__}: {exc}", info)
    _show_error_dialog(f"{context}:\n{type(exc).__name__}: {exc}", path)


def install_global_handler() -> None:
    """Log errors that escape the normal try/except (e.g. other threads)."""
    def hook(exc_type, exc, tb) -> None:
        try:
            write(
                f"Unhandled error: {exc_type.__name__}: {exc}",
                (exc_type, exc, tb),
            )
        except Exception:
            pass
    sys.excepthook = hook


def install_tk_handler(root) -> None:
    """Log errors raised inside Tk event handlers instead of printing them."""
    def handler(exc_type, exc, tb) -> None:
        path = write(
            f"Tk callback error: {exc_type.__name__}: {exc}",
            (exc_type, exc, tb),
        )
        _show_error_dialog(f"A problem occurred:\n{type(exc).__name__}: {exc}", path)
    root.report_callback_exception = handler
