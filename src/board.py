"""The compact, resizable board view."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from config import (
    FONT_ICON,
    FONT_MONO,
    FONT_MONO_SMALL,
    FONT_PLUS,
    FONT_TITLE,
    FONT_UI,
    FONT_UI_SMALL,
    NOTE_WIDTH,
    REFRESH_NOTE_MS,
    ROW_HEIGHT,
    THEME,
    TIME_WIDTH,
)
from geometry import fit_text
from iconbutton import IconButton
from slider import SixStateSlider
from timeutil import age_text, is_stale
from tooltip import Tooltip


class ScrollArea(tk.Frame):
    """Vertical scroll area that keeps rows full width."""

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg"])
        self.canvas = tk.Canvas(self, bg=THEME["bg"], highlightthickness=0, bd=0)
        self.bar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=THEME["bg"])
        self._window = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.inner.bind("<MouseWheel>", self._on_wheel)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.bar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_inner_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self._window, width=event.width)

    @staticmethod
    def _on_wheel(event):
        step = -1 if event.delta > 0 else 1
        master = event.widget
        while not isinstance(master, ScrollArea) and master.master:
            master = master.master
        if isinstance(master, ScrollArea):
            master.canvas.yview_scroll(step, "units")


class BoardView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=THEME["bg"])
        self.app = app
        self.rows: dict[str, dict] = {}
        self.note_font = tkfont.Font(
            family=FONT_UI_SMALL[0], size=FONT_UI_SMALL[1]
        )

        header = tk.Frame(self, bg=THEME["panel"], height=48)
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Frame(header, bg=THEME["border"], height=1).pack(
            fill=tk.X, side=tk.BOTTOM
        )
        tk.Label(
            header, text="Pair Bias Board", bg=THEME["panel"], fg=THEME["text"],
            font=FONT_TITLE, padx=18,
        ).pack(side=tk.LEFT)

        self.top_button = tk.Button(
            header, text="On Top", command=app.toggle_topmost,
            bg=THEME["panel"], fg=THEME["muted"], relief=tk.FLAT, bd=0,
            font=FONT_UI_SMALL, padx=10, cursor="hand2",
            activebackground=THEME["panel_alt"],
        )
        self.top_button.pack(side=tk.RIGHT, pady=8, padx=(0, 14))

        IconButton(
            header, "+", app.open_add_pair, bg=THEME["panel"],
            fg=THEME["accent"], font=FONT_PLUS,
        ).pack(side=tk.RIGHT, pady=8, padx=(0, 4))
        IconButton(
            header, "⚙", app.open_manage, bg=THEME["panel"],
            fg=THEME["muted"], font=FONT_ICON,
        ).pack(side=tk.RIGHT, pady=8, padx=(0, 2))

        self.scroll = ScrollArea(self)
        self.scroll.pack(fill=tk.BOTH, expand=True)

        self._note_refresh_loop()

    # ---- rows ------------------------------------------------------------
    def rebuild(self, pairs):
        for row in self.rows.values():
            row["frame"].destroy()
        self.rows.clear()

        if not pairs:
            empty = tk.Label(
                self.scroll.inner,
                text="No pairs on the board. Click + to add one.",
                bg=THEME["bg"], fg=THEME["muted"], font=FONT_UI,
            )
            empty.pack(pady=28)
            self.rows["__empty__"] = {"frame": empty}
            return

        for pair in pairs:
            self.rows[pair.id] = self._make_row(pair)
        self.refresh(pairs)

    def _make_row(self, pair):
        frame = tk.Frame(
            self.scroll.inner, bg=THEME["panel"], height=ROW_HEIGHT,
            highlightthickness=1, highlightbackground=THEME["border"], bd=0,
        )
        frame.pack(fill=tk.X, padx=10, pady=3)
        frame.pack_propagate(False)
        row = {}

        ticker = tk.Label(
            frame, text=pair.symbol, width=9, anchor="w",
            bg=THEME["panel"], fg=THEME["text"],
            font=FONT_MONO, padx=10,
        )
        ticker.pack(side=tk.LEFT)

        slider = SixStateSlider(
            frame, pair.state,
            lambda key, pair_id=pair.id, r=row: self.app.set_state(
                pair_id, key, source=r.get("slider")
            ),
        )
        slider.pack(side=tk.LEFT, padx=(4, 8))

        age = tk.Label(
            frame, text="", width=TIME_WIDTH // 8, anchor="w",
            bg=THEME["panel"], fg=THEME["muted"], font=FONT_UI_SMALL,
        )
        age.pack(side=tk.LEFT)

        note = tk.Label(
            frame, text="", anchor="w", bg=THEME["panel"],
            fg=THEME["muted"], font=self.note_font,
        )
        note.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tooltip = Tooltip(note, lambda p=pair: p.note or "(no note)")

        row.update({
            "frame": frame, "ticker": ticker, "slider": slider,
            "age": age, "note": note, "tooltip": tooltip,
        })
        return row

    # ---- live updates ----------------------------------------------------
    def refresh(self, pairs, skip_slider=None):
        """Update text only; never recreate sliders (keeps animation smooth)."""
        for pair in pairs:
            row = self.rows.get(pair.id)
            if row is None:
                continue
            slider = row["slider"]
            if slider is not skip_slider and not slider.is_busy():
                slider.set_state(pair.state)
            stale = is_stale(pair.updated_at)
            row["age"].configure(
                text=age_text(pair.updated_at),
                fg=THEME["warning"] if stale else THEME["muted"],
            )
            row["ticker"].configure(
                fg=THEME["warning"] if stale else THEME["text"]
            )
            row["note"].configure(
                text=fit_text(pair.note, self.note_font, NOTE_WIDTH)
            )

    def set_top_button(self, enabled: bool):
        self.top_button.configure(
            text="On Top •" if enabled else "On Top",
            fg=THEME["accent"] if enabled else THEME["muted"],
        )

    def _note_refresh_loop(self):
        """Re-measure note truncation after a resize."""
        if self.winfo_exists():
            pairs = self.app.data["pairs"]
            for pair in pairs:
                row = self.rows.get(pair.id)
                if row:
                    row["note"].configure(
                        text=fit_text(pair.note, self.note_font, NOTE_WIDTH)
                    )
            self.after(REFRESH_NOTE_MS, self._note_refresh_loop)
