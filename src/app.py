"""Application controller: holds the data and connects the two views."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from board import BoardView
from config import FONT_UI_SMALL, MIN_WINDOW_SIZE, REFRESH_INTERVAL_MS, THEME
from geometry import clamp_geometry
from manage import ManageWindow
from models import Pair
from storage import StorageError, load_data, save_data
from timeutil import to_iso, utc_now
from validation import validate_symbol


class App:
    def __init__(self):
        self.data, warning = load_data()
        self.manage_window = None
        self._note_save_after = None

        self.root = tk.Tk()
        self.root.title("Pair Bias Board")
        self.root.configure(bg=THEME["bg"])
        self._configure_styles()

        min_w, min_h = MIN_WINDOW_SIZE
        saved_geometry = self.data["settings"].get("geometry", "")
        geometry = clamp_geometry(
            saved_geometry,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
            min_w, min_h,
        )
        if geometry:
            self.root.geometry(geometry)
        else:
            self.root.geometry(f"{min_w}x{min_h}+60+60")
        self.root.minsize(min_w, min_h)
        # Free to drag or resize, but never smaller than the readable layout.
        self.root.resizable(True, True)

        self.root.attributes(
            "-topmost", bool(self.data["settings"]["always_on_top"])
        )

        self.board = BoardView(self.root, self)
        self.board.pack(fill=tk.BOTH, expand=True)
        self.board.rebuild(self.visible_pairs())
        self.board.set_top_button(self.data["settings"]["always_on_top"])

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(REFRESH_INTERVAL_MS, self._refresh_loop)

        if warning:
            messagebox.showwarning("Pair Bias Board - data warning", warning)

    # ---- setup -----------------------------------------------------------
    @staticmethod
    def _configure_styles():
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background=THEME["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab", background=THEME["bg"],
            foreground=THEME["muted"], padding=(14, 8),
            font=FONT_UI_SMALL, borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME["panel"])],
            foreground=[("selected", THEME["text"])],
        )
        style.configure(
            "Vertical.TScrollbar", background=THEME["border"],
            troughcolor=THEME["bg"], arrowcolor=THEME["muted"],
            borderwidth=0,
        )

    # ---- helpers ---------------------------------------------------------
    def visible_pairs(self):
        return [pair for pair in self.data["pairs"] if pair.visible]

    def _find(self, pair_id):
        return next(
            (pair for pair in self.data["pairs"] if pair.id == pair_id), None
        )

    def _save(self) -> bool:
        try:
            save_data(self.data)
            return True
        except StorageError as exc:
            messagebox.showerror("Pair Bias Board - save failed", str(exc))
            return False

    def _sync_views(self):
        self.board.rebuild(self.visible_pairs())
        if self.manage_window is not None:
            self.manage_window.refresh()

    def _refresh_loop(self):
        if self.board.winfo_exists():
            self.board.refresh(self.visible_pairs())
            self.root.after(REFRESH_INTERVAL_MS, self._refresh_loop)

    # ---- actions ---------------------------------------------------------
    def set_state(self, pair_id, key, source=None):
        pair = self._find(pair_id)
        if pair is None:
            return
        # Selecting a state (even the same one) confirms it now.
        pair.state = key
        pair.updated_at = to_iso(utc_now())
        self._save()
        # The slider that started this change is already animating itself.
        self.board.refresh(self.visible_pairs(), skip_slider=source)
        if self.manage_window is not None:
            self.manage_window.refresh()

    def add_pair(self, text) -> str | None:
        existing = [pair.symbol for pair in self.data["pairs"]]
        symbol, error = validate_symbol(text, existing=existing)
        if error:
            return error
        self.data["pairs"].append(Pair.new(symbol))
        self._save()
        self.board.rebuild(self.visible_pairs())
        return None

    def delete_pair(self, pair_id):
        self.data["pairs"] = [
            pair for pair in self.data["pairs"] if pair.id != pair_id
        ]
        self._save()
        self._sync_views()

    def move_pair(self, pair_id, delta):
        pairs = self.data["pairs"]
        index = next(
            (i for i, pair in enumerate(pairs) if pair.id == pair_id), None
        )
        if index is None:
            return
        target = index + delta
        if target < 0 or target >= len(pairs):
            return
        pairs[index], pairs[target] = pairs[target], pairs[index]
        self._save()
        self._sync_views()

    def set_visible(self, pair_id, visible):
        pair = self._find(pair_id)
        if pair is None:
            return
        pair.visible = bool(visible)
        self._save()
        self.board.rebuild(self.visible_pairs())

    def set_note(self, pair_id, text):
        pair = self._find(pair_id)
        if pair is None:
            return
        pair.note = text
        self._save()  # deliberately does NOT refresh the bias timestamp
        self.board.refresh(self.visible_pairs())

    def set_note_live(self, pair_id, text):
        """Inline note edit: change memory now, save after typing stops."""
        pair = self._find(pair_id)
        if pair is None or pair.note == text:
            return
        pair.note = text  # deliberately does NOT refresh the bias timestamp
        if self._note_save_after is not None:
            try:
                self.root.after_cancel(self._note_save_after)
            except tk.TclError:
                pass
        self._note_save_after = self.root.after(500, self.flush_note_save)

    def flush_note_save(self):
        """Write a pending inline note immediately."""
        if self._note_save_after is not None:
            try:
                self.root.after_cancel(self._note_save_after)
            except tk.TclError:
                pass
            self._note_save_after = None
        self._save()

    def reset_all(self):
        now = to_iso(utc_now())
        for pair in self.data["pairs"]:
            pair.state = "N"
            pair.updated_at = now
        self._save()
        self._sync_views()

    def toggle_topmost(self):
        current = bool(self.data["settings"]["always_on_top"])
        self.data["settings"]["always_on_top"] = not current
        self.root.attributes("-topmost", not current)
        self.board.set_top_button(not current)
        self._save()

    # ---- windows ---------------------------------------------------------
    def open_manage(self):
        if self.manage_window is not None and self.manage_window.winfo_exists():
            self.manage_window.lift()
            self.manage_window.focus_force()
            return
        self.manage_window = ManageWindow(self)

    def open_add_pair(self):
        self.open_manage()
        window = self.manage_window
        window.notebook.select(0)
        window.symbol_entry.focus_set()

    def close(self):
        self.flush_note_save()
        self.data["settings"]["geometry"] = self.root.geometry()
        self._save()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
