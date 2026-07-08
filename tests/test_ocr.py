from lazynote import ocr


def test_is_available_true_when_on_path(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: "/usr/bin/tesseract")
    assert ocr.is_available() is True


def test_is_available_false_when_missing(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: None)
    assert ocr.is_available() is False
