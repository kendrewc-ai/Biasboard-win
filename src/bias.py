"""Currency bias summary built only from manually chosen, fresh biases.

This is a visual summary of subjective bias. It is NOT position size,
exposure, or a trading signal.
"""
from __future__ import annotations

from config import STALE_AFTER_HOURS
from states import state_by_key
from timeutil import is_stale, utc_now

CONCENTRATION_LIMIT = 3


def currency_bias_summary(pairs, now=None, hours=STALE_AFTER_HOURS) -> dict:
    """Sum weighted contributions per currency.

    `pairs` items need: symbol (6 chars), state (short key), updated_at.
    Neutral, No Trade, stale and invalid rows are skipped and listed in
    `ignored`. Base gets the state score, quote gets the opposite.
    """
    if now is None:
        now = utc_now()

    totals: dict[str, dict] = {}
    ignored: list[str] = []

    for item in pairs:
        # Accept either Pair objects from the app or plain dicts in tests.
        item = item if isinstance(item, dict) else item.to_dict()
        symbol = (item.get("symbol") or "").strip().upper()
        try:
            state = state_by_key(item.get("state"))
        except ValueError:
            state = None

        score = state["score"] if state else None
        unreadable = len(symbol) != 6
        if (unreadable or score is None or score == 0
                or is_stale(item.get("updated_at", ""), now=now, hours=hours)):
            ignored.append(symbol or "(unnamed pair)")
            continue

        base, quote = symbol[:3], symbol[3:]
        for code, contribution in ((base, score), (quote, -score)):
            entry = totals.setdefault(code, {"net": 0, "contributions": []})
            entry["net"] += contribution
            entry["contributions"].append((symbol, contribution))

    currencies: dict[str, dict] = {}
    conflicts: list[str] = []
    concentrated: list[str] = []

    for code in sorted(totals):
        entry = totals[code]
        values = [value for _, value in entry["contributions"]]
        conflict = any(v > 0 for v in values) and any(v < 0 for v in values)
        concentration = abs(entry["net"]) >= CONCENTRATION_LIMIT
        conflict_pairs = (
            sorted({symbol for symbol, _ in entry["contributions"]})
            if conflict else []
        )
        currencies[code] = {
            "net": entry["net"],
            "contributions": entry["contributions"],
            "conflict": conflict,
            "conflict_pairs": conflict_pairs,
            "concentration": concentration,
        }
        if conflict:
            conflicts.append(code)
        if concentration:
            concentrated.append(code)

    return {
        "currencies": currencies,
        "conflicts": conflicts,
        "concentrated": concentrated,
        "ignored": ignored,
    }
