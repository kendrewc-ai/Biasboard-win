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

from app import App  # noqa: E402


def main():
    App().run()


if __name__ == "__main__":
    main()
