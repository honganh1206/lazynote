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

from pathlib import PurePosixPath

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

# PyInstaller's PySide6.QtQml hook currently collects the whole Qt QML tree.
# That pulls in huge unused modules (WebEngine, Quick3D, Charts, Multimedia,
# VirtualKeyboard, ...), and their linked Qt libraries bypass Analysis.excludes.
# Keep only the Qt modules this app imports from Python/QML.
_keep_qt_libs = {
    "libicudata.so.73",
    "libicui18n.so.73",
    "libicuuc.so.73",
    "libQt6Core.so.6",
    "libQt6DBus.so.6",
    "libQt6EglFSDeviceIntegration.so.6",
    "libQt6EglFsKmsSupport.so.6",
    "libQt6Gui.so.6",
    "libQt6LabsPlatform.so.6",
    "libQt6Network.so.6",
    "libQt6OpenGL.so.6",
    "libQt6Qml.so.6",
    "libQt6QmlMeta.so.6",
    "libQt6QmlModels.so.6",
    "libQt6QmlWorkerScript.so.6",
    "libQt6Quick.so.6",
    "libQt6QuickControls2.so.6",
    "libQt6QuickControls2Basic.so.6",
    "libQt6QuickControls2BasicStyleImpl.so.6",
    "libQt6QuickControls2Impl.so.6",
    "libQt6QuickLayouts.so.6",
    "libQt6QuickTemplates2.so.6",
    "libQt6WaylandClient.so.6",
    "libQt6Widgets.so.6",
    "libQt6WlShellIntegration.so.6",
    "libQt6XcbQpa.so.6",
}

_keep_qml_roots = {
    "Qt/labs/platform",
    "QtCore",
    "QtQml",
    "QtQuick",
}

_keep_qml_paths = {
    "QtQuick/Controls",
    "QtQuick/Controls/Basic",
    "QtQuick/Controls/Basic/impl",
    "QtQuick/Controls/impl",
    "QtQuick/Layouts",
    "QtQuick/Templates",
    "QtQuick/Window",
}

_keep_plugin_files = {
    # Desktop platform backends: X11, Wayland, and offscreen for CI smoke tests.
    "platforms": {"libqxcb.so", "libqwayland.so", "libqoffscreen.so"},
    "xcbglintegrations": {"libqxcb-egl-integration.so", "libqxcb-glx-integration.so"},
    "wayland-decoration-client": {"libadwaita.so", "libbradient.so"},
    "wayland-graphics-integration-client": {"libqt-plugin-wayland-egl.so"},
    "wayland-shell-integration": {
        "libfullscreen-shell-v1.so",
        "libqt-shell.so",
        "libwl-shell-plugin.so",
        "libxdg-shell.so",
    },
    # Keep normal desktop text input; omit Qt virtual keyboard and embedded evdev plugins.
    "platforminputcontexts": {
        "libcomposeplatforminputcontextplugin.so",
        "libibusplatforminputcontextplugin.so",
    },
}

_keep_plugin_types = {
    "platforms",
    "wayland-decoration-client",
    "wayland-graphics-integration-client",
    "wayland-shell-integration",
    "xcbglintegrations",
}


def _qt_payload_entry_name(entry):
    # TOC entries are usually (dest_name, src_name, typecode), but some PyInstaller
    # APIs use (src, dest). Match against both path-like fields defensively.
    return tuple(str(part).replace("\\", "/") for part in entry[:2])


def _keep_qt_payload(entry):
    names = _qt_payload_entry_name(entry)
    for name in names:
        path = PurePosixPath(name)
        parts = path.parts

        if "PySide6" not in parts:
            return True

        if ".abi3.so" in path.name:
            return True

        if "PySide6" in parts and "Qt" in parts and "lib" in parts:
            return path.name in _keep_qt_libs

        if "PySide6" in parts and "Qt" in parts and "qml" in parts:
            rel = "/".join(parts[parts.index("qml") + 1 :])
            parent = str(PurePosixPath(rel).parent)
            if parent == ".":
                parent = PurePosixPath(rel).parts[0]
            return parent in _keep_qml_roots or any(
                parent == allowed
                or (allowed != "QtQuick/Controls" and parent.startswith(allowed + "/"))
                for allowed in _keep_qml_paths
            )

        if "PySide6" in parts and "Qt" in parts and "plugins" in parts:
            rel_parts = parts[parts.index("plugins") + 1 :]
            if not rel_parts or rel_parts[0] not in _keep_plugin_types:
                return False
            allowed_files = _keep_plugin_files.get(rel_parts[0])
            return allowed_files is None or path.name in allowed_files

        return True

    return True

a = Analysis(
    ["../src/lazynote/__main__.py"],
    pathex=["../src"],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    excludes=excludes,
    noarchive=False,
)

a.binaries = [entry for entry in a.binaries if _keep_qt_payload(entry)]
a.datas = [entry for entry in a.datas if _keep_qt_payload(entry)]

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
