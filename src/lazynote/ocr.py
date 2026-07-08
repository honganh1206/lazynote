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
