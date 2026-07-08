from lazynote import ocr
from types import SimpleNamespace


def test_is_available_true_when_on_path(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: "/usr/bin/tesseract")
    assert ocr.is_available() is True


def test_is_available_false_when_missing(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: None)
    assert ocr.is_available() is False


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
