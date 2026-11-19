"""Management view: add/reorder/hide/delete pairs, notes, bias summary."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from bias import currency_bias_summary
from board import ScrollArea
from config import (
    CURRENCIES,
    FONT_MONO,
    FONT_MONO_SMALL_BOLD,
    FONT_TITLE,
    FONT_UI,
    FONT_UI_SMALL,
    QUICK_PICKS,
    REMINDER,
    SUMMARY_DISCLAIMER,
    THEME,
)
from states import state_by_key


class NoteDialog(tk.Toplevel):
    def __init__(self, parent, pair, on_save):
        super().__init__(parent)
        self.title(f"Note for {pair.symbol}")
        self.configure(bg=THEME["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self._on_save = on_save
        self._pair = pair

        tk.Label(
            self, text=f"Note for {pair.symbol}", bg=THEME["bg"],
            fg=THEME["text"], font=FONT_TITLE,
        ).pack(anchor="w", padx=14, pady=(14, 6))
        tk.Label(
            self, text="Short note shown on the board. Leave empty to clear.",
            bg=THEME["bg"], fg=THEME["muted"], font=FONT_UI_SMALL,
        ).pack(anchor="w", padx=14)

        self.entry = tk.Entry(
            self, width=52, bg=THEME["panel"], fg=THEME["text"],
            insertbackground=THEME["text"], relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=THEME["border"],
            highlightcolor=THEME["border"],
            selectbackground=THEME["accent_soft"],
            selectforeground=THEME["text"], selectborderwidth=0,
            font=FONT_UI,
        )
        self.entry.insert(0, pair.note)
        self.entry.pack(padx=14, pady=10)
        self.entry.focus_set()

        buttons = tk.Frame(self, bg=THEME["bg"])
        buttons.pack(padx=14, pady=(0, 14), fill=tk.X)
        tk.Button(
            buttons, text="Save", command=self._save, bg=THEME["accent"],
            fg="#FFFFFF", relief=tk.FLAT, width=10,
        ).pack(side=tk.RIGHT, padx=(6, 0))
        tk.Button(
            buttons, text="Clear", command=self._clear, bg=THEME["panel_alt"],
            fg=THEME["muted"], relief=tk.FLAT, width=10,
        ).pack(side=tk.RIGHT)
        tk.Button(
            buttons, text="Cancel", command=self.destroy, bg=THEME["panel_alt"],
            fg=THEME["muted"], relief=tk.FLAT, width=10,
        ).pack(side=tk.LEFT)
        self.bind("<Escape>", lambda _e: self.destroy())

    def _save(self):
        self._on_save(self._pair.id, self.entry.get().strip())
        self.destroy()

    def _clear(self):
        self._on_save(self._pair.id, "")
        self.destroy()


class ManageWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("Pair Bias Board - Manage")
        self.configure(bg=THEME["bg"])
        self.geometry("840x620")
        self.transient(app.root)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.pairs_tab = tk.Frame(self.notebook, bg=THEME["bg"])
        self.summary_tab = tk.Frame(self.notebook, bg=THEME["bg"])
        self.notebook.add(self.pairs_tab, text="Pairs")
        self.notebook.add(self.summary_tab, text="Currency Bias Summary")

        self._build_pairs_tab()
        self._build_summary_tab()
        self.refresh()
        self.protocol("WM_DELETE_WINDOW", self.close)

    # ---- pairs tab -------------------------------------------------------
    def _build_pairs_tab(self):
        add_box = tk.Frame(
            self.pairs_tab, bg=THEME["panel"], bd=0,
            highlightthickness=1, highlightbackground=THEME["border"],
            highlightcolor=THEME["border"],
        )
        add_box.pack(fill=tk.X, padx=10, pady=(14, 6))
        tk.Label(
            add_box, text="Add pair", bg=THEME["panel"], fg=THEME["text"],
            font=FONT_TITLE,
        ).pack(anchor="w", padx=12, pady=(12, 0))

        entry_row = tk.Frame(add_box, bg=THEME["panel"])
        entry_row.pack(fill=tk.X, padx=8, pady=8)
        self.symbol_entry = tk.Entry(
            entry_row, width=12, bg=THEME["panel"], fg=THEME["text"],
            insertbackground=THEME["text"], relief=tk.FLAT,
            highlightbackground=THEME["border"], highlightthickness=1,
            highlightcolor=THEME["border"],
            selectbackground=THEME["accent_soft"],
            selectforeground=THEME["text"], selectborderwidth=0,
            font=FONT_MONO,
        )
        self.symbol_entry.pack(side=tk.LEFT)
        self.symbol_entry.bind("<Return>", lambda _e: self._add_typed())
        tk.Button(
            entry_row, text="Add", command=self._add_typed, bg=THEME["accent"],
            fg="#FFFFFF", relief=tk.FLAT, width=8,
        ).pack(side=tk.LEFT, padx=(8, 0))
        self.add_error = tk.Label(
            entry_row, text="", bg=THEME["panel"], fg=THEME["error"],
            font=FONT_UI_SMALL, anchor="w",
        )
        self.add_error.pack(side=tk.LEFT, padx=12, fill=tk.X, expand=True)

        picks = tk.Frame(add_box, bg=THEME["panel"])
        picks.pack(fill=tk.X, padx=8, pady=(0, 8))
        for index, symbol in enumerate(QUICK_PICKS):
            row, col = divmod(index, 7)
            tk.Button(
                picks, text=symbol, width=8,
                command=lambda s=symbol: self._add_quick(s),
                bg=THEME["panel_alt"], fg=THEME["text"], relief=tk.FLAT,
                font=FONT_UI_SMALL,
            ).grid(row=row, column=col, padx=2, pady=2, sticky="w")

        tk.Label(
            self.pairs_tab,
            text="Rows on board   |   move ▲▼   |   tick = visible   "
                 "|   note   |   delete",
            bg=THEME["bg"], fg=THEME["muted"], font=FONT_UI_SMALL,
        ).pack(anchor="w", padx=12, pady=(6, 2))

        self.list_area = ScrollArea(self.pairs_tab, content_width=820)
        self.list_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        bottom = tk.Frame(self.pairs_tab, bg=THEME["bg"])
        bottom.pack(fill=tk.X, padx=10, pady=8)
        tk.Button(
            bottom, text="Reset all to Neutral", command=self._reset_all,
            bg=THEME["panel_alt"], fg=THEME["warning"], relief=tk.FLAT,
            font=FONT_UI_SMALL,
        ).pack(side=tk.LEFT)
        tk.Label(
            bottom,
            text=f"Supported codes: {', '.join(sorted(CURRENCIES))}",
            bg=THEME["bg"], fg=THEME["muted"], font=FONT_UI_SMALL,
            wraplength=560, justify=tk.LEFT,
        ).pack(side=tk.RIGHT, fill=tk.X, expand=True)

    def _add_typed(self):
        error = self.app.add_pair(self.symbol_entry.get())
        self.add_error.configure(text=error or "")
        if error is None:
            self.symbol_entry.delete(0, tk.END)
            self.refresh()

    def _add_quick(self, symbol):
        error = self.app.add_pair(symbol)
        self.add_error.configure(text=error or "")
        if error is None:
            self.refresh()

    def _rebuild_pair_list(self):
        for child in list(self.list_area.inner.winfo_children()):
            child.destroy()
        pairs = self.app.data["pairs"]
        if not pairs:
            tk.Label(
                self.list_area.inner, text="No pairs yet. Add one above.",
                bg=THEME["bg"], fg=THEME["muted"], font=FONT_UI,
            ).pack(pady=20)
            return

        for position, pair in enumerate(pairs):
            row = tk.Frame(
                self.list_area.inner, bg=THEME["panel"], bd=0,
                highlightthickness=1, highlightbackground=THEME["border"],
                highlightcolor=THEME["border"],
            )
            row.pack(fill=tk.X, padx=6, pady=3)

            tk.Label(
                row, text=f"{position + 1:>2}.  {pair.symbol}", width=13,
                anchor="w", bg=THEME["panel"], fg=THEME["text"],
                font=FONT_TITLE,
            ).pack(side=tk.LEFT)

            state = state_by_key(pair.state)
            tk.Label(
                row, text=state["short"], width=4, bg=THEME["panel"],
                fg=state["color"], font=FONT_MONO_SMALL_BOLD,
            ).pack(side=tk.LEFT)

            tk.Button(
                row, text="▲", width=2, command=lambda i=pair.id: self.app.move_pair(i, -1),
                bg=THEME["panel_alt"], fg=THEME["muted"], relief=tk.FLAT,
            ).pack(side=tk.LEFT, padx=(8, 1))
            tk.Button(
                row, text="▼", width=2, command=lambda i=pair.id: self.app.move_pair(i, 1),
                bg=THEME["panel_alt"], fg=THEME["muted"], relief=tk.FLAT,
            ).pack(side=tk.LEFT, padx=1)

            visible = tk.BooleanVar(value=pair.visible)
            visible.trace_add(
                "write",
                lambda *_a, i=pair.id, v=visible: self.app.set_visible(i, v.get()),
            )
            tk.Checkbutton(
                row, text="on board", variable=visible, bg=THEME["panel"],
                fg=THEME["muted"], selectcolor=THEME["panel_alt"],
                activebackground=THEME["panel"], relief=tk.FLAT,
                font=FONT_UI_SMALL,
            ).pack(side=tk.LEFT, padx=(8, 2))

            note_preview = pair.note or "(no note)"
            if len(note_preview) > 22:
                note_preview = note_preview[:21] + "…"
            tk.Button(
                row, text=f"Note: {note_preview}", width=30, anchor="w",
                command=lambda p=pair: NoteDialog(
                    self, p, lambda i, text: self._save_note(i, text)
                ),
                bg=THEME["panel_alt"], fg=THEME["muted"], relief=tk.FLAT,
                font=FONT_UI_SMALL,
            ).pack(side=tk.LEFT, padx=2)

            tk.Button(
                row, text="Delete", command=lambda p=pair: self._delete(p),
                bg=THEME["panel_alt"], fg=THEME["error"], relief=tk.FLAT,
                font=FONT_UI_SMALL,
            ).pack(side=tk.LEFT, padx=2)

    def _save_note(self, pair_id, text):
        self.app.set_note(pair_id, text)
        self.refresh()

    def _delete(self, pair):
        if messagebox.askyesno(
            "Delete pair",
            f"Delete {pair.symbol} from the board?\nIts bias and note will be lost.",
            parent=self,
        ):
            self.app.delete_pair(pair.id)
            self.refresh()

    def _reset_all(self):
        if messagebox.askyesno(
            "Reset all to Neutral",
            "Set every pair to Neutral and record this time as the update time?",
            parent=self,
        ):
            self.app.reset_all()
            self.refresh()

    # ---- summary tab -----------------------------------------------------
    def _build_summary_tab(self):
        tk.Label(
            self.summary_tab, text=SUMMARY_DISCLAIMER, bg=THEME["bg"],
            fg=THEME["muted"], font=FONT_UI_SMALL, wraplength=790,
            justify=tk.LEFT,
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self.summary_text = tk.Text(
            self.summary_tab, bg=THEME["panel"], fg=THEME["text"],
            relief=tk.FLAT, font=FONT_UI, wrap=tk.WORD,
            highlightbackground=THEME["border"], highlightthickness=1,
            highlightcolor=THEME["border"],
            padx=12, pady=12, height=18,
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=14)
        self.summary_text.configure(state=tk.DISABLED)
        self.summary_text.tag_configure("warn", foreground=THEME["warning"])
        self.summary_text.tag_configure("dim", foreground=THEME["muted"])

        tk.Label(
            self.summary_tab, text=REMINDER, bg=THEME["bg"],
            fg=THEME["accent"], font=FONT_TITLE,
            wraplength=790, justify=tk.LEFT,
        ).pack(anchor="w", padx=14, pady=10)

    def _rebuild_summary(self):
        result = currency_bias_summary(self.app.data["pairs"])
        currencies = result["currencies"]
        text = self.summary_text
        text.configure(state=tk.NORMAL)
        text.delete("1.0", tk.END)

        if not currencies:
            text.insert(tk.END, "No fresh, active biases to summarise.\n", "dim")
        for code, info in currencies.items():
            sign = "+" if info["net"] > 0 else ""
            text.insert(tk.END, f"{code}   net {sign}{info['net']}\n")
            pieces = [f"{symbol} {value:+d}" for symbol, value in info["contributions"]]
            text.insert(tk.END, f"      from: {', '.join(pieces)}\n", "dim")
            if info["conflict"]:
                text.insert(
                    tk.END,
                    f"      CONFLICT: {', '.join(info['conflict_pairs'])}\n",
                    "warn",
                )
            if info["concentration"]:
                text.insert(
                    tk.END,
                    f"      POTENTIAL CONCENTRATION: |net| = "
                    f"{abs(info['net'])} (>= 3)\n",
                    "warn",
                )

        if result["ignored"]:
            text.insert(tk.END, "\nSkipped (Neutral, No Trade or stale): ", "dim")
            text.insert(tk.END, ", ".join(result["ignored"]) + "\n", "dim")

        text.configure(state=tk.DISABLED)

    # ---- lifecycle -------------------------------------------------------
    def refresh(self):
        if not self.winfo_exists():
            return
        self._rebuild_pair_list()
        self._rebuild_summary()

    def close(self):
        self.destroy()
        self.app.manage_window = None
