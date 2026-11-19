"""The compact, resizable board view."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from config import (
    FONT_ICON,
    FONT_MONO,
    FONT_MONO_SMALL,
    FONT_PLUS,
    FONT_TITLE,
    FONT_UI,
    FONT_UI_SMALL,
    ROW_HEIGHT,
    THEME,
    TIME_WIDTH,
)
from geometry import scrollbar_thumb
from iconbutton import IconButton
from slider import SixStateSlider
from timeutil import age_text, is_stale
from tooltip import Tooltip


class MinimalScrollbar(tk.Canvas):
    """One thin grey line on white: no arrows, no trough, no chunky handle."""

    def __init__(self, parent, command):
        super().__init__(
            parent, width=10, bg=THEME["panel"],
            highlightthickness=0, bd=0, cursor="hand2",
        )
        self._command = command
        self._start = 0.0
        self._end = 1.0
        self._dragging = False
        self._offset = 0
        self._thumb = self.create_line(
            5, 0, 5, 0, fill="#C7C7CC", width=6, capstyle=tk.ROUND,
        )
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_motion)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda _e: self._draw())

    def set(self, first, last):
        """Tk scroll command: receive visible fraction (first, last)."""
        self._start, self._end = float(first), float(last)
        self._draw()

    def _draw(self):
        top, bottom = scrollbar_thumb(
            self.winfo_height(), self._start, self._end
        )
        self.coords(self._thumb, 5, top, 5, bottom)

    def _on_press(self, event):
        top, bottom = scrollbar_thumb(
            self.winfo_height(), self._start, self._end
        )
        if top <= event.y <= bottom:
            self._dragging = True
            self._offset = event.y - top
        else:
            self._jump(event.y - (bottom - top) / 2)

    def _on_motion(self, event):
        if self._dragging:
            self._jump(event.y - self._offset)

    def _on_release(self, _event):
        self._dragging = False

    def _jump(self, y):
        height = self.winfo_height()
        top, bottom = scrollbar_thumb(height, self._start, self._end)
        length = bottom - top
        fraction = (y - length / 2) / max(1, height - length)
        self._command("moveto", max(0.0, min(1.0, fraction)))


class ScrollArea(tk.Frame):
    """Vertical scroll area that keeps rows full width."""

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg"])
        self.canvas = tk.Canvas(self, bg=THEME["bg"], highlightthickness=0, bd=0)
        self.bar = MinimalScrollbar(self, self.canvas.yview)
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

    def _on_inner_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._update_bar()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self._window, width=event.width)
        self._update_bar()

    def _update_bar(self):
        """Show the thin bar only when the rows do not fit."""
        region = self.canvas.bbox("all")
        if region and region[3] - region[1] > self.canvas.winfo_height() + 2:
            self.bar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.bar.pack_forget()

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

        note_var = tk.StringVar(value=pair.note)
        note = tk.Entry(
            frame, textvariable=note_var, bg=THEME["panel"],
            fg=THEME["muted"], relief=tk.FLAT,
            highlightthickness=1, highlightbackground=THEME["border"],
            font=self.note_font, width=22,
        )
        note.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), pady=6)
        note.bind(
            "<KeyRelease>",
            lambda _e, i=pair.id, v=note_var: self._note_changed(i, v),
        )
        note.bind("<Return>", lambda _e: self._note_done())
        note.bind("<FocusOut>", lambda _e: self._note_done())
        tooltip = Tooltip(note, lambda v=note_var: v.get() or "(no note)")

        row.update({
            "frame": frame, "ticker": ticker, "slider": slider,
            "age": age, "note": note, "note_var": note_var,
            "tooltip": tooltip,
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
            note_var = row.get("note_var")
            if (note_var is not None and row["note"] is not self.focus_get()
                    and note_var.get() != pair.note):
                note_var.set(pair.note)

    def _note_changed(self, pair_id, var):
        self.app.set_note_live(pair_id, var.get())

    def _note_done(self):
        self.app.flush_note_save()
        window = self.app.manage_window
        if window is not None and window.winfo_exists():
            window.refresh()

    def set_top_button(self, enabled: bool):
        self.top_button.configure(
            text="On Top •" if enabled else "On Top",
            fg=THEME["accent"] if enabled else THEME["muted"],
        )

