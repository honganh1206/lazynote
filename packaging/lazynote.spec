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
#
# Size note: we do NOT collect_all("PySide6"). PyInstaller's built-in PySide6
# hook collects only the Qt modules/plugins/QML actually imported. collect_all
# would force the entire Qt stack (WebEngine, Qt3D, Charts, Multimedia,
# QtQuick3D, Designer...) into the bundle -> ~200MB. The excludes below drop
# heavy modules even if something pulls them in transitively. The app uses
# QtCore/Gui/Widgets/Qml/Quick/QuickControls2 (+ Network/DBus/OpenGL); it stores
# data via stdlib sqlite3, not QtSql.

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("lazynote")  # qml/*.qml + icon.png

# Qt modules this app never uses; excluding keeps them out of the bundle.
excludes = [
    "tkinter",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtQuick3D",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtDesigner",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtBluetooth",
    "PySide6.QtPositioning",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
]

a = Analysis(
    ["../src/lazynote/__main__.py"],
    pathex=["../src"],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    excludes=excludes,
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
    strip=True,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    name="lazynote",
)
