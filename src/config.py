"""All user-facing constants live here so they are easy to find and change.

Nothing in this file talks to the internet or to a trading account.
"""
from __future__ import annotations

# --- Stale bias -----------------------------------------------------------
# A bias older than this many hours is shown as "STALE" and ignored by the
# currency bias summary. Change this one number to change the rule.
STALE_AFTER_HOURS = 24

# How often the compact board recomputes "time since last set".
REFRESH_INTERVAL_MS = 30_000

# --- Storage --------------------------------------------------------------
APP_DIR_NAME = "PairBiasBoard"
DATA_FILE_NAME = "data.json"
DATA_VERSION = 1
DEFAULT_SYMBOL = "USDJPY"  # used only on the very first launch

# --- Notes ----------------------------------------------------------------
MAX_NOTE_CHARS = 200

# --- Supported three-letter codes ----------------------------------------
# Keep the whole list here. XAU = gold, XAG = silver.
CURRENCIES = frozenset(
    {
        "AED", "ARS", "AUD", "BGN", "BRL", "CAD", "CHF", "CNY", "CZK",
        "DKK", "EUR", "GBP", "HKD", "HUF", "IDR", "ILS", "INR", "ISK",
        "JPY", "KRW", "MXN", "MYR", "NOK", "NZD", "PHP", "PLN", "RON",
        "SEK", "SGD", "THB", "TRY", "TWD", "USD", "ZAR", "XAU", "XAG",
    }
)

# One-tap choices in the Add Pair view.
QUICK_PICKS = (
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD",
    "NZDUSD", "EURJPY", "GBPJPY", "EURGBP", "EURAUD", "AUDJPY",
    "XAUUSD",
)

# --- Typography -----------------------------------------------------------
# Windows system fonts: clean like SF Pro / SF Mono on Apple devices.
FONT_UI = ("Segoe UI", 10)
FONT_UI_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)
FONT_MONO_SMALL_BOLD = ("Consolas", 9, "bold")
FONT_ICON = ("Segoe UI Symbol", 13)
FONT_PLUS = ("Segoe UI", 15)

# --- Light, minimalist theme ----------------------------------------------
# Warm off-white canvas, white cards, whisper borders, one blue accent.
# Inspired by the Apple and Notion design systems (translated to Tkinter).
THEME = {
    "bg": "#F6F5F4",           # warm off-white page
    "panel": "#FFFFFF",        # card / row surface
    "panel_alt": "#EFEEEC",    # hover and secondary chips
    "border": "#E6E3DF",       # barely-visible divider
    "text": "#1D1D1F",         # primary near-black
    "muted": "#6E6E73",        # secondary text
    "faint": "#A39E98",        # placeholders and disabled text
    "accent": "#0071E3",       # the only saturated colour
    "accent_soft": "#E8F1FD",  # selected chip background
    "error": "#B4443D",
    "warning": "#B26A00",
    "track": "#E3E1DE",        # slider track
    "knob": "#FFFFFF",         # slider thumb
    "knob_border": "#D6D3CF",
}

# --- Compact board layout -------------------------------------------------
# Tiny floor so the window can shrink freely; scrollbars reveal hidden content.
MIN_WINDOW_SIZE = (220, 140)
# Size used only on the very first launch (no saved geometry yet).
DEFAULT_WINDOW_SIZE = (800, 460)
CONTENT_WIDTH = 760  # inner layout width before horizontal scrolling starts
ROW_HEIGHT = 46
SLIDER_WIDTH = 260
SLIDER_HEIGHT = 36
TIME_WIDTH = 92

REMINDER = "Bias = permission to look for a setup, not an entry signal."
SUMMARY_DISCLAIMER = (
    "This is a simple visual summary of subjective biases, not a calculation "
    "of position size or actual exposure."
)
