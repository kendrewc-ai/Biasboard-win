"""The compact, resizable board view."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from config import (
    CONTENT_WIDTH,
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
    """One thin grey line on white, for either axis."""

    def __init__(self, parent, command, orient="vertical"):
        self._orient = orient
        if orient == "vertical":
            super().__init__(
                parent, width=10, bg=THEME["panel"],
                highlightthickness=0, bd=0, cursor="hand2",
            )
        else:
            super().__init__(
                parent, height=10, bg=THEME["panel"],
                highlightthickness=0, bd=0, cursor="hand2",
            )
        self._command = command
        self._start = 0.0
        self._end = 1.0
        self._dragging = False
        self._offset = 0
        self._thumb = self.create_line(
            0, 0, 0, 0, fill="#C7C7CC", width=6, capstyle=tk.ROUND,
        )
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_motion)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda _e: self._draw())

    def _length(self):
        if self._orient == "vertical":
            return self.winfo_height()
        return self.winfo_width()

    def _position(self, event):
        return event.y if self._orient == "vertical" else event.x

    def set(self, first, last):
        """Tk scroll command: receive visible fraction (first, last)."""
        self._start, self._end = float(first), float(last)
        self._draw()

    def _draw(self):
        top, bottom = scrollbar_thumb(self._length(), self._start, self._end)
        if self._orient == "vertical":
            self.coords(self._thumb, 5, top, 5, bottom)
        else:
            self.coords(self._thumb, top, 5, bottom, 5)

    def _on_press(self, event):
        top, bottom = scrollbar_thumb(self._length(), self._start, self._end)
        position = self._position(event)
        self.grab_set()  # keep receiving motion even outside the thin bar
        if top <= position <= bottom:
            self._dragging = True
            self._offset = position - top
        else:
            self._jump(position - (bottom - top) / 2)
            self.grab_release()

    def _on_motion(self, event):
        if self._dragging:
            self._jump(self._position(event) - self._offset)

    def _on_release(self, _event):
        self._dragging = False
        if self.grab_current() is self:
            self.grab_release()

    def _jump(self, top):
        """Move so the thumb starts at `top` (pixels along the bar)."""
        length = self._length()
        _, bottom = scrollbar_thumb(length, self._start, self._end)
        fraction = top / max(1, length - bottom)
        self._command("moveto", max(0.0, min(1.0, fraction)))


class ScrollArea(tk.Frame):
    """Scrollable canvas with thin overlay bars on both axes."""

    def __init__(self, parent, content_width=CONTENT_WIDTH):
        super().__init__(parent, bg=THEME["bg"])
        self._content_width = content_width
        self.canvas = tk.Canvas(self, bg=THEME["bg"], highlightthickness=0, bd=0)
        self.vbar = MinimalScrollbar(self, self.canvas.yview, "vertical")
        self.hbar = MinimalScrollbar(self, self.canvas.xview, "horizontal")
        self.inner = tk.Frame(self.canvas, bg=THEME["bg"])
        self._window = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw", width=content_width
        )
        self.canvas.configure(
            yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set,
            yscrollincrement=24, xscrollincrement=40,
        )
        self._y_remainder = 0.0
        self._x_remainder = 0.0
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        # Wheel events go to the focused widget, so bind at the window level.
        # Each area ignores events that did not happen inside its own content.
        top = self.winfo_toplevel()
        top.bind("<MouseWheel>", self._on_wheel, add="+")
        top.bind("<Shift-MouseWheel>", self._on_shift_wheel, add="+")
        top.bind("<Button-4>", self._on_wheel_up, add="+")
        top.bind("<Button-5>", self._on_wheel_down, add="+")
        # Bars first, so the canvas takes whatever space is left.
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _on_inner_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._update_bars()

    def _on_canvas_configure(self, event):
        # Keep a stable content width; a narrower window scrolls sideways.
        width = max(self._content_width, event.width - 12)
        self.canvas.itemconfig(self._window, width=width)
        self._update_bars()

    def _update_bars(self):
        """Show each thin bar only when that axis has hidden content."""
        region = self.canvas.bbox("all")
        if not region:
            return
        needs_x = region[2] - region[0] > self.canvas.winfo_width() + 2
        needs_y = region[3] - region[1] > self.canvas.winfo_height() + 2
        x_packed = self.hbar.winfo_manager() == "pack"
        y_packed = self.vbar.winfo_manager() == "pack"
        if needs_x and not x_packed:
            self.hbar.pack(side=tk.BOTTOM, fill=tk.X, before=self.canvas)
        elif not needs_x and x_packed:
            self.hbar.pack_forget()
        if needs_y and not y_packed:
            self.vbar.pack(side=tk.RIGHT, fill=tk.Y, before=self.canvas)
        elif not needs_y and y_packed:
            self.vbar.pack_forget()

    def _contains(self, widget):
        """Is this event widget inside this scroll area?"""
        current = widget
        while current is not None:
            if current is self or current is self.canvas or current is self.inner:
                return True
            current = getattr(current, "master", None)
        return False

    def _on_wheel(self, event):
        if not self._contains(event.widget):
            return
        # Windows sends multiples of 120; touchpads send smaller deltas.
        amount = self._y_remainder + (getattr(event, "delta", 0) or 0) / 120.0
        steps = int(amount)
        self._y_remainder = amount - steps
        if steps:
            self.canvas.yview_scroll(-steps, "units")

    def _on_shift_wheel(self, event):
        if not self._contains(event.widget):
            return
        # Shift+wheel and hardware horizontal wheels both arrive here on Tk 8.6.10+.
        amount = self._x_remainder + (getattr(event, "delta", 0) or 0) / 120.0
        steps = int(amount)
        self._x_remainder = amount - steps
        if steps:
            self.canvas.xview_scroll(steps, "units")

    def _on_wheel_up(self, event):
        if self._contains(event.widget):
            self.canvas.yview_scroll(-1, "units")

    def _on_wheel_down(self, event):
        if self._contains(event.widget):
            self.canvas.yview_scroll(1, "units")


class BoardView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=THEME["bg"])
        self.app = app
        self.rows: dict[str, dict] = {}
        self.note_font = tkfont.Font(
            family=FONT_UI_SMALL[0], size=FONT_UI_SMALL[1]
        )

        # Fixed header: controls stay pinned to the window's top-right corner
        # and never move when the content scrolls or the window shrinks.
        self.header = tk.Frame(self, bg=THEME["panel"], height=48)
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.pack_propagate(False)
        tk.Frame(self.header, bg=THEME["border"], height=1).pack(
            fill=tk.X, side=tk.BOTTOM
        )

        self.top_button = tk.Button(
            self.header, text="On Top", command=app.toggle_topmost,
            bg=THEME["panel"], fg=THEME["muted"], relief=tk.FLAT, bd=0,
            font=FONT_UI_SMALL, padx=10, cursor="hand2",
            activebackground=THEME["panel_alt"],
        )
        self.top_button.pack(side=tk.RIGHT, pady=8, padx=(0, 14))

        IconButton(
            self.header, "+", app.open_add_pair, bg=THEME["panel"],
            fg=THEME["accent"], font=FONT_PLUS,
        ).pack(side=tk.RIGHT, pady=8, padx=(0, 4))
        IconButton(
            self.header, "⚙", app.open_manage, bg=THEME["panel"],
            fg=THEME["muted"], font=FONT_ICON,
        ).pack(side=tk.RIGHT, pady=8, padx=(0, 2))

        # Packed last so the controls keep their space; the title shrinks.
        tk.Label(
            self.header, text="Pair Bias Board", bg=THEME["panel"],
            fg=THEME["text"], font=FONT_TITLE, padx=18, anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.scroll = ScrollArea(self)
        self.scroll.pack(fill=tk.BOTH, expand=True)

        # Clicking empty board space releases the note box cleanly.
        for widget in (self, self.header, self.scroll.canvas,
                       self.scroll.inner):
            widget.bind(
                "<ButtonPress-1>", self._blur_on_outside_click, add="+"
            )

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
            bd=0, highlightthickness=1,
            highlightbackground=THEME["border"],
            highlightcolor=THEME["border"],  # no dark focus ring on the row
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
            highlightthickness=1,
            highlightbackground=THEME["border"],
            highlightcolor=THEME["border"],
            selectbackground=THEME["accent_soft"],
            selectforeground=THEME["text"], selectborderwidth=0,
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

    def _blur_on_outside_click(self, event):
        """Clear a note box when the user clicks non-editing board space."""
        if isinstance(event.widget, (SixStateSlider, MinimalScrollbar,
                                     tk.Entry, tk.Text, tk.Button,
                                     tk.Checkbutton)):
            return  # slider, another note, or a real control keeps its focus
        if isinstance(self.focus_get(), tk.Entry):
            self.focus_set()

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

