"""Validation for pair symbols. Pure functions, no Tk dependency."""
from __future__ import annotations

from config import CURRENCIES


def normalise_symbol(text: str) -> str:
    """Uppercase typed input and remove surrounding whitespace."""
    return (text or "").strip().upper()


def validate_symbol(text: str, existing=()) -> tuple[str | None, str | None]:
    """Check a typed symbol.

    Returns (symbol, None) when valid, or (None, friendly_error) when not.
    `existing` is any iterable of symbols already on the board.
    """
    symbol = normalise_symbol(text)

    if not symbol:
        return None, "Enter a symbol, for example EURUSD."

    if not symbol.isalpha():
        return None, "Use letters only, for example EURUSD (no numbers or spaces)."

    if len(symbol) != 6:
        return None, "A symbol must be exactly 6 letters, for example EURUSD."

    base, quote = symbol[:3], symbol[3:]
    unknown = [code for code in (base, quote) if code not in CURRENCIES]
    if unknown:
        supported = ", ".join(sorted(CURRENCIES))
        return None, (
            f"Unknown currency code {', '.join(unknown)}. "
            f"Supported codes: {supported}."
        )

    if base == quote:
        return None, "Base and quote must be different currency codes."

    taken = {normalise_symbol(item) for item in existing}
    if symbol in taken:
        return None, f"{symbol} is already on the board."

    return symbol, None
