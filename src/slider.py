"""Reusable six-position slider drawn on a Tk Canvas.

Minimal style: thin track tinted with the current bias colour, a small white
round thumb, and six short labels. One instance per ticker row.
Drag follows the mouse; release snaps with a short animation. Clicking a
label and the arrow keys also work.
"""
from __future__ import annotations

import tkinter as tk

from config import FONT_MONO_SMALL, SLIDER_HEIGHT, SLIDER_WIDTH, THEME
from geometry import ease_out, fill_span, nearest_index, position_x
from states import index_of_key, key_at_index, state_at_index
from tooltip import Tooltip

PAD = 20
TRACK_Y = 11
LABEL_Y = 27
THUMB_RADIUS = 8
ANIM_STEPS = 8
ANIM_DELAY_MS = 18


class SixStateSlider(tk.Canvas):
    def __init__(self, parent, state_key: str, on_change,
                 width: int = SLIDER_WIDTH, height: int = SLIDER_HEIGHT):
        super().__init__(
            parent, width=width, height=height, bg=THEME["panel"],
            highlightthickness=0, bd=0, takefocus=1,
        )
        self._width = width
        self._index = index_of_key(state_key)
        self._knob_x = position_x(self._index, width, PAD)
        self._on_change = on_change
        self._anim_id = None
        self._press_x = 0
        self._dragged = False

        self._build()
        self._tooltip = Tooltip(self, self._tooltip_text)

        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_motion)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Left>", self._on_key)
        self.bind("<Right>", self._on_key)
        self.bind("<Home>", self._on_key)
        self.bind("<End>", self._on_key)
        self.bind("<FocusIn>", lambda _e: self._redraw(), add="+")
        self.bind("<FocusOut>", lambda _e: self._redraw(), add="+")

    # ---- drawing ---------------------------------------------------------
    def _build(self):
        self._track = self.create_line(
            PAD, TRACK_Y, self._width - PAD, TRACK_Y,
            fill=THEME["track"], width=4, capstyle=tk.ROUND,
        )
        fill_start, fill_end = fill_span(self._index, self._width, PAD)
        self._fill = self.create_line(
            fill_start, TRACK_Y, fill_end, TRACK_Y,
            fill=state_at_index(self._index)["color"],
            width=4, capstyle=tk.ROUND,
        )
        self._shadow = self.create_oval(
            self._knob_x - THUMB_RADIUS, TRACK_Y - THUMB_RADIUS + 1,
            self._knob_x + THUMB_RADIUS, TRACK_Y + THUMB_RADIUS + 1,
            fill=THEME["border"], outline="",
        )
        self._knob = self.create_oval(
            self._knob_x - THUMB_RADIUS, TRACK_Y - THUMB_RADIUS,
            self._knob_x + THUMB_RADIUS, TRACK_Y + THUMB_RADIUS,
            fill=THEME["knob"], outline=THEME["knob_border"], width=1,
        )
        self._labels = []
        for index in range(6):
            x = position_x(index, self._width, PAD)
            self._labels.append(self.create_text(
                x, LABEL_Y, text=state_at_index(index)["short"],
                fill=THEME["muted"], font=FONT_MONO_SMALL,
            ))
        self._redraw()

    def _redraw(self):
        visual = nearest_index(self._knob_x, self._width, PAD)
        colour = state_at_index(visual)["color"]
        x = self._knob_x

        fill_start, fill_end = fill_span(visual, self._width, PAD)
        if fill_start == fill_end:
            self.itemconfigure(self._fill, state="hidden")
        else:
            self.itemconfigure(self._fill, state="normal")
            self.coords(self._fill, fill_start, TRACK_Y, fill_end, TRACK_Y)
        self.itemconfigure(self._fill, fill=colour)

        for item in (self._shadow, self._knob):
            offset = 1 if item is self._shadow else 0
            self.coords(
                item,
                x - THUMB_RADIUS, TRACK_Y - THUMB_RADIUS + offset,
                x + THUMB_RADIUS, TRACK_Y + THUMB_RADIUS + offset,
            )

        for index, label in enumerate(self._labels):
            selected = index == visual
            self.itemconfigure(
                label,
                fill=THEME["text"] if selected else THEME["muted"],
                font=FONT_MONO_SMALL + ("bold",) if selected else FONT_MONO_SMALL,
            )

    def _tooltip_text(self):
        visual = nearest_index(self._knob_x, self._width, PAD)
        name = state_at_index(visual)["name"]
        if self._dragged:
            return f"{name}  (release to confirm)"
        return name

    # ---- animation -------------------------------------------------------
    def _stop_animation(self):
        if self._anim_id is not None:
            try:
                self.after_cancel(self._anim_id)
            except tk.TclError:
                pass
            self._anim_id = None

    def _animate_to(self, target_x):
        self._stop_animation()
        start_x = self._knob_x
        step = 0

        def frame():
            nonlocal step
            step += 1
            t = step / ANIM_STEPS
            self._knob_x = start_x + (target_x - start_x) * ease_out(t)
            self._redraw()
            if step < ANIM_STEPS:
                self._anim_id = self.after(ANIM_DELAY_MS, frame)
            else:
                self._anim_id = None
                self._knob_x = target_x
                self._redraw()

        frame()

    # ---- public API ------------------------------------------------------
    def current_key(self) -> str:
        return key_at_index(self._index)

    def is_busy(self) -> bool:
        """True while animating or being dragged; callers should not reset it."""
        return self._anim_id is not None or self._dragged

    def set_state(self, key: str):
        """Set without animation or callback (used when loading data)."""
        self._stop_animation()
        self._index = index_of_key(key)
        self._knob_x = position_x(self._index, self._width, PAD)
        self._redraw()

    def _commit(self, index: int):
        self._index = max(0, min(5, index))
        self._animate_to(position_x(self._index, self._width, PAD))
        self._on_change(key_at_index(self._index))

    # ---- input -----------------------------------------------------------
    def _on_press(self, event):
        self.focus_set()
        self._stop_animation()
        self._press_x = event.x
        self._dragged = False

    def _on_motion(self, event):
        if abs(event.x - self._press_x) > 3:
            self._dragged = True
        if self._dragged:
            self._knob_x = max(PAD, min(self._width - PAD, event.x))
            self._redraw()

    def _on_release(self, event):
        end_x = self._knob_x if self._dragged else event.x
        index = nearest_index(end_x, self._width, PAD)
        self._dragged = False
        self._commit(index)

    def _on_key(self, event):
        key = event.keysym
        if key == "Right":
            target = self._index + 1
        elif key == "Left":
            target = self._index - 1
        elif key == "Home":
            target = 0
        elif key == "End":
            target = 5
        else:
            return
        self._commit(target)
        return "break"
