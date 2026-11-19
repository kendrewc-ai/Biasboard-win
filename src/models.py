"""One pair of the board. Plain data, no Tk dependency."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from config import MAX_NOTE_CHARS
from states import DEFAULT_STATE, STATE_KEYS
from timeutil import to_iso, utc_now
from validation import normalise_symbol


@dataclass
class Pair:
    id: str
    symbol: str
    state: str = DEFAULT_STATE
    updated_at: str = field(default_factory=lambda: to_iso(utc_now()))
    note: str = ""
    visible: bool = True

    @classmethod
    def new(cls, symbol: str) -> "Pair":
        """Create a fresh pair with a stable unique id and Neutral bias."""
        return cls(id=uuid.uuid4().hex, symbol=normalise_symbol(symbol))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "state": self.state,
            "updated_at": self.updated_at,
            "note": self.note,
            "visible": self.visible,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "Pair":
        """Read a saved pair defensively so one bad field cannot break the app."""
        raw = raw if isinstance(raw, dict) else {}
        state = raw.get("state")
        if state not in STATE_KEYS:
            state = DEFAULT_STATE
        return cls(
            id=str(raw.get("id") or uuid.uuid4().hex),
            symbol=normalise_symbol(str(raw.get("symbol") or "")),
            state=state,
            updated_at=str(raw.get("updated_at") or to_iso(utc_now())),
            note=str(raw.get("note") or "")[:MAX_NOTE_CHARS],
            visible=bool(raw.get("visible", True)),
        )
