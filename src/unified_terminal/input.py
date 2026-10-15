from PySide6.QtCore import Qt


class TerminalInput:
    KEY_SEQUENCES = {
        Qt.Key.Key_Up: "\x1b[A",
        Qt.Key.Key_Down: "\x1b[B",
        Qt.Key.Key_Right: "\x1b[C",
        Qt.Key.Key_Left: "\x1b[D",
        Qt.Key.Key_Home: "\x1b[H",
        Qt.Key.Key_End: "\x1b[F",
        Qt.Key.Key_Insert: "\x1b[2~",
        Qt.Key.Key_Delete: "\x1b[3~",
        Qt.Key.Key_PageUp: "\x1b[5~",
        Qt.Key.Key_PageDown: "\x1b[6~",
        Qt.Key.Key_F1: "\x1bOP",
        Qt.Key.Key_F2: "\x1bOQ",
        Qt.Key.Key_F3: "\x1bOR",
        Qt.Key.Key_F4: "\x1bOS",
        Qt.Key.Key_F5: "\x1b[15~",
        Qt.Key.Key_F6: "\x1b[17~",
        Qt.Key.Key_F7: "\x1b[18~",
        Qt.Key.Key_F8: "\x1b[19~",
        Qt.Key.Key_F9: "\x1b[20~",
        Qt.Key.Key_F10: "\x1b[21~",
        Qt.Key.Key_F11: "\x1b[23~",
        Qt.Key.Key_F12: "\x1b[24~",
        Qt.Key.Key_Backspace: "\x7f",
        Qt.Key.Key_Return: "\r",
        Qt.Key.Key_Enter: "\r",
        Qt.Key.Key_Tab: "\t",
        Qt.Key.Key_Escape: "\x1b",
    }

    def encode_key(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                return chr(key - Qt.Key.Key_A + 1)

            if key == Qt.Key.Key_Space:
                return "\x00"

            if key == Qt.Key.Key_BracketLeft:
                return "\x1b"

            if key == Qt.Key.Key_Backslash:
                return "\x1c"

            if key == Qt.Key.Key_BracketRight:
                return "\x1d"

            if key == Qt.Key.Key_6:
                return "\x1e"

            if key == Qt.Key.Key_Minus:
                return "\x1f"

            return None

        if key in self.KEY_SEQUENCES:
            return self.KEY_SEQUENCES[key]

        if modifiers & (
            Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        ):
            return None

        text = event.text()

        if text and text.isprintable():
            return text

        return None