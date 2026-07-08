# Clipboard OCR (Screenshot → Text) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Press Ctrl+V in Lazynote; if the clipboard holds a screenshot image, OCR it with Tesseract and insert the recognized text at the cursor (multi-line preserved); if it holds text, paste normally.

**Architecture:** A pure `ocr.py` module wraps the `tesseract` CLI via `subprocess` (stdin PNG bytes → stdout text). The bridge's `paste_or_ocr()` slot inspects the clipboard: image → encode to PNG via `QBuffer`, run OCR on a daemon worker thread, emit `ocrComplete(text)` back to the GUI thread; text → return synchronously. The bespoke per-line editor intercepts Ctrl+V, calls the slot, and splices multi-line text into its `lines[]` array via a new `pasteText()` (generalizing the existing `splitLine`).

**Tech Stack:** Python 3.12, PySide6 (Qt 6), QML, `tesseract` CLI (external), `subprocess` + `shutil` + `threading` (stdlib), pytest.

**Design doc:** `docs/plans/2026-07-08-clipboard-ocr-design.md`

**Conventions (from AGENTS.md):**
- Pure modules must NOT import PySide6 (unit-testable under plain pytest).
- TDD for pure modules; QML glue verified by running the app (offscreen smoke).
- Conventional Commits; stage only the files you changed (no `git add -A`).
- `QT_QPA_PLATFORM=offscreen pytest -q` runs tests; `ruff check .` lints.

---

### Task 1: Scaffold the pure `ocr.py` module + first failing test

**Files:**
- Create: `src/lazynote/ocr.py`
- Create: `tests/test_ocr.py`

**Step 1: Write the failing test** (`tests/test_ocr.py`)

```python
from lazynote import ocr


def test_is_available_true_when_on_path(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: "/usr/bin/tesseract")
    assert ocr.is_available() is True


def test_is_available_false_when_missing(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: None)
    assert ocr.is_available() is False
```

**Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen pytest -q tests/test_ocr.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'lazynote.ocr'`

**Step 3: Write minimal implementation** (`src/lazynote/ocr.py`)

```python
"""OCR via the tesseract CLI (stdin PNG bytes → stdout text).

Pure module: no PySide6 import, so it's unit-testable under plain pytest.
"""

from __future__ import annotations

import shutil
import subprocess

# Raised when the tesseract binary is not on PATH.
class OcrUnavailable(RuntimeError):
    pass


# Raised when tesseract exits non-zero (bad image, missing language data, ...).
class OcrFailed(RuntimeError):
    pass


def is_available() -> bool:
    """True if the tesseract binary is on PATH."""
    return shutil.which("tesseract") is not None
```

**Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen pytest -q tests/test_ocr.py`
Expected: PASS (2 tests).

**Step 5: Lint**

Run: `ruff check src/lazynote/ocr.py tests/test_ocr.py`
Expected: clean.

**Step 6: Commit**

```bash
git add src/lazynote/ocr.py tests/test_ocr.py
git commit -m "feat: add pure ocr module scaffold with is_available"
```

---

### Task 2: Implement `run_ocr` — happy path (TDD)

**Files:**
- Modify: `src/lazynote/ocr.py`
- Modify: `tests/test_ocr.py`

**Step 1: Write the failing test**

Append to `tests/test_ocr.py`:

```python
import subprocess
from types import SimpleNamespace


def _fake_run(stdout=b"hello world\n", returncode=0, stderr=b""):
    def _run(cmd, input=None, capture_output=False, timeout=None):
        return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)
    return _run


def test_run_ocr_returns_stdout_text(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: "/usr/bin/tesseract")
    monkeypatch.setattr(ocr.subprocess, "run", _fake_run(stdout=b"hello world\n"))
    assert ocr.run_ocr(b"\x89PNG fake") == "hello world"


def test_run_ocr_strips_trailing_whitespace(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: "/usr/bin/tesseract")
    monkeypatch.setattr(ocr.subprocess, "run", _fake_run(stdout=b"  line1\nline2  \n"))
    assert ocr.run_ocr(b"img") == "line1\nline2"


def test_run_ocr_passes_lang_and_psm(monkeypatch):
    seen = {}
    def _run(cmd, input=None, capture_output=False, timeout=None):
        seen["cmd"] = cmd
        return SimpleNamespace(stdout=b"x", stderr=b"", returncode=0)
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: "/usr/bin/tesseract")
    monkeypatch.setattr(ocr.subprocess, "run", _run)
    ocr.run_ocr(b"img", lang="fra", psm=3)
    assert seen["cmd"] == ["tesseract", "-", "-", "--psm", "3", "-l", "fra"]
```

**Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen pytest -q tests/test_ocr.py`
Expected: FAIL — `AttributeError: module 'lazynote.ocr' has no attribute 'run_ocr'`.

**Step 3: Write minimal implementation**

Append to `src/lazynote/ocr.py`:

```python
def run_ocr(png_bytes: bytes, lang: str = "eng", psm: int = 6) -> str:
    """OCR PNG bytes via tesseract stdin→stdout. Returns text (may be empty).

    Raises OcrUnavailable if the binary is missing, OcrFailed on non-zero exit.
    """
    if not is_available():
        raise OcrUnavailable("tesseract not on PATH")
    result = subprocess.run(
        ["tesseract", "-", "-", "--psm", str(psm), "-l", lang],
        input=png_bytes,
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        msg = result.stderr.decode("utf-8", "replace").strip()
        raise OcrFailed(msg or f"tesseract exit {result.returncode}")
    return result.stdout.decode("utf-8", "replace").strip()
```

**Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen pytest -q tests/test_ocr.py`
Expected: PASS (all tests so far).

**Step 5: Lint**

Run: `ruff check src/lazynote/ocr.py tests/test_ocr.py`
Expected: clean.

**Step 6: Commit**

```bash
git add src/lazynote/ocr.py tests/test_ocr.py
git commit -m "feat: implement ocr.run_ocr happy path via tesseract stdin/stdout"
```

---

### Task 3: `run_ocr` error cases (TDD)

**Files:**
- Modify: `tests/test_ocr.py`
- Modify: `src/lazynote/ocr.py` (no change expected — already raises correctly)

**Step 1: Write the failing tests**

Append to `tests/test_ocr.py`:

```python
def test_run_ocr_raises_when_binary_missing(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: None)
    try:
        ocr.run_ocr(b"img")
    except ocr.OcrUnavailable:
        return
    raise AssertionError("expected OcrUnavailable")


def test_run_ocr_raises_ocrfailed_on_nonzero_exit(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: "/usr/bin/tesseract")
    monkeypatch.setattr(
        ocr.subprocess, "run", _fake_run(returncode=1, stderr=b"bad image")
    )
    try:
        ocr.run_ocr(b"img")
    except ocr.OcrFailed as e:
        assert "bad image" in str(e)
        return
    raise AssertionError("expected OcrFailed")


def test_run_ocr_empty_output_returns_empty_string(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: "/usr/bin/tesseract")
    monkeypatch.setattr(ocr.subprocess, "run", _fake_run(stdout=b""))
    assert ocr.run_ocr(b"img") == ""
```

**Step 2: Run tests to verify they pass (implementation already correct)**

Run: `QT_QPA_PLATFORM=offscreen pytest -q tests/test_ocr.py`
Expected: PASS (all). These tests lock in the error contract.

**Step 3: Lint**

Run: `ruff check src/lazynote/ocr.py tests/test_ocr.py`
Expected: clean.

**Step 4: Commit**

```bash
git add tests/test_ocr.py
git commit -m "test: cover ocr error cases (missing binary, nonzero exit, empty)"
```

---

### Task 4: Add `pasteText()` to the editor (QML, multi-line splice)

**Files:**
- Modify: `src/lazynote/qml/Editor.qml` (add `pasteText` near `splitLine`, ~line 97)

**Step 1: Add the `pasteText` function**

In `Editor.qml`, immediately after the `joinWithPrev` function (after line 112), insert:

```javascript
    // Multi-line paste at the cursor. Generalizes splitLine to N lines using
    // the same lines[]/pushEdit/ensureEditor contract (safe with the
    // onTextChanged "if (text !== root.lines[row.index])" guard and the
    // syncing flag in pushEdit).
    function pasteText(text) {
        if (text === "")
            return
        var parts = text.split("\n")
        var line = lines[cursorLine]
        var col = cursorCol
        var head = line.substring(0, col)
        var tail = line.substring(col)
        var arr = lines.slice()
        if (parts.length === 1) {
            arr[cursorLine] = head + parts[0] + tail
            lines = arr
            cursorCol = col + parts[0].length
            pushEdit()
            ensureEditor()
        } else {
            var first = head + parts[0]
            var last = parts[parts.length - 1] + tail
            var middle = parts.slice(1, -1)
            arr.splice(cursorLine, 1, first, ...middle, last)
            lines = arr
            cursorLine = cursorLine + parts.length - 1
            cursorCol = parts[parts.length - 1].length
            list.model = lines.length
            pushEdit()
            Qt.callLater(ensureEditor)
        }
    }
```

**Step 2: Smoke-verify the QML still loads**

Run: `QT_QPA_PLATFORM=offscreen python -m lazynote` (with a display or offscreen; this is a smoke load — it should not crash).
Expected: app constructs without QML errors. (If offscreen produces no window, lack of a traceback is success.)

**Step 3: Lint**

Run: `ruff check .` (no Python changed, should stay clean).

**Step 4: Commit**

```bash
git add src/lazynote/qml/Editor.qml
git commit -m "feat: add pasteText() multi-line splice to bespoke editor"
```

---

### Task 5: Wire the bridge — `paste_or_ocr` slot + OCR worker + signals

**Files:**
- Modify: `src/lazynote/bridge.py`

**Step 1: Add imports**

At the top of `bridge.py`, extend the existing imports. Add to the `QtCore` import line (line 11) the symbols `QBuffer`, `QImage`, `QIODevice` — note `QImage`/`QBuffer`/`QIODevice` are in `PySide6.QtCore`. Also add `import threading`.

Concretely, change line 11 from:

```python
from PySide6.QtCore import Property, Qt, QObject, QTimer, QUrl, Signal, Slot
```

to:

```python
from PySide6.QtCore import (
    Property, Qt, QObject, QTimer, QUrl, Signal, Slot,
    QBuffer, QImage, QIODevice,
)
```

And add near the top stdlib imports:

```python
import threading
```

Add the `ocr` import with the other `lazynote` imports (line 14):

```python
from lazynote import fonts, obsidian, ocr, store, theme
```

**Step 2: Add the two new signals**

In the `Backend` class signal block (after `linkSettingsChanged = Signal()` around line 31), add:

```python
    ocrComplete = Signal(str)        # recognized text
    ocrStatus = Signal(str, bool)    # (message, isError)
```

**Step 3: Add the `paste_or_ocr` slot + worker**

Add these methods to the `Backend` class (e.g. after `toggle_checkbox`, at the end of the class):

```python
    # ---- clipboard OCR ----
    @Slot(result=str)
    def paste_or_ocr(self) -> str:
        """Ctrl+V handler. Returns text to paste now, or "" to wait for OCR.

        - clipboard has an image → "", starts async OCR; result via ocrComplete.
        - clipboard has text → returns it; QML pastes immediately.
        - empty clipboard → "".
        """
        cb = QGuiApplication.clipboard()
        img = cb.image()
        if not img.isNull():
            self.ocrStatus.emit("Recognizing…", False)
            self._start_ocr(img)
            return ""
        return cb.text()

    def _start_ocr(self, image: QImage) -> None:
        """Encode the image to PNG on the GUI thread, then OCR on a worker."""
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        image.save(buf, "PNG")
        png = bytes(buf.data())
        lang = store.get_settings().get("ocr_lang") or "eng"
        t = threading.Thread(target=self._ocr_worker, args=(png, lang), daemon=True)
        t.start()

    def _ocr_worker(self, png: bytes, lang: str) -> None:
        """Runs on a daemon thread; emits signals delivered to the GUI thread."""
        try:
            text = ocr.run_ocr(png, lang=lang)
        except ocr.OcrUnavailable:
            self.ocrStatus.emit(
                "OCR needs tesseract: sudo apt install tesseract-ocr", True
            )
            return
        except ocr.OcrFailed as e:
            self.ocrStatus.emit(f"OCR failed: {e}", True)
            return
        except Exception as e:
            self.ocrStatus.emit(f"OCR failed: {e}", True)
            return
        if not text:
            self.ocrStatus.emit("No text recognized", True)
            return
        self.ocrComplete.emit(text)
```

**Step 4: Smoke-verify the bridge imports cleanly**

Run: `QT_QPA_PLATFORM=offscreen python -m lazynote`
Expected: no traceback; app constructs.

Also run the existing bridge tests to confirm nothing broke:
Run: `QT_QPA_PLATFORM=offscreen pytest -q tests/test_bridge.py`
Expected: PASS (unchanged).

**Step 5: Lint**

Run: `ruff check src/lazynote/bridge.py`
Expected: clean.

**Step 6: Commit**

```bash
git add src/lazynote/bridge.py
git commit -m "feat: add paste_or_ocr slot + async OCR worker to bridge"
```

---

### Task 6: Intercept Ctrl+V in the editor and connect the OCR signals

**Files:**
- Modify: `src/lazynote/qml/Editor.qml`

**Step 1: Add a Ctrl+V handler in the `TextInput.Keys.onPressed` block**

In `Editor.qml`, the `TextInput`'s `Keys.onPressed` (around line 316) currently handles Backspace/Up/Down. Add a Ctrl+V branch at the top of that handler:

Change:

```javascript
                    Keys.onPressed: function (e) {
                        if (e.key === Qt.Key_Backspace && cursorPosition === 0 && selectionStart === selectionEnd) {
```

to:

```javascript
                    Keys.onPressed: function (e) {
                        if ((e.modifiers & Qt.ControlModifier) && e.key === Qt.Key_V) {
                            var t = backend.paste_or_ocr()
                            if (t !== "")
                                root.pasteText(t)
                            e.accepted = true
                        } else if (e.key === Qt.Key_Backspace && cursorPosition === 0 && selectionStart === selectionEnd) {
```

(The rest of the Backspace/Up/Down branches stay unchanged — they're already `else if` chains.)

**Step 2: Connect the OCR signals at the root level**

In `Editor.qml`, add a new `Connections` block alongside the existing `backend` `Connections` (after the `onContentChanged` block, ~line 140):

```javascript
    // OCR result/feedback from the bridge's async worker.
    Connections {
        target: backend
        function onOcrComplete(text) { root.pasteText(text) }
        function onOcrStatus(msg, isError) { root.showOcrStatus(msg, isError) }
    }
```

**Step 3: Smoke-verify**

Run: `QT_QPA_PLATFORM=offscreen python -m lazynote`
Expected: no traceback.

**Step 4: Lint**

Run: `ruff check .` (no Python changed).

**Step 5: Commit**

```bash
git add src/lazynote/qml/Editor.qml
git commit -m "feat: intercept Ctrl+V for image→OCR paste and wire ocr signals"
```

---

### Task 7: Add a transient OCR status surface in the editor

The design calls for reusing the editor's existing status surface ("where 'saved' lives"). First verify whether one exists; if not, add a minimal transient label.

**Files:**
- Modify: `src/lazynote/qml/Editor.qml`
- Possibly: `src/lazynote/qml/Main.qml` (only if the status surface lives there)

**Step 1: Search for an existing status surface**

Run: `grep -nE 'saved|status|ocrStatus|showOcrStatus' src/lazynote/qml/*.qml`
Inspect what (if anything) already surfaces transient status text. The `showOcrStatus(msg, isError)` function referenced in Task 6 does not exist yet — this task defines it.

**Step 2: Add a `showOcrStatus` function + a transient label**

If a status `Text` already exists in `Editor.qml` or `Main.qml`, route `showOcrStatus` to it. Otherwise, add a minimal transient label in `Editor.qml`. Add near the `pasteText` function:

```javascript
    property string ocrStatusText: ""
    property bool ocrStatusError: false

    function showOcrStatus(msg, isError) {
        if (msg === "") {
            ocrStatusText = ""
            return
        }
        ocrStatusText = msg
        ocrStatusError = isError
        statusFade.restart()
    }
```

And add a `Text` element at the bottom of the `ListView`'s parent `Item` (root), positioned unobtrusively (e.g. bottom-left), styled with `colMuted` / red for errors, fading after ~3s:

```qml
    Text {
        id: ocrStatusLabel
        text: root.ocrStatusText
        color: root.ocrStatusError ? "#d97757" : root.colMuted
        font.family: root.fnt.family
        font.pixelSize: root.fnt.size - 2
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 8
        opacity: 0
        Behavior on opacity { NumberAnimation { duration: 160 } }
        Timer {
            id: statusFade
            interval: 3000
            repeat: false
            onTriggered: root.ocrStatusText = ""
        }
        onTextChanged: parent.opacity = text === "" ? 0 : 1
        // keep label visible while it has text; fade when text clears
    }
```

Note: the `onTextChanged: parent.opacity` trick is awkward — simpler is to bind `opacity` directly:

```qml
    Text {
        id: ocrStatusLabel
        text: root.ocrStatusText
        color: root.ocrStatusError ? "#d97757" : root.colMuted
        font.family: root.fnt.family
        font.pixelSize: root.fnt.size - 2
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 8
        opacity: root.ocrStatusText === "" ? 0 : 1
        Behavior on opacity { NumberAnimation { duration: 160 } }
        Timer {
            id: statusFade
            interval: 3000
            onTriggered: root.ocrStatusText = ""
        }
    }
```

Use the second (binding) form. The `#d97757` is a warm error red consistent with the app's warm palette; adjust to match `theme.py` if a semantic error color exists.

**Step 3: Smoke-verify**

Run: `QT_QPA_PLATFORM=offscreen python -m lazynote`
Expected: no traceback.

**Step 4: Commit**

```bash
git add src/lazynote/qml/Editor.qml
# (add Main.qml too if you routed through it)
git commit -m "feat: add transient OCR status label in editor"
```

---

### Task 8: Add `tesseract-ocr` to the .deb `Recommends`

**Files:**
- Modify: `packaging/build-deb.sh` (the `control` heredoc, ~line 46)

**Step 1: Add a `Recommends` line**

In `packaging/build-deb.sh`, after the `Depends:` line in the heredoc (line 46), add:

```text
Recommends: tesseract-ocr
```

So the block becomes:

```text
Depends: libegl1, libgl1, libxkbcommon0, libdbus-1-3, libfontconfig1, libfreetype6, libxcb-cursor0
Recommends: tesseract-ocr
```

`tesseract-ocr-eng` (English language data) is a dependency of `tesseract-ocr` on Debian/Ubuntu, so the one `Recommends` covers both. We use `Recommends` (not `Depends`) so the package still installs if tesseract is absent; the app degrades to a clear "install tesseract" toast.

**Step 2: Verify the shell script is still syntactically valid**

Run: `bash -n packaging/build-deb.sh`
Expected: no output (valid syntax).

**Step 3: Commit**

```bash
git add packaging/build-deb.sh
git commit -m "packaging: recommend tesseract-ocr for clipboard OCR feature"
```

---

### Task 9: Final verification

**Step 1: Run the full test suite**

Run: `QT_QPA_PLATFORM=offscreen pytest -q`
Expected: PASS (all existing tests + new `test_ocr.py` tests).

**Step 2: Lint the whole repo**

Run: `ruff check .`
Expected: clean.

**Step 3: Headless smoke load**

Run: `QT_QPA_PLATFORM=offscreen python -m lazynote`
Expected: no traceback; engine constructs.

**Step 4: Manual end-to-end (requires a display + tesseract installed)**

If `tesseract` is installed, do a real run (not offscreen):

1. `sudo apt install tesseract-ocr` (if not already).
2. `python -m lazynote`.
3. Take a screenshot of some on-screen text with the DE tool (Print / Spectacle / Flameshot), copying to clipboard.
4. Focus Lazynote, place cursor, press Ctrl+V.
5. Confirm: "Recognizing…" appears, then the recognized text inserts at the cursor (multi-line preserved).
6. Copy some plain text, Ctrl+V in Lazynote → confirm normal text paste still works.
7. Uninstall tesseract (`sudo apt remove tesseract-ocr`), screenshot, Ctrl+V → confirm the "OCR needs tesseract: …" toast appears and nothing is inserted. Reinstall afterward.

**Step 5: Note any manual gaps**

If a display/tesseract isn't available in this environment, state plainly that Step 4 (manual end-to-end) was not run, and that the feature needs a real run before release. Do not claim it passed.

---

## Summary of done-when

- `tests/test_ocr.py` passes under `QT_QPA_PLATFORM=offscreen pytest -q` (pure module contract locked).
- `ruff check .` clean.
- Offscreen smoke load constructs without traceback.
- Manual end-to-end (if a display + tesseract are available): screenshot → Ctrl+V → text inserts; text paste still works; missing-tesseract toast degrades cleanly.
