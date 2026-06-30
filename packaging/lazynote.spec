# PyInstaller spec for Lazynote.
#
# Run from the repo root:
#   pip install pyinstaller .
#   pyinstaller --noconfirm packaging/lazynote.spec
#
# Produces a self-contained onedir bundle at dist/lazynote/ (executable: dist/lazynote/lazynote).
# build-deb.sh wraps that bundle into a .deb.
#
# `lazynote` must be importable (pip install .) so collect_data_files can find
# the packaged qml/*.qml and icon.png. They land at lazynote/qml and
# lazynote/icon.png inside the bundle, matching Path(__file__).parent / "qml"
# and the QML's ../icon.png at runtime.

from PyInstaller.utils.hooks import collect_all, collect_data_files

datas = collect_data_files("lazynote")  # qml/*.qml + icon.png
binaries = []
hiddenimports = []

# Pull in PySide6's Qt libs, plugins, and QML modules (QtQuick, Controls,
# Qt.labs.platform). The bundled PySide6 hook handles most of this; collect_all
# is the belt-and-suspenders version so QML imports resolve in the frozen app.
_d, _b, _h = collect_all("PySide6")
datas += _d
binaries += _b
hiddenimports += _h

a = Analysis(
    ["../src/lazynote/__main__.py"],
    pathex=["../src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="lazynote",
    console=False,
    strip=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="lazynote",
)
