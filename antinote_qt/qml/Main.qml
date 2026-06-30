import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: win
    width: 400
    height: 400
    minimumWidth: 360
    minimumHeight: 360
    visible: true
    title: "Antinote"
    color: "#1f2023"

    Shortcut { sequence: "Ctrl+H"; onActivated: backend.navigate(-1) }
    Shortcut { sequence: "Ctrl+L"; onActivated: backend.navigate(1) }
    Shortcut { sequence: "Ctrl+N"; onActivated: backend.new_note() }
    Shortcut { sequence: "Ctrl+D"; onActivated: backend.delete_current() }

    Editor {
        anchors.fill: parent
        anchors.margins: 6
        anchors.bottomMargin: 22
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

    Component.onCompleted: backend.load()
}
