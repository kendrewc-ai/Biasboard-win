"""Local JSON storage. No cloud, no telemetry, no network calls.

Writes go to a temporary file and are then atomically renamed, so a crash
cannot leave a half-written data file.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from config import APP_DIR_NAME, DATA_FILE_NAME, DATA_VERSION, DEFAULT_SYMBOL
from models import Pair
from validation import normalise_symbol


class StorageError(Exception):
    """Raised when data cannot be read or written safely."""


def app_data_dir() -> str:
    """Per-user Windows application data folder (never the install folder)."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if not base:  # non-Windows fallback, e.g. while running tests elsewhere
        base = os.path.join(os.path.expanduser("~"), ".pairbiasboard")
    return os.path.join(base, APP_DIR_NAME)


def data_path(path: str | None = None) -> str:
    return path or os.path.join(app_data_dir(), DATA_FILE_NAME)


def default_data() -> dict:
    """State used on the very first launch only."""
    return {
        "version": DATA_VERSION,
        "pairs": [Pair.new(DEFAULT_SYMBOL)],
        "settings": {"always_on_top": False, "geometry": ""},
    }


def _serialize(data: dict) -> dict:
    settings = data.get("settings") or {}
    return {
        "version": DATA_VERSION,
        "pairs": [pair.to_dict() for pair in data["pairs"]],
        "settings": {
            "always_on_top": bool(settings.get("always_on_top", False)),
            "geometry": str(settings.get("geometry", "")),
        },
    }


def _deserialize(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise StorageError("The data file does not contain a settings object.")

    pairs: list[Pair] = []
    seen_symbols: set[str] = set()
    seen_ids: set[str] = set()
    for item in raw.get("pairs", []):
        pair = Pair.from_dict(item)
        if not pair.symbol or pair.symbol in seen_symbols:
            continue  # empty or duplicate symbol: skip, never duplicate a row
        if pair.id in seen_ids:
            pair.id = Pair.new(pair.symbol).id
        seen_symbols.add(pair.symbol)
        seen_ids.add(pair.id)
        pairs.append(pair)

    settings = raw.get("settings")
    settings = settings if isinstance(settings, dict) else {}
    return {
        "version": DATA_VERSION,
        "pairs": pairs,
        "settings": {
            "always_on_top": bool(settings.get("always_on_top", False)),
            "geometry": str(settings.get("geometry", "")),
        },
    }


def save_data(data: dict, path: str | None = None) -> None:
    """Atomically save data. Raises StorageError instead of losing anything."""
    target = data_path(path)
    temp = target + ".tmp"
    try:
        parent = os.path.dirname(os.path.abspath(target))
        os.makedirs(parent, exist_ok=True)
        with open(temp, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(_serialize(data), handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    except (OSError, TypeError, ValueError) as exc:
        try:
            if os.path.isfile(temp):
                os.remove(temp)
        except OSError:
            pass
        raise StorageError(
            f"Could not save your data to:\n{target}\n\n{exc}\n\n"
            "Your previous data file was left untouched."
        ) from exc


def load_data(path: str | None = None) -> tuple[dict, str | None]:
    """Return (data, warning). A corrupt file is backed up, never overwritten."""
    target = data_path(path)
    if not os.path.exists(target):
        return default_data(), None

    try:
        with open(target, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        raise StorageError(f"Could not read your data file:\n{target}\n\n{exc}") from exc

    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"{os.path.splitext(os.path.basename(target))[0]}"
        backup = os.path.join(
            os.path.dirname(os.path.abspath(target)),
            f"{name}.corrupt-{stamp}.json",
        )
        try:
            os.replace(target, backup)
        except OSError as exc:
            raise StorageError(
                f"The data file is damaged and a backup could not be made:\n"
                f"{target}\n\n{exc}"
            ) from exc
        return default_data(), (
            "Your data file could not be read. A backup was saved at:\n"
            f"{backup}\n\nA fresh board was started. You can inspect the "
            "backup and copy it back by hand."
        )

    return _deserialize(raw), None
