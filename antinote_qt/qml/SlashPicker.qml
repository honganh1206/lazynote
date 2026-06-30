import QtQuick
import QtQuick.Controls

// Animated keyword picker shown when the first line is a lone "/".
Popup {
    id: picker
    padding: 4
    focus: true
    closePolicy: Popup.NoAutoClose

    property var keywords: backend ? backend.keywords : []
    property int selected: 0
    signal chosen(string keyword)

    background: Rectangle {
        color: "#2a2b2f"
        border.color: "#3a3b40"
        radius: 6
    }

    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 90 }
        NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: 90; easing.type: Easing.OutCubic }
    }
    exit: Transition {
        NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 70 }
    }

    onOpened: { selected = 0; scope.forceActiveFocus() }

    contentItem: FocusScope {
        id: scope
        focus: true
        implicitWidth: col.implicitWidth
        implicitHeight: col.implicitHeight

        Keys.onPressed: function (e) {
            var n = picker.keywords.length
            if (n === 0) return
            if (e.key === Qt.Key_Down) {
                picker.selected = (picker.selected + 1) % n; e.accepted = true
            } else if (e.key === Qt.Key_Up) {
                picker.selected = (picker.selected - 1 + n) % n; e.accepted = true
            } else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) {
                picker.chosen(picker.keywords[picker.selected]); e.accepted = true
            } else if (e.key === Qt.Key_Escape) {
                picker.close(); e.accepted = true
            } else {
                var num = parseInt(e.text)
                if (!isNaN(num) && num >= 1 && num <= n) {
                    picker.chosen(picker.keywords[num - 1]); e.accepted = true
                }
            }
        }

        Column {
            id: col
            spacing: 2
            Repeater {
                model: picker.keywords
                delegate: Rectangle {
                    width: 192
                    height: 28
                    radius: 4
                    color: index === picker.selected ? "#34363b" : "transparent"
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        x: 10
                        text: modelData
                        color: "#d6d3cc"
                        font.pixelSize: 14
                        font.bold: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onEntered: picker.selected = index
                        onClicked: picker.chosen(modelData)
                    }
                }
            }
        }
    }
}
