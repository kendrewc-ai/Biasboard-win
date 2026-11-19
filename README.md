# Pair Bias Board

A small Windows desktop window that reminds you of your **manual** directional
bias for the FX pairs you follow. You choose the pairs and set each bias
yourself. No account, no internet, no market data, no trades.

The interface is deliberately simple: a warm off-white background, white
cards, thin dividers, one blue accent, Segoe UI text with Consolas for tickers.
The slider is a thin line with a small white round thumb — it moves with your
mouse and settles softly into place. No gradients or shadows.

> Bias = permission to look for a setup, not an entry signal.

This is a normal application window. The optional **ON TOP** button is a normal
Windows "always on top" window setting — it keeps this window above other app
windows while the app is running. It is **not** a widget pinned to the Windows
desktop behind your icons, and it is **not** part of the Windows Widgets panel.

---

## 1. Check your computer

You need Windows 10 or Windows 11 and Python 3.11 or newer.

Open **PowerShell** (press `Win + X`, choose *Windows PowerShell*) and run:

```powershell
python --version
```

You should see something like `Python 3.11.9` or `Python 3.14.7`.

Now check Tkinter (the window toolkit):

```powershell
python -c "import tkinter; print('Tkinter OK, Tk', tkinter.TkVersion)"
```

If you see `Tkinter OK`, you are ready.

### If Python is not installed

1. Go to <https://www.python.org/downloads/>.
2. Click the big **Download Python** button.
3. Run the downloaded file.
4. **Important:** tick the box **"Add python.exe to PATH"** at the bottom of the
   first screen, then click *Install Now*.
5. Close and reopen PowerShell, then repeat the two checks above.

No extra Python packages are needed. The app uses only the Python standard
library. There is nothing to `pip install` for normal use.

---

## 2. Run the app

In PowerShell, open the folder where you put the app (change the path if your
folder is somewhere else):

```powershell
cd "$HOME\PairBiasBoard"
python main.py
```

The board opens. On the very first launch it contains one pair, **USDJPY**, set
to Neutral. If you delete it, it will not come back.

To close the board, click the window's **X** button, or run `python main.py`
again later — your data is saved automatically.

---

## 3. Launch without a terminal (recommended)

There is a file named **`Run Pair Bias Board.bat`** in the project folder.
Double-click it and the board opens. You can keep the terminal closed.

To put a shortcut on your Desktop, run this once in PowerShell:

```powershell
$ws = New-Object -ComObject WScript.Shell
$app = (Get-Location).Path
$sc = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Pair Bias Board.lnk")
$sc.TargetPath = Join-Path $app "Run Pair Bias Board.bat"
$sc.WorkingDirectory = $app
$sc.Save()
```

Now you can double-click **Pair Bias Board** on your Desktop.

---

## 4. Using the board

The six slider positions, from left to right, are:

| Short | Full name |
| --- | --- |
| VB | Very Bearish |
| B | Bearish |
| N | Neutral |
| Bu | Bullish |
| VBu | Very Bullish |
| NT | No Trade |

Each row shows: **ticker**, **six-position slider**, **time since last set**,
then the **note**.

- **Drag** the knob with your mouse. It follows the pointer. Let go and it
  smoothly snaps to the nearest of the six positions and saves.
- **Click** any short label (VB, B, N, Bu, VBu, NT) to move there with a short
  animation.
- **Keyboard:** click the slider first, then use **Left / Right** to move one
  position, or **Home / End** for the first / last position.
- **Full name:** hover the mouse over the slider to see the full state name,
  for example "Very Bullish". The selected label is also bold and the knob
  shows the short text, so colour is not the only clue.
- **⚠ STALE** appears when the bias is more than 24 hours old. The age updates
  automatically while the app is open.
- Selecting a state — even the one already selected — confirms it and starts a
  fresh 24-hour timer.
- The **On Top** button in the header toggles always-on-top (a small dot shows
  when it is on). Your choice is remembered.
- **+** opens the Add Pair box. The small gear button opens the Manage window.

Notes that are too long simply scroll inside the small note box on the row.
Hover the note to see the full text. The Manage window also shows the full note.

The coloured part of the slider always starts at **N (Neutral)**: bearish states
paint leftwards in red, bullish states paint rightwards in green. No Trade uses
a muted colour. The short label and bold text also show the selected position.

The window can be dragged anywhere by its title bar and freely resized, right
down to a very small size. The header is **fixed**: the Add, settings gear and
On Top controls stay pinned at the top-right corner and do not move when you
scroll. The rows below scroll independently.

