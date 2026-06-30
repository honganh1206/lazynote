import QtQuick
import QtQuick.Controls

// Scaffold window. The frameless/rounded/always-on-top chrome is built in a
// later task; this just proves the engine loads and renders.
ApplicationWindow {
    id: root
    width: 400
    height: 400
    visible: true
    title: "Antinote"

    Rectangle {
        anchors.fill: parent
        color: "#1f2023"
        radius: 10

        Text {
            anchors.centerIn: parent
            text: "Antinote"
            color: "#d6d3cc"
            font.pixelSize: 18
        }
    }
}
