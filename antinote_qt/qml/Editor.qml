import QtQuick
import QtQuick.Controls

// Option A editor: a TextArea whose document is colored by a Python
// QSyntaxHighlighter (attached via backend.attach_highlighter).
ScrollView {
    id: root
    clip: true

    TextArea {
        id: area
        wrapMode: TextArea.Wrap
        selectByMouse: true
        persistentSelection: true
        color: "#d6d3cc"
        selectionColor: "#34363b"
        font.pixelSize: 15
        leftPadding: 14
        topPadding: 10
        rightPadding: 14
        background: Rectangle { color: "transparent" }

        function updateCursorLine() {
            var line = text.substring(0, cursorPosition).split("\n").length - 1
            backend.set_cursor_line(line)
        }

        Component.onCompleted: {
            text = backend.content
            backend.attach_highlighter(textDocument)
        }

        onTextChanged: {
            if (text !== backend.content)
                backend.edit(text)
            backend.refresh_highlight()
            updateCursorLine()
        }

        onCursorPositionChanged: updateCursorLine()

        // When the backend changes content (navigate / new / delete / slash),
        // pull the new text in. The guard prevents an edit→content→set loop.
        Connections {
            target: backend
            function onContentChanged() {
                if (area.text !== backend.content)
                    area.text = backend.content
            }
        }
    }
}