When content does not fit, a thin grey scrollbar appears on the right and/or
along the bottom. The mouse wheel scrolls vertically; **Shift + wheel** or a
horizontal wheel scrolls sideways. High-resolution touchpad deltas are
accumulated, so scrolling stays smooth instead of jumping. Each bar can be
dragged directly with the mouse, and both bars hide again when the content
fits.

---

## 5. Add, reorder, hide, delete, and notes

Click **⚙** to open **Manage**. It has two tabs.

### Add a pair (Pairs tab)

- Type a symbol in the box and press **Add** or **Enter**, or click one of the
  quick-pick buttons.
- Typed symbols are automatically made uppercase (`eurusd` → `EURUSD`).
- Rules: exactly 6 letters, split into two valid 3-letter codes, base and quote
  different, and not already on the board. `XAU` (gold) and `XAG` (silver) are
  supported. Errors appear in red next to the box.
- New pairs start as **Neutral**.

### Reorder, hide, delete

- **▲ / ▼** move a row up or down.
- The **on board** checkbox decides whether the pair appears on the compact
  board. Unticking it hides the row but keeps all its data.
- **Delete** asks for confirmation before removing the pair and its note.
- **Reset all to Neutral** asks for confirmation, sets every pair to Neutral,
  and records that time as the update time.

Changing a note, order, or visibility does **not** change the bias time.

### Edit a note

You can type directly in the **note box on the board row** — no Save button
needed. It saves itself about half a second after you stop typing, and
immediately when you press **Enter** or click away. Editing a note does not
change the bias time. The row does not turn bold or dark while you edit, and
clicking empty board space releases the note box.

In the Pairs tab of Manage, click the **Note: …** button for a pair. Type your
note and click **Save**. Click **Clear** (or save an empty box) to remove it.
The full note appears on the board right after the time.

### Currency Bias Summary tab

This is a summary of your **manual biases**, not your real positions or risk.
Neutral, No Trade, and stale pairs are ignored. Weights are:

- Very Bullish: base +2, quote −2
- Bullish: base +1, quote −1
- Bearish: base −1, quote +1
- Very Bearish: base −2, quote +2

Each currency shows its net score and the pairs that contributed. A
**CONFLICT** is flagged when different pairs give the same currency both plus
and minus contributions; the pairs are listed. **POTENTIAL CONCENTRATION** is
flagged when the absolute net score is 3 or more. These weights are a simple
visual summary of subjective bias — **not** position size or actual exposure.

---

## 6. Where the data is stored

By default your data is a JSON file in your own Windows user area, not in the
project folder:

```
%LOCALAPPDATA%\PairBiasBoard\data.json
```

### Moving the app (portable mode)

The code has no fixed drive letters or user names. The launcher starts
`main.py` from its own folder, and the app finds its files relative to that
folder. You can copy the whole `PairBiasBoard` folder to another folder, another
drive, or another Windows computer and run it there — no code edits and no
extra installs (Python + Tkinter are the only requirements).

By default each Windows user keeps their own board in `%LOCALAPPDATA%`. If you
want the data to travel **with the folder**, close the app and create an empty
file named `PORTABLE` (no extension) next to `main.py`. On the next start the
app creates a `data` folder there and uses `data\data.json`. Copy the whole
folder and your board goes with it. Remove the `PORTABLE` file to switch back
to the per-user folder; the `data` folder is left alone, so copy `data.json`
yourself if you want it back.

In PowerShell, to see the default folder:

```powershell
explorer "$env:LOCALAPPDATA\PairBiasBoard"
```

To back it up to your Desktop:

```powershell
Copy-Item "$env:LOCALAPPDATA\PairBiasBoard\data.json" "$env:USERPROFILE\Desktop\data-backup.json"
```

To restore, close the app, copy the backup back over `data.json`, then reopen.

If the file is ever damaged, the app shows a clear message, saves a copy named
`data.corrupt-<date>.json` beside it, and starts a fresh board. It never quietly
overwrites the damaged file. If saving fails, an error window appears and the
old file is left untouched.

The app makes no network calls and sends no data anywhere.

---

## 7. Tests

From the project folder:

```powershell
cd "$HOME\PairBiasBoard"
python -m unittest discover -s tests -v
```

The tests cover symbol validation, the six-state mapping, stale logic, JSON
persistence, portable path resolution, window-position repair, and the currency
bias / conflict maths. They need no internet and no extra packages.

---

## 8. Windows manual test checklist

