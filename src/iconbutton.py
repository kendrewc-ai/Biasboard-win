"""Small circular flat icon button: the minimal header controls (+ and gear)."""
from __future__ import annotations

import tkinter as tk

from config import FONT_UI, THEME


class IconButton(tk.Canvas):
    def __init__(self, parent, glyph, command, size=30, bg=None, fg=None,
                 font=None):
        surface = bg or THEME["panel"]
        super().__init__(
            parent, width=size, height=size, bg=surface,
            highlightthickness=0, bd=0, cursor="hand2",
        )
        self._command = command
        self._idle_fill = surface
        self._hover_fill = THEME["panel_alt"]
        self._circle = self.create_oval(
            1, 1, size - 1, size - 1, fill=self._idle_fill, outline=""
        )
        self._text = self.create_text(
            size / 2, size / 2, text=glyph,
            fill=fg or THEME["muted"], font=font or FONT_UI,
        )
        self.bind("<Enter>", lambda _e: self.itemconfigure(
            self._circle, fill=self._hover_fill))
        self.bind("<Leave>", lambda _e: self.itemconfigure(
            self._circle, fill=self._idle_fill))
        self.bind("<ButtonRelease-1>", self._on_click)

    def _on_click(self, _event):
        self._command()
