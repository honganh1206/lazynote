"""OCR via the tesseract CLI (stdin PNG bytes → stdout text).

Pure module: no PySide6 import, so it's unit-testable under plain pytest.
"""

from __future__ import annotations

import shutil


# Raised when the tesseract binary is not on PATH.
class OcrUnavailable(RuntimeError):
    pass


# Raised when tesseract exits non-zero (bad image, missing language data, ...).
class OcrFailed(RuntimeError):
    pass


def is_available() -> bool:
    """True if the tesseract binary is on PATH."""
    return shutil.which("tesseract") is not None
