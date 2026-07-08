# Clipboard OCR (Screenshot → Text) — Design

Date: 2026-07-08

## Goal

Let the user capture text from any on-screen image by taking a screenshot with
their desktop environment's own tool, then pressing **Ctrl+V** in Lazynote. If
the clipboard holds an image, it is OCR'd locally with Tesseract and the
recognized text is inserted at the cursor (multi-line preserved). If the
clipboard holds text, normal paste runs unchanged.

Reuse the DE's screenshot tool rather than building an in-app region selector:
the DE tool already does region selection, works on both X11 and Wayland, and
puts the image on the clipboard in a compositor-agnostic way. Lazynote only
needs to detect the image, OCR it, and insert the text.

## Decisions

- **Capture**: reuse the DE's screenshot tool (Print / Spectacle / Flameshot /
  grim+slurp). No in-app region overlay, no global capture hotkey, no portal
  code in Lazynote. The user screenshots to clipboard as usual.
- **Trigger**: smart **Ctrl+V** in the editor — image on clipboard → OCR; text
  on clipboard → normal paste. One keystroke, behavior chosen by clipboard
  contents.
- **OCR engine**: **Tesseract** via `subprocess` (no `pytesseract`, no `Pillow`).
  Matches the project's lightweight/local ethos; screen text is Tesseract's
  sweet spot.
- **Image encoding**: `QImage` → PNG bytes via `QBuffer` + `image.save(buf, "PNG")`.
  PNG bytes flow to tesseract stdin → text from stdout. No temp files.