The automated checks and a scripted Tk smoke test were run on Windows. A human
should still do a quick visual pass:

- [ ] Drag the knob slowly — it follows the mouse; release snaps smoothly.
- [ ] Click each of the six labels — the knob animates to that position.
- [ ] Click the slider then use Left/Right/Home/End — the state changes.
- [ ] Hover a slider — the full state name appears (e.g. "Very Bullish").
- [ ] Hover a truncated note — the full note appears.
- [ ] Add a pair by typing lowercase text; try a duplicate and a bad code.
- [ ] Reorder, hide, show, and delete a pair (with confirmation).
- [ ] Edit and clear a note; confirm it does not change the age.
- [ ] Type directly in the board's note box; confirm it saves without a Save button.
- [ ] Drag a window edge down to a very small size — both scrollbars appear as needed.
- [ ] Scroll with the wheel and with Shift+wheel; the header buttons stay pinned.
- [ ] Check bearish colour grows left from N and bullish colour grows right from N.
- [ ] Click **Reset all to Neutral** and confirm.
- [ ] Toggle **ON TOP** and check it stays on after a restart.
- [ ] Add enough pairs to scroll (more than 8 rows); scroll with the mouse wheel.
- [ ] Close and reopen — pairs, order, notes, states, and window position return.
- [ ] To test STALE: close the app, open `data.json`, change one `updated_at`
      to an old date such as `2020-01-01T00:00:00+00:00`, save, and reopen.
      That row should show **⚠ STALE** and be ignored in the summary.

---

## 9. Build the Windows EXE (no CMD window)

The app still runs from source with `python main.py`. Building the EXE needs
PyInstaller, installed once:

```powershell
py -3.12 -m pip install pyinstaller
py -3.12 build.py
```

(Use Python 3.12 for the build: that is where PyInstaller was installed.)

`build.py` resolves every path from its own folder, converts the existing
`icon.png` into `icon.ico` if needed (same artwork, no redesign), and writes:

```
dist\Pair Bias Board.exe
```

- `--onefile --windowed` means one portable EXE and **no CMD window**.
- The icon is set on the EXE (Explorer, taskbar, Start menu) and on the app
  window itself. To pin it: right-click the EXE or its Start menu shortcut,
  then **Pin to taskbar** or **Pin to Start**.
- Data goes to `%LOCALAPPDATA%\PairBiasBoard\`. Put a `PORTABLE` file next to
  the EXE and data goes to `<app folder>\data\` instead, so the whole folder
  can be copied to another drive.
- Errors are written to `pairbiasboard.log` beside `data.json` (and shown in a
  dialog), because there is no console to print them to.

### After you change the app

The EXE is a **snapshot** of the code when it was built. It does not update
itself. After editing `main.py` or anything in `src\`:

1. Close the app if it is running (a running EXE cannot be overwritten).
2. Run `py -3.12 build.py` in this folder. It replaces `dist\Pair Bias Board.exe`.
3. Open the new EXE and check it once.

Your pairs, notes and states live in `data.json`, **outside** the EXE, so a
rebuild never deletes them. If you replace `icon.png`, delete `icon.ico` first
so `build.py` makes a new ICO from the new artwork.

For quick checks before rebuilding, running `python main.py` uses your latest
source code immediately — no build needed.

---

## Project files

```
PairBiasBoard/
├── main.py                     entry point (error logging + Windows app id)
├── build.py                    builds the windowed EXE from project-relative paths
├── icon.png                    your existing icon artwork (source)
├── icon.ico                    Windows icon generated from icon.png
├── Run Pair Bias Board.bat     double-click launcher for source runs
├── README.md                   this file
├── .gitignore                  keeps caches and runtime data out of Git
├── src/
│   ├── app.py                  controller: connects views and data
│   ├── errorlog.py             crash/error logging (no console needed)
│   ├── bias.py                 currency bias / conflict maths
│   ├── board.py                compact board + scroll area
│   ├── config.py               all settings and the supported-code list
│   ├── geometry.py             window repair, slider and scrollbar maths
│   ├── iconbutton.py           minimal round header buttons
│   ├── manage.py               manage window + bias summary
│   ├── models.py               Pair record
│   ├── paths.py                portable path resolution
│   ├── slider.py               reusable six-position slider widget
│   ├── states.py               the six fixed states
│   ├── storage.py              safe local JSON save/load
│   ├── timeutil.py             stale and age helpers
│   ├── tooltip.py              hover tooltip
│   └── validation.py           symbol rules
└── tests/                      automated checks (standard-library unittest)
```
