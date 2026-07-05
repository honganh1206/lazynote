import QtQuick
import QtQuick.Controls
import Qt.labs.platform as Platform

ApplicationWindow {
    id: win
    width: 400
    height: 400
    minimumWidth: 360
    minimumHeight: 360
    visible: true
    title: "Lazynote"
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property bool slashActive: backend && backend.content.split("\n")[0] === "/"
    onSlashActiveChanged: slashActive ? picker.open() : picker.close()

    Connections {
        target: backend
        function onToggleWindowRequested() { win.toggleVisible() }
    }

    // Persist geometry (debounced). `restored` suppresses saves during startup restore.
    property bool restored: false
    Timer {
        id: geoSaveTimer
        interval: 500
        onTriggered: if (win.restored) backend.save_geometry(win.x, win.y, win.width, win.height)
    }
    onXChanged: geoSaveTimer.restart()
    onYChanged: geoSaveTimer.restart()
    onWidthChanged: geoSaveTimer.restart()
    onHeightChanged: geoSaveTimer.restart()

    // Auto-hide on blur (when enabled in settings).
    Timer { id: autoHideTimer; interval: 300; onTriggered: win.hide() }
    onActiveChanged: {
        if (!active) {
            backend.flush()
            if (backend.auto_hide_enabled()) autoHideTimer.restart()
        } else {
            autoHideTimer.stop()
        }
    }

    function toggleVisible() {
        if (win.visible) {
            win.hide()
        } else {
            win.show()
            win.raise()
            win.requestActivate()
        }
    }

    function setAlwaysOnTop(on) {
        win.flags = Qt.Window | Qt.FramelessWindowHint | (on ? Qt.WindowStaysOnTopHint : 0)
        backend.setting_set("always_on_top", on ? "true" : "false")
    }

    Platform.SystemTrayIcon {
        visible: true
        icon.source: Qt.resolvedUrl("../icon.png")
        tooltip: "Lazynote"
        menu: Platform.Menu {
            Platform.MenuItem { text: "Show/Hide"; onTriggered: win.toggleVisible() }
            Platform.MenuItem {
                text: "New Note"
                onTriggered: { win.show(); win.raise(); win.requestActivate(); backend.new_note() }
            }
            Platform.MenuSeparator {}
            Platform.MenuItem {
                text: "Toggle Always on Top"
                onTriggered: win.setAlwaysOnTop((win.flags & Qt.WindowStaysOnTopHint) === 0)
            }
            Platform.MenuItem { text: "Toggle Auto-hide"; onTriggered: backend.toggle_auto_hide() }
            Platform.MenuSeparator {}
            // Theme items are flat (not a submenu): Qt.labs.platform's DBus tray
            // menu corrupts the heap when a nested Menu sits between separators.
            Platform.MenuItem {
                text: "Theme: System"; checkable: true
                checked: backend && backend.theme === "system"
                onTriggered: backend.set_theme("system")
            }
            Platform.MenuItem {
                text: "Theme: Light"; checkable: true
                checked: backend && backend.theme === "light"
                onTriggered: backend.set_theme("light")
            }
            Platform.MenuItem {
                text: "Theme: Dark"; checkable: true
                checked: backend && backend.theme === "dark"
                onTriggered: backend.set_theme("dark")
            }
            Platform.MenuSeparator {}
            Platform.MenuItem {
                text: "Settings…"
                onTriggered: { win.show(); win.raise(); win.requestActivate(); settings.open() }
            }
            Platform.MenuSeparator {}
            Platform.MenuItem { text: "Quit"; onTriggered: { backend.flush(); Qt.quit() } }
        }
    }

    Shortcut { sequence: "Ctrl+H"; onActivated: backend.navigate(-1) }
    Shortcut { sequence: "Ctrl+L"; onActivated: backend.navigate(1) }
    Shortcut { sequence: "Ctrl+N"; onActivated: backend.new_note() }
    Shortcut { sequence: "Ctrl+D"; onActivated: backend.delete_current() }
    Shortcut { sequence: "Ctrl+,"; onActivated: settings.open() }

    Rectangle {
        id: panel
        anchors.fill: parent
        color: backend ? backend.colors.bg : "#1f2023"
        radius: 10

        Rectangle {
            id: dragStrip
            height: 16
            color: "transparent"
            anchors { left: parent.left; right: parent.right; top: parent.top }
            MouseArea {
                id: dragMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.OpenHandCursor
                onPressed: win.startSystemMove()
            }
        }

        Editor {
            id: editor
            anchors {
                left: parent.left; right: parent.right
                top: dragStrip.bottom; bottom: parent.bottom
                leftMargin: 6; rightMargin: 6; bottomMargin: 22
            }
        }

        // Hover-revealed top-edge controls, sharing the export button's reveal
        // idiom: hovering the drag strip reveals them; each button's own hit area
        // keeps the zone "hovered" while the cursor is on it. Buttons are disabled
        // when not revealed so clicks pass through to the drag strip for window
        // moving (no accidental close while dragging from a corner).
        Item {
            id: topZone
            anchors { left: panel.left; right: panel.right; top: panel.top }
            height: 28

            readonly property bool hovered:
                dragMouse.containsMouse
                || themeBtnArea.containsMouse
                || hideBtnArea.containsMouse
                || closeBtnArea.containsMouse

            function revealColor(base) {
                // Slightly brighter than the muted rest color so an active glyph reads.
                return backend ? backend.colors.text : base
            }

            // ---- theme toggle (top-left) ----
            MouseArea {
                id: themeBtnArea
                x: 4
                y: 0
                width: 28
                height: 28
                enabled: topZone.hovered
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: backend.toggle_theme()
            }
            Text {
                text: backend && backend.effectiveScheme === "dark" ? "☾" : "☀"
                color: topZone.revealColor("#d6d3cc")
                font.pixelSize: 15
                x: 12
                y: 6 + (topZone.hovered ? 0 : -8)
                opacity: topZone.hovered ? 1.0 : 0.0
                visible: opacity > 0.01
                Behavior on y { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                Behavior on opacity { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
            }

            // ---- close (rightmost) ----
            MouseArea {
                id: closeBtnArea
                anchors { right: parent.right; top: parent.top; rightMargin: 2; topMargin: 0 }
                width: 28
                height: 28
                enabled: topZone.hovered
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: { backend.flush(); Qt.quit() }
            }
            Text {
                text: "✕"
                color: closeBtnArea.containsMouse
                       ? "#e06c6c"   // danger red on hover, the standard close affordance
                       : (backend ? backend.colors.text : "#d6d3cc")
                font.pixelSize: 14
                anchors.right: parent.right
                anchors.rightMargin: 11
                y: 6 + (topZone.hovered ? 0 : -8)
                opacity: topZone.hovered ? 1.0 : 0.0
                visible: opacity > 0.01
                Behavior on y { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                Behavior on opacity { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                Behavior on color { ColorAnimation { duration: 120 } }
            }

            // ---- hide (just left of close) ----
            MouseArea {
                id: hideBtnArea
                anchors { right: closeBtnArea.left; top: parent.top; rightMargin: 0; topMargin: 0 }
                width: 28
                height: 28
                enabled: topZone.hovered
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: win.hide()
            }
            Text {
                text: "–"
                color: topZone.revealColor("#d6d3cc")
                font.pixelSize: 18
                anchors.right: closeBtnArea.left
                anchors.rightMargin: 7
                y: 2 + (topZone.hovered ? 0 : -8)
                opacity: topZone.hovered ? 1.0 : 0.0
                visible: opacity > 0.01
                Behavior on y { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                Behavior on opacity { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
            }
        }

        Text {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: 12
            anchors.bottomMargin: 8
            color: backend ? backend.colors.muted : "#6f6b64"
            font.pixelSize: 11
            text: backend
                  ? (backend.mode ? backend.mode + " · " : "") + (backend.index + 1) + "/" + backend.count
                  : ""
        }

        // Hover-revealed "Export to Obsidian" icon at the lower-left corner.
        // A thin trigger strip at the very bottom reveals the glyph; the icon's
        // own hit area keeps it visible while the cursor is on it. ↗ is the
        // conventional "export / open externally" arrow; pure glyph — no pill.
        Item {
            id: exportZone
            anchors { left: panel.left; right: panel.right; bottom: panel.bottom }
            height: 34

            // Trigger strip hugging the lower edge (full width).
            MouseArea {
                id: exportStrip
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 10
                hoverEnabled: true
            }

            readonly property bool hovered: exportStrip.containsMouse || exportBtnArea.containsMouse

            // Invisible hit target around the glyph (≈32px so it's easily clickable).
            MouseArea {
                id: exportBtnArea
                x: 4
                y: exportZone.height - 32
                width: 32
                height: 32
                enabled: exportZone.hovered
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: backend.export_obsidian()
            }

            Text {
                id: exportIcon
                text: "↗"
                color: backend ? backend.colors.text : "#d6d3cc"
                font.pixelSize: 15
                x: 12
                y: exportZone.height - 22 + (exportZone.hovered ? 0 : 8)
                opacity: exportZone.hovered ? 1.0 : 0.0
                visible: opacity > 0.01
                Behavior on y { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                Behavior on opacity { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
            }
        }

        // Bottom-right resize grip (frameless windows have no system grips).
        Rectangle {
            width: 16
            height: 16
            color: "transparent"
            anchors { right: parent.right; bottom: parent.bottom }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.SizeFDiagCursor
                onPressed: win.startSystemResize(Qt.RightEdge | Qt.BottomEdge)
            }
        }
    }

    SlashPicker {
        id: picker
        x: 24
        y: 30
        onChosen: function (keyword) {
            backend.slash_select(keyword)
            close()
            editor.focusEditor()
        }
    }

    SettingsPopup {
        id: settings
    }

    Component.onCompleted: {
        backend.load()
        var aot = backend.setting_get("always_on_top") !== "false"
        win.flags = Qt.Window | Qt.FramelessWindowHint | (aot ? Qt.WindowStaysOnTopHint : 0)
        var geo = backend.restore_geometry()
        if (geo.length === 4) {
            win.x = geo[0]; win.y = geo[1]; win.width = geo[2]; win.height = geo[3]
        }
        win.restored = true
        editor.focusEditor()
    }
}
