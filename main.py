"""Pair Bias Board - entry point.

Run from this folder with:  python main.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from app import App  # noqa: E402


def main():
    App().run()


if __name__ == "__main__":
    main()
