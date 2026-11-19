"""The six fixed bias states, in the exact left-to-right slider order.

A state is a plain dict so it can be saved/loaded without special code.
`score` is used only by the currency bias summary; No Trade has no score.
"""
from __future__ import annotations

STATES = [
    {"key": "VB",  "short": "VB",  "name": "Very Bearish", "color": "#B4443D",
     "kind": "bearish",  "score": -2},
    {"key": "B",   "short": "B",   "name": "Bearish",      "color": "#D9776F",
     "kind": "bearish",  "score": -1},
    {"key": "N",   "short": "N",   "name": "Neutral",      "color": "#7F7F86",
     "kind": "neutral",  "score": 0},
    {"key": "Bu",  "short": "Bu",  "name": "Bullish",      "color": "#4A9D78",
     "kind": "bullish",  "score": 1},
    {"key": "VBu", "short": "VBu", "name": "Very Bullish", "color": "#2F7D59",
     "kind": "bullish",  "score": 2},
    {"key": "NT",  "short": "NT",  "name": "No Trade",     "color": "#858194",
     "kind": "no_trade", "score": None},
]

STATE_KEYS = tuple(state["key"] for state in STATES)
STATE_COUNT = len(STATES)
DEFAULT_STATE = "N"

_BY_KEY = {state["key"]: state for state in STATES}


def state_by_key(key: str) -> dict:
    """Return the state dict for a short key such as 'VBu'."""
    try:
        return _BY_KEY[key]
    except KeyError:
        raise ValueError(f"Unknown bias state: {key!r}") from None


def state_at_index(index: int) -> dict:
    """Return the state at a slider position (0 = far left)."""
    return STATES[index]


def index_of_key(key: str) -> int:
    """Return the slider position for a short key such as 'VBu'."""
    try:
        return STATE_KEYS.index(key)
    except ValueError:
        raise ValueError(f"Unknown bias state: {key!r}") from None


def key_at_index(index: int) -> str:
    """Return the short key at a slider position."""
    return STATES[index]["key"]
