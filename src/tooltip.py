"""Tiny hover tooltip that shows the full state name on the board."""
from __future__ import annotations

import tkinter as tk

from config import FONT_UI_SMALL, THEME


class Tooltip:
    """Show `get_text()` in a small borderless window while hovering."""

    def __init__(self, widget, get_text, delay_ms=350):
        self.widget = widget
        self.get_text = get_text
        self.delay_ms = delay_ms
        self.window = None
        self._after = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<Motion>", self._on_motion, add="+")

    def _on_enter(self, _event=None):
        self._cancel()
        self._after = self.widget.after(self.delay_ms, self.show)

    def _on_motion(self, event):
        if self.window is not None:
            self._place(event.x_root, event.y_root)

    def _on_leave(self, _event=None):
        self._cancel()
        self.hide()

    def _cancel(self):
        if self._after is not None:
            try:
                self.widget.after_cancel(self._after)
            except tk.TclError:
                pass
            self._after = None

    def show(self):
        if self.window is not None:
            return
        text = self.get_text()
        if not text:
            return
        self.window = tk.Toplevel(self.widget)
        self.window.withdraw()
        self.window.overrideredirect(True)
        label = tk.Label(
            self.window, text=text, bg=THEME["panel"], fg=THEME["text"],
            font=FONT_UI_SMALL, padx=8, pady=4,
            highlightbackground=THEME["border"], highlightthickness=1,
        )
        label.pack()
        self._place(self.widget.winfo_pointerx(), self.widget.winfo_pointery())

    def _place(self, x_root, y_root):
        if self.window is None:
            return
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = min(x_root + 16, self.widget.winfo_screenwidth() - width - 8)
        y = min(y_root + 18, self.widget.winfo_screenheight() - height - 8)
        self.window.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.window.deiconify()

    def hide(self):
        if self.window is not None:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
            self.window = None
