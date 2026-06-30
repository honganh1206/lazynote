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
    title: "Antinote"
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property bool slashActive: backend && backend.content.split("\n")[0] === "/"
    onSlashActiveChanged: slashActive ? picker.open() : picker.close()

    Connections {
        target: backend
        function onToggleWindowRequested() { win.toggleVisible() }
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
        tooltip: "Antinote"
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
            Platform.MenuItem { text: "Quit"; onTriggered: { backend.flush(); Qt.quit() } }
        }
    }

    Shortcut { sequence: "Ctrl+H"; onActivated: backend.navigate(-1) }
    Shortcut { sequence: "Ctrl+L"; onActivated: backend.navigate(1) }
    Shortcut { sequence: "Ctrl+N"; onActivated: backend.new_note() }
    Shortcut { sequence: "Ctrl+D"; onActivated: backend.delete_current() }

    Rectangle {
        id: panel
        anchors.fill: parent
        color: "#1f2023"
        radius: 10

        Rectangle {
            id: dragStrip
            height: 16
            color: "transparent"
            anchors { left: parent.left; right: parent.right; top: parent.top }
            MouseArea {
                anchors.fill: parent
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

        Text {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: 12
            anchors.bottomMargin: 8
            color: "#6f6b64"
            font.pixelSize: 11
            text: backend
                  ? (backend.mode ? backend.mode + " · " : "") + (backend.index + 1) + "/" + backend.count
                  : ""
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

    Component.onCompleted: {
        backend.load()
        var aot = backend.setting_get("always_on_top") !== "false"
        win.flags = Qt.Window | Qt.FramelessWindowHint | (aot ? Qt.WindowStaysOnTopHint : 0)
        editor.focusEditor()
    }
}
