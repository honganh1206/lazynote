import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    modal: true
    focus: true
    padding: 14
    anchors.centerIn: Overlay.overlay

    background: Rectangle {
        color: backend ? backend.colors.bg : "#1f2023"
        border.color: backend ? backend.colors.selection : "#34363b"
        radius: 10
    }

    function apply() {
        if (backend) backend.set_font(familyBox.currentText, sizeSpin.value)
    }

    ColumnLayout {
        spacing: 10

        Text {
            text: "Font"
            color: backend ? backend.colors.muted : "#6f6b64"
            font.pixelSize: 12
        }

        ComboBox {
            id: familyBox
            Layout.preferredWidth: 240
            model: backend ? backend.mono_families() : []
            Component.onCompleted: {
                if (!backend) return
                var i = model.indexOf(backend.font.family)
                if (i >= 0) currentIndex = i
            }
            onActivated: root.apply()

            contentItem: Text {
                leftPadding: 8
                text: familyBox.displayText
                color: backend ? backend.colors.text : "#d6d3cc"
                font.pixelSize: 13
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            background: Rectangle {
                color: backend ? backend.colors.bg : "#1f2023"
                border.color: backend ? backend.colors.selection : "#34363b"
                radius: 6
            }
            popup: Popup {
                y: familyBox.height
                width: familyBox.width
                implicitHeight: Math.min(contentItem.implicitHeight, 240)
                padding: 1
                background: Rectangle {
                    color: backend ? backend.colors.bg : "#1f2023"
                    border.color: backend ? backend.colors.selection : "#34363b"
                    radius: 6
                }
                contentItem: ListView {
                    clip: true
                    implicitHeight: contentHeight
                    model: familyBox.popup.visible ? familyBox.delegateModel : null
                    ScrollIndicator.vertical: ScrollIndicator {}
                }
            }
            delegate: ItemDelegate {
                width: familyBox.width
                highlighted: familyBox.highlightedIndex === index
                contentItem: Text {
                    text: modelData
                    color: backend ? backend.colors.text : "#d6d3cc"
                    font.pixelSize: 13
                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    color: familyBox.highlightedIndex === index ? (backend ? backend.colors.selection : "#34363b") : "transparent"
                }
            }
        }

        RowLayout {
            spacing: 8
            Text {
                text: "Size"
                color: backend ? backend.colors.muted : "#6f6b64"
                font.pixelSize: 12
            }
            SpinBox {
                id: sizeSpin
                from: 8
                to: 32
                value: backend ? backend.font.size : 15
                onValueModified: root.apply()

                contentItem: Text {
                    text: sizeSpin.value
                    color: backend ? backend.colors.text : "#d6d3cc"
                    font.pixelSize: 13
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitWidth: 90
                    color: backend ? backend.colors.bg : "#1f2023"
                    border.color: backend ? backend.colors.selection : "#34363b"
                    radius: 6
                }
                up.indicator: Rectangle {
                    x: sizeSpin.width - width
                    height: sizeSpin.height
                    implicitWidth: 24
                    color: sizeSpin.up.pressed ? (backend ? backend.colors.selection : "#34363b") : "transparent"
                    Text { text: "+"; anchors.centerIn: parent; color: backend ? backend.colors.text : "#d6d3cc"; font.pixelSize: 15 }
                }
                down.indicator: Rectangle {
                    height: sizeSpin.height
                    implicitWidth: 24
                    color: sizeSpin.down.pressed ? (backend ? backend.colors.selection : "#34363b") : "transparent"
                    Text { text: "−"; anchors.centerIn: parent; color: backend ? backend.colors.text : "#d6d3cc"; font.pixelSize: 15 }
                }
            }
        }

        Text {
            text: "Links"
            color: backend ? backend.colors.muted : "#6f6b64"
            font.pixelSize: 12
        }

        ColumnLayout {
            spacing: 6

            CheckBox {
                id: shorteningBox
                text: "Shorten links"
                checked: backend ? backend.setting_get("link_shortening") !== "false" : true
                onCheckedChanged: backend.setting_set("link_shortening", checked ? "true" : "false")

                contentItem: Text {
                    leftPadding: shorteningBox.indicator.width + shorteningBox.spacing
                    text: shorteningBox.text
                    color: backend ? backend.colors.text : "#d6d3cc"
                    font.pixelSize: 13
                    verticalAlignment: Text.AlignVCenter
                }
                indicator.width: 16
                indicator.height: 16
            }

            CheckBox {
                id: hyperlinkBox
                text: "Enable link features"
                checked: backend ? backend.setting_get("hyperlink_features") !== "false" : true
                onCheckedChanged: backend.setting_set("hyperlink_features", checked ? "true" : "false")

                contentItem: Text {
                    leftPadding: hyperlinkBox.indicator.width + hyperlinkBox.spacing
                    text: hyperlinkBox.text
                    color: backend ? backend.colors.text : "#d6d3cc"
                    font.pixelSize: 13
                    verticalAlignment: Text.AlignVCenter
                }
                indicator.width: 16
                indicator.height: 16
            }

            Text {
                text: "Ctrl+Click opens · Ctrl+Shift+Click expands"
                color: backend ? backend.colors.muted : "#6f6b64"
                font.pixelSize: 11
            }
        }
    }
}
