"""Build the native-looking Windows EXE from this project folder.

Usage:  python build.py

All paths are derived from this file, so the build works after moving the
project to another folder or drive. Requires PyInstaller; Pillow is only
needed if icon.ico has not been generated from the existing icon.png yet.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "Pair Bias Board"
ICON_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def ensure_icon() -> Path:
    """Return icon.ico, converting the existing PNG artwork only if needed."""
    ico = ROOT / "icon.ico"
    if ico.is_file():
        return ico
    png = ROOT / "icon.png"
    if not png.is_file():
        raise SystemExit(f"Missing icon source: {png}")
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("icon.ico is missing; install Pillow to convert icon.png.")
    with Image.open(png) as image:
        image.convert("RGBA").save(ico, format="ICO", sizes=ICON_SIZES)
    print(f"Created {ico.name} from {png.name} (same artwork, ICO format).")
    return ico


def main() -> int:
    icon = ensure_icon()
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile",              # one portable EXE, easy to copy anywhere
        "--windowed",             # no CMD / console window on launch
        "--name", APP_NAME,
        "--icon", str(icon),      # Explorer, taskbar and Start menu icon
        "--add-data", f"{icon}{os.pathsep}.",  # icon for the Tk window too
        "--paths", str(ROOT / "src"),  # flat modules imported by main.py
        str(ROOT / "main.py"),
    ]
    print("Building:", " ".join(command))
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        return result.returncode
    exe = ROOT / "dist" / f"{APP_NAME}.exe"
    print(f"\nDone: {exe}")
    print("Data and error log: %LOCALAPPDATA%\\PairBiasBoard\\ "
          "(or <app folder>\\data with a PORTABLE marker).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
