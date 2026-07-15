import QtQuick
import QtQuick.Controls

// Bespoke per-line animated editor.
//
// The whole document text is the source of truth (`docText`), synced to the
// backend via backend.content / backend.edit. It
// is split into `lines`; each line is a ListView delegate. The line that holds
// the caret is an editable TextEdit showing the RAW text (so `/x` is visible &
// editable); every other line is rendered statically from backend.line_render()
// spans — real ☐/☑ glyphs, hidden `/x`, heading colours, dim italic comments,
// strikethrough for checked items, and clickable links. Enter splits a line,
// Backspace at column 0 joins, Up/Down carry the caret between lines, and the
// checkbox glyph toggles `/x` with a scale/opacity animation.
Item {
    id: root
    clip: true

    // ---- palette ----
    readonly property color colText: backend ? backend.colors.text : "#d6d3cc"
    readonly property color colMuted: backend ? backend.colors.muted : "#6f6b64"
    readonly property var fnt: backend ? backend.font : ({family: "", size: 15})

    // ---- document state (source of truth) ----
    property string docText: ""
    property var lines: [""]
    property int cursorLine: 0
    property int cursorCol: 0
    // Guards against edit -> contentChanged -> set feedback loops.
    property bool syncing: false

    function focusEditor() {
        list.forceActiveFocus()
        ensureEditor()
    }

    function rebuildLines() {
        lines = docText.split("\n")
        if (cursorLine > lines.length - 1)
            cursorLine = lines.length - 1
        if (cursorLine < 0)
            cursorLine = 0
        list.model = lines.length
        // Re-render every visible static delegate (cursor reveal may have moved).
        bumpVersion()
    }

    // A monotonically-rising token delegates watch to re-pull their render data.
    property int renderVersion: 0
    function bumpVersion() { renderVersion = renderVersion + 1 }

    function pushEdit() {
        syncing = true
        docText = lines.join("\n")
        backend.edit(docText)
        syncing = false
        bumpVersion()
    }

    // Focus the TextEdit for the current cursor line (after the delegate exists).
    function ensureEditor() {
        list.positionViewAtIndex(cursorLine, ListView.Contain)
        var it = list.itemAtIndex(cursorLine)
        if (it && it.editorRef)
            it.editorRef.takeFocus(cursorCol)
    }

    function moveToLine(target, col) {
        if (target < 0 || target > lines.length - 1)
            return
        cursorLine = target
        cursorCol = Math.min(col, lines[target].length)
        bumpVersion()           // old line becomes static, new line becomes editor
        Qt.callLater(ensureEditor)
    }

    function commitLine(idx, newText, newCol) {
        var arr = lines.slice()
        arr[idx] = newText
        lines = arr
        cursorCol = newCol
        pushEdit()
    }

    function splitLine(idx, col) {
        var line = lines[idx]
        var head = line.substring(0, col)
        var tail = line.substring(col)
        var arr = lines.slice()
        arr.splice(idx, 1, head, tail)
        lines = arr
        cursorLine = idx + 1
        cursorCol = 0
        list.model = lines.length
        pushEdit()
        Qt.callLater(ensureEditor)
    }

    function joinWithPrev(idx) {
        if (idx <= 0)
            return
        var arr = lines.slice()
        var prevLen = arr[idx - 1].length
        arr[idx - 1] = arr[idx - 1] + arr[idx]
        arr.splice(idx, 1)
        lines = arr
        cursorLine = idx - 1
        cursorCol = prevLen
        list.model = lines.length
        pushEdit()
        Qt.callLater(ensureEditor)
    }

    // Multi-line paste at the cursor. Generalizes splitLine to N lines using
    // the same lines[]/pushEdit/ensureEditor contract (safe with the
    // onTextChanged "if (text !== root.lines[row.index])" guard and the
    // syncing flag in pushEdit).
    function pasteText(text) {
        if (text === "")
            return
        var parts = text.split("\n")
        var line = lines[cursorLine]
        var col = cursorCol
        var head = line.substring(0, col)
        var tail = line.substring(col)
        var arr = lines.slice()
        if (parts.length === 1) {
            arr[cursorLine] = head + parts[0] + tail
            lines = arr
            cursorCol = col + parts[0].length
            pushEdit()
            ensureEditor()
        } else {
            var first = head + parts[0]
            var last = parts[parts.length - 1] + tail
            var middle = parts.slice(1, -1)
            arr.splice(cursorLine, 1, first, ...middle, last)
            lines = arr
            cursorLine = cursorLine + parts.length - 1
            cursorCol = parts[parts.length - 1].length
            list.model = lines.length
            pushEdit()
            Qt.callLater(ensureEditor)
        }
    }

    // Transient OCR status feedback (fleshed out in the status-label task).
    property string ocrStatusText: ""
    property bool ocrStatusError: false

    function showOcrStatus(msg, isError) {
        if (msg === "") {
            ocrStatusText = ""
            return
        }
        ocrStatusText = msg
        ocrStatusError = isError
        statusFade.restart()
    }

    Component.onCompleted: {
        docText = backend.content
        rebuildLines()
        Qt.callLater(focusEditor)
    }

    // Re-pull static span colors when the palette changes (content is unchanged,
    // so onContentChanged would short-circuit and leave stale colors).
    Connections {
        target: backend
        function onThemeChanged() { root.bumpVersion() }
        function onLinkSettingsChanged() { root.bumpVersion() }
    }

    // Pull external content changes (navigate / new / delete / slash / toggle).
    Connections {
        target: backend
        function onContentChanged() {
            if (root.syncing)
                return
            if (backend.content !== root.docText) {
                root.docText = backend.content
                root.rebuildLines()
                Qt.callLater(root.ensureEditor)
            }
        }
    }

    // OCR result/feedback from the bridge's async worker.
    Connections {
        target: backend
        function onOcrComplete(text) { root.pasteText(text) }
        function onOcrStatus(msg, isError) { root.showOcrStatus(msg, isError) }
    }

    ListView {
        id: list
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        anchors.topMargin: 14
        anchors.bottomMargin: 14
        model: 1
        spacing: 2
        clip: true
        focus: true
        boundsBehavior: Flickable.StopAtBounds

        // Clicking empty space below the lines drops the caret on the last line.
        MouseArea {
            anchors.fill: parent
            z: -1
            onClicked: root.moveToLine(root.lines.length - 1, root.lines[root.lines.length - 1].length)
        }

        delegate: Item {
            id: row
            width: list.width
            height: Math.max(rowText.implicitHeight,
                             editorLoader.item ? editorLoader.item.contentHeight : 0,
                             22)

            required property int index
            property bool isCursorLine: index === root.cursorLine
            // Re-fetch render data whenever the document version bumps.
            property int rv: root.renderVersion
            property var lineData: backend.line_render(index, root.cursorLine)
            onRvChanged: lineData = backend.line_render(index, root.cursorLine)

            // Expose the editor (when present) so root can focus it.
            property var editorRef: isCursorLine ? editorLoader.item : null

            // ---- checkbox glyph (todo items only) ----
            property string checkbox: lineData ? lineData.checkbox : ""
            Text {
                id: box
                visible: row.checkbox !== ""
                x: 0
                y: Math.max(0, (22 - implicitHeight) / 2)
                text: row.checkbox === "checked" ? "☑" : "☐"
                color: row.checkbox === "checked" ? root.colMuted : root.colText
                font.family: root.fnt.family
                font.pixelSize: root.fnt.size

                // Animate the check toggle.
                Behavior on text { SequentialAnimation {
                    NumberAnimation { target: box; property: "scale"; to: 0.6; duration: 70 }
                    NumberAnimation { target: box; property: "scale"; to: 1.0; duration: 130; easing.type: Easing.OutBack }
                } }

                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -3
                    cursorShape: Qt.PointingHandCursor
                    onClicked: backend.toggle_checkbox(row.index)
                }
            }

            property real textLeft: row.checkbox !== "" ? 22 : 0

            // ---- static styled rendering (non-cursor lines) ----
            Text {
                id: rowText
                visible: !row.isCursorLine
                x: row.textLeft
                width: row.width - row.textLeft
                anchors.verticalCenter: row.verticalCenter
                wrapMode: Text.Wrap
                textFormat: Text.RichText
                font.family: root.fnt.family
                font.pixelSize: root.fnt.size
                color: root.colText
                text: row.buildHtml(row.lineData)

                // Modifier-aware link interaction:
                //   Ctrl+Click          -> open the full URL in the browser
                //   Ctrl+Shift+Click   -> toggle expand/shorten for that URL
                //   plain click         -> place the caret (same as clicking text)
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton
                    cursorShape: rowText.hoveredLink !== "" ? Qt.PointingHandCursor : Qt.IBeamCursor
                    onClicked: function (mouse) {
                        var href = rowText.linkAt(mouse.x, mouse.y)
                        if (href === "") {
                            root.moveToLine(row.index, root.lines[row.index].length)
                            return
                        }
                        if ((mouse.modifiers & Qt.ControlModifier) && (mouse.modifiers & Qt.ShiftModifier)) {
                            backend.toggle_link_expand(href)
                        } else if (mouse.modifiers & Qt.ControlModifier) {
                            backend.open_url(href)
                        } else {
                            root.moveToLine(row.index, root.lines[row.index].length)
                        }
                    }
                }
            }

            // Build rich-text HTML from the per-character spans. Link spans use
            // the full URL (s.url) as the href and the (possibly shortened)
            // s.text as the visible label.
            function buildHtml(d) {
                if (!d || !d.spans || d.spans.length === 0)
                    return "&nbsp;"
                var html = ""
                for (var i = 0; i < d.spans.length; i++) {
                    var s = d.spans[i]
                    if (s.hidden)
                        continue
                    var t = root.escapeHtml(s.text)
                    var style = "color:" + s.color + ";"
                    if (s.italic) style += "font-style:italic;"
                    if (s.strike) style += "text-decoration:line-through;"
                    if (s.link) {
                        var href = s.url ? s.url : s.text
                        html += "<a href=\"" + root.escapeHtml(href) + "\" style=\"" + style
                              + "text-decoration:underline;\">" + t + "</a>"
                    } else {
                        html += "<span style=\"" + style + "\">" + t + "</span>"
                    }
                }
                return html === "" ? "&nbsp;" : html
            }

            // ---- editable raw line (cursor line) ----
            Loader {
                id: editorLoader
                active: row.isCursorLine
                x: row.textLeft
                width: row.width - row.textLeft
                height: row.height
                sourceComponent: lineEditor
            }

            Component {
                id: lineEditor
                TextEdit {
                    id: input
                    text: root.lines[row.index] !== undefined ? root.lines[row.index] : ""
                    textFormat: TextEdit.PlainText
                    color: root.colText
                    selectionColor: backend ? backend.colors.selection : "#34363b"
                    selectByMouse: true
                    font.family: root.fnt.family
                    font.pixelSize: root.fnt.size
                    verticalAlignment: TextEdit.AlignVCenter
                    wrapMode: TextEdit.Wrap
                    clip: true

                    function takeFocus(col) {
                        forceActiveFocus()
                        cursorPosition = Math.min(col, text.length)
                    }

                    Component.onCompleted: {
                        if (row.isCursorLine)
                            Qt.callLater(takeFocus, root.cursorCol)
                    }

                    onTextChanged: {
                        if (text !== root.lines[row.index])
                            root.commitLine(row.index, text, cursorPosition)
                    }
                    onCursorPositionChanged: root.cursorCol = cursorPosition

                    Keys.onReturnPressed: function (e) {
                        root.splitLine(row.index, cursorPosition)
                        e.accepted = true
                    }
                    Keys.onEnterPressed: function (e) {
                        root.splitLine(row.index, cursorPosition)
                        e.accepted = true
                    }
                    Keys.onPressed: function (e) {
                        if ((e.modifiers & Qt.ControlModifier) && e.key === Qt.Key_V) {
                            var t = backend.paste_or_ocr()
                            if (t !== "")
                                root.pasteText(t)
                            e.accepted = true
                        } else if (e.key === Qt.Key_Backspace && cursorPosition === 0 && selectionStart === selectionEnd) {
                            root.joinWithPrev(row.index)
                            e.accepted = true
                        } else if (e.key === Qt.Key_Up) {
                            root.moveToLine(row.index - 1, cursorPosition)
                            e.accepted = true
                        } else if (e.key === Qt.Key_Down) {
                            root.moveToLine(row.index + 1, cursorPosition)
                            e.accepted = true
                        }
                    }
                }
            }

            // Click a static line to place the caret there.
            MouseArea {
                anchors.fill: parent
                anchors.leftMargin: row.textLeft
                enabled: !row.isCursorLine
                onClicked: root.moveToLine(row.index, root.lines[row.index].length)
            }

            // Subtle line-appear animation.
            opacity: 0
            Component.onCompleted: appear.start()
            NumberAnimation { id: appear; target: row; property: "opacity"; to: 1; duration: 140 }
        }
    }

    // Transient OCR status label: fades in when text is set, fades out after 3s.
    Text {
        id: ocrStatusLabel
        text: root.ocrStatusText
        color: root.ocrStatusError ? "#d97757" : root.colMuted
        font.family: root.fnt.family
        font.pixelSize: root.fnt.size - 2
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 8
        opacity: root.ocrStatusText === "" ? 0 : 1
        Behavior on opacity { NumberAnimation { duration: 160 } }
        Timer {
            id: statusFade
            interval: 3000
            onTriggered: root.ocrStatusText = ""
        }
    }

    // Minimal HTML escaping for static span text.
    function escapeHtml(s) {
        return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    }
}