- **Async**: OCR runs on a daemon worker thread; result returns to the GUI
  thread via a Qt signal (queued cross-thread delivery, same pattern as
  `shortcuts.py`'s Alt+A activation).
- **Insertion**: splice at the cursor, `head + pasted + tail`, multi-line
  preserved. Generalizes the editor's existing `splitLine` to N lines.
- **No new Python dependencies.** No new settings UI for v1 (`ocr_lang`
  defaults to `eng`).

## End-to-end flow

1. User takes a screenshot with the DE tool, choosing "copy to clipboard".
2. User focuses Lazynote, places the cursor, presses **Ctrl+V**.
3. Bridge checks `QGuiApplication.clipboard()`:
   - clipboard has an image → emit "Recognizing…" status, start OCR worker,
     return `""` to QML (nothing pasted yet).
   - clipboard has text → return it synchronously, QML pastes immediately.
4. Worker thread: `QImage` → PNG bytes → `tesseract - - --psm 6 -l <lang>`
   → text. Emit `ocrComplete(text)` or `ocrStatus(msg, isError)` on failure.
5. QML `onOcrComplete` → `root.pasteText(text)` splices into the editor.
   Debounced autosave fires like any other edit.

## Pure module — `src/lazynote/ocr.py`

No PySide6 import (keeps the "pure modules stay unit-testable" rule). Operates
on raw `bytes`:

```python
class OcrUnavailable(RuntimeError): ...   # tesseract binary missing
class OcrFailed(RuntimeError): ...        # non-zero exit / stderr

def is_available() -> bool:
    return shutil.which("tesseract") is not None

def run_ocr(png_bytes: bytes, lang: str = "eng", psm: int = 6) -> str:
    """OCR PNG bytes via tesseract stdin→stdout. Returns text (may be empty).

    Raises OcrUnavailable if the binary is missing, OcrFailed on non-zero exit.
    """
    if not is_available():
        raise OcrUnavailable("tesseract not on PATH")
    result = subprocess.run(
        ["tesseract", "-", "-", "--psm", str(psm), "-l", lang],
        input=png_bytes, capture_output=True, timeout=30,
    )
    if result.returncode != 0:
        msg = result.stderr.decode("utf-8", "replace").strip()
        raise OcrFailed(msg or f"tesseract exit {result.returncode}")
    return result.stdout.decode("utf-8", "replace").strip()
```

`--psm 6` (assume a single uniform block of text) is the right default for
screen text. No post-processing in v1 — Tesseract output goes in raw; screen
text is usually clean enough. We can add line-join / whitespace-collapse later.

## Bridge API — `bridge.py`

New signals + slot, mirroring the existing theme/font property style:

- `ocrComplete = Signal(str)` — recognized text (empty handled by caller).
- `ocrStatus = Signal(str, bool)` — `(message, isError)` for toasts.

```python
@Slot(result=str)
def paste_or_ocr(self) -> str:
    """Ctrl+V handler. Returns text to paste now, or "" to wait for OCR.

    image on clipboard → "", starts async OCR; result via ocrComplete.
    text on clipboard  → returns it; QML pastes immediately.
    empty clipboard    → "".
    """
    cb = QGuiApplication.clipboard()
    img = cb.image()
    if not img.isNull():
        self.ocrStatus.emit("Recognizing…", False)
        self._start_ocr(img)
        return ""
    return cb.text()

def _start_ocr(self, image):
    buf = QBuffer(); buf.open(QIODevice.WriteOnly)
    image.save(buf, "PNG")
    png = bytes(buf.data())
    lang = store.get_settings().get("ocr_lang") or "eng"
    threading.Thread(target=self._ocr_worker, args=(png, lang), daemon=True).start()

def _ocr_worker(self, png, lang):
    try:
        text = ocr.run_ocr(png, lang=lang)
    except ocr.OcrUnavailable:
        self.ocrStatus.emit("OCR needs tesseract: sudo apt install tesseract-ocr", True); return
    except ocr.OcrFailed as e:
        self.ocrStatus.emit(f"OCR failed: {e}", True); return
    except Exception as e:
        self.ocrStatus.emit(f"OCR failed: {e}", True); return
    if not text:
        self.ocrStatus.emit("No text recognized", True); return
    self.ocrComplete.emit(text)
```

Qt auto-selects a queued connection for cross-thread signal emission, so
`ocrComplete`/`ocrStatus` deliver to the GUI thread without an explicit
`QueuedConnection` — same pattern `shortcuts.py` relies on.

## Editor — `qml/Editor.qml`

**Paste interception** in the cursor line's `TextInput.Keys.onPressed`:

```javascript
if ((e.modifiers & Qt.ControlModifier) && e.key === Qt.Key_V) {
    var t = backend.paste_or_ocr()
    if (t !== "") root.pasteText(t)   // text clipboard: paste now
    e.accepted = true                 // suppress default paste either way
}
```

**`pasteText(text)`** — generalizes the existing `splitLine` to N lines, using
the same `lines[]` / `pushEdit` / `ensureEditor` contract (safe with the
`onTextChanged` `if (text !== root.lines[row.index])` feedback-loop guard and
the `syncing` flag in `pushEdit`):

```javascript
function pasteText(text) {
    if (text === "") return
    var parts = text.split("\n")
    var line = lines[cursorLine], col = cursorCol
    var head = line.substring(0, col), tail = line.substring(col)
    var arr = lines.slice()
    if (parts.length === 1) {
        arr[cursorLine] = head + parts[0] + tail
        lines = arr
        cursorCol = col + parts[0].length
        pushEdit(); ensureEditor()
    } else {
        var first = head + parts[0]
        var last = parts[parts.length - 1] + tail
        var middle = parts.slice(1, -1)
        arr.splice(cursorLine, 1, first, ...middle, last)
        lines = arr
        cursorLine = cursorLine + parts.length - 1
        cursorCol = parts[parts.length - 1].length
        list.model = lines.length
        pushEdit(); Qt.callLater(ensureEditor)
    }
}
```

Cursor ends at the end of the pasted text (standard paste behavior). Insertion
obeys the text protocol — if the first pasted line is `todo` / `#`-prefixed,
mode detection reacts, which is correct.

**Signal connections** at the root level:

```javascript
Connections {
    target: backend
    function onOcrComplete(text) { root.pasteText(text) }
    function onOcrStatus(msg, isError) { /* show in the existing status surface */ }
}
```

Status reuses the editor's existing status surface (where "saved" lives). If
no dedicated status element exists today, add a small transient label that
fades after a few seconds — minimal, matching the app's quiet aesthetic.

## Error / edge-case matrix

| Situation | Behavior |
|---|---|
| `tesseract` not installed | Toast: "OCR needs tesseract: `sudo apt install tesseract-ocr`", no insertion |
| Missing language data (`ocr_lang=fra` but no `fra.traineddata`) | Toast: "OCR failed: …" (Tesseract's stderr is descriptive) |
| OCR returns empty string | Toast: "No text recognized" |
| Clipboard has both image + text | Image wins → OCR path (intentional — that's the feature) |
| Clipboard empty | `paste_or_ocr` returns `""`, nothing pasted, no toast |
| User takes another screenshot while OCR runs | Last writer wins; v1 accepts interleaving, guard only if it bites |

## Settings

- `ocr_lang` in `app_settings`, default `eng`. No settings UI for v1 (YAGNI).
  Wire into the settings popup later only if language switching is actually
  needed.

## Packaging

`tesseract-ocr` as **`Recommends:`** (not `Depends:`) in the `.deb` — installs
by default on apt-based systems but doesn't break the package if absent;
`tesseract-ocr-eng` is a dependency of `tesseract-ocr` on Debian/Ubuntu, so the
one `Recommends` covers both. The app degrades to a clear "install tesseract"
toast. Non-deb users get the toast with the install command.

## Test surface

| What | How | Pure? |
|---|---|---|
| `ocr.is_available()` | mock `shutil.which` → assert True/False | ✅ no Qt |
| `ocr.run_ocr` happy path | mock `subprocess.run` canned stdout → assert text | ✅ no Qt |
| `ocr.run_ocr` missing binary | `shutil.which` → None → raises `OcrUnavailable` | ✅ no Qt |
| `ocr.run_ocr` non-zero exit | mock returncode=1 → raises `OcrFailed` | ✅ no Qt |
| `ocr.run_ocr` empty output | mock returns b"" → returns `""` | ✅ no Qt |
| Multi-line `pasteText` splice | run the app (offscreen smoke + real run) | ❌ QML |

Pure `ocr.py` is the unit-testable core (TDD, like `parse/*`, `highlight.py`,
`geometry.py`, `db.py`). Editor paste splice and bridge clipboard/signal
wiring are verified by running the app — matches the project's convention:
**TDD for pure modules, run-the-app for QML glue.**

## Files

```
src/lazynote/
  ocr.py            NEW   — pure OCR module (subprocess + tesseract)
  bridge.py         CHG   — paste_or_ocr slot, _ocr_worker thread, signals
  qml/Editor.qml    CHG   — Ctrl+V interception, pasteText(), signal handlers
tests/
  test_ocr.py       NEW   — unit tests for ocr.py
pyproject.toml      (no change — no new deps)
packaging/          CHG   — .deb Recommends: tesseract-ocr
```
