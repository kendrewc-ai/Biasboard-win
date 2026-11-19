"""Small pure helpers for window layout, note fitting and slider positions."""
from __future__ import annotations

import re

_GEOMETRY = re.compile(r"^(\d+)x(\d+)([+-]\d+)([+-]\d+)$")


def parse_geometry(text: str) -> tuple[int, int, int, int] | None:
    """Parse Tk geometry 'WxH+X+Y'. Negative offsets are allowed."""
    match = _GEOMETRY.match((text or "").strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def format_geometry(width: int, height: int, x: int, y: int) -> str:
    return f"{width}x{height}+{x}+{y}"


def clamp_geometry(text: str, screen_w: int, screen_h: int,
                   min_w: int, min_h: int) -> str:
    """Repair a saved window position so some of the window is on screen."""
    parsed = parse_geometry(text)
    if parsed is None:
        return ""

    width, height, x, y = parsed
    width = min(max(width, min_w), max(200, screen_w - 16))
    height = min(max(height, min_h), max(160, screen_h - 16))
    width = min(width, screen_w)
    height = min(height, screen_h)

    if x < 0 or x > screen_w - 80:
        x = 40
    if y < 0 or y > screen_h - 40:
        y = 40
    x = max(0, min(x, screen_w - width))
    y = max(0, min(y, screen_h - height))
    return format_geometry(width, height, x, y)


def fit_text(text: str, font, max_px: int) -> str:
    """Shorten a note to fit `max_px`, adding a visible ellipsis."""
    if not text:
        return ""
    if font.measure(text) <= max_px:
        return text
    for length in range(len(text), 0, -1):
        candidate = text[:length].rstrip() + "…"
        if font.measure(candidate) <= max_px:
            return candidate
    return "…"


def position_x(index: int, width: int, pad: int) -> float:
    """Centre x of one of the six slider positions."""
    return pad + (width - 2 * pad) * index / 5


def nearest_index(x: float, width: int, pad: int) -> int:
    """Closest slider position, clamped to 0..5; ties choose the right one."""
    best = 0
    best_distance = float("inf")
    for index in range(6):
        distance = abs(x - position_x(index, width, pad))
        if distance <= best_distance:
            best, best_distance = index, distance
    return best


def ease_out(t: float) -> float:
    """Fast-start, soft-land easing for the short knob animation."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def fill_span(index: int, width: int, pad: int) -> tuple[float, float]:
    """Slider colour always grows out of Neutral (index 2).

    Bearish states draw leftwards from N, bullish states draw rightwards.
    """
    origin = position_x(2, width, pad)
    return origin, position_x(index, width, pad)


def scrollbar_thumb(height: int, start: float, end: float,
                    min_len: int = 28) -> tuple[float, float]:
    """Top and bottom of a thin overlay scrollbar thumb."""
    height = max(0, height)
    span = max(0.0, min(1.0, end - start))
    if span >= 1.0 or height == 0:
        return 0, height
    length = min(height, max(min_len, height * span))
    top = (height - length) * (start / max(1e-9, 1.0 - span))
    top = max(0.0, min(height - length, top))
    return top, top + length
