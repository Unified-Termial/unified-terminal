
import pyte

from PySide6.QtCore import QRect, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from unified_terminal.backend import TerminalBackend
from unified_terminal.input import TerminalInput


class TerminalWidget(QWidget):
    PADDING = 12
    SCROLLBACK_LINES = 1000
    SCROLLBACK_RATIO = 0.1
    ANSI_COLORS = {
        "black": "#000000",
        "red": "#aa0000",
        "green": "#00aa00",
        "brown": "#aa5500",
        "blue": "#0000aa",
        "magenta": "#aa00aa",
        "cyan": "#00aaaa",
        "white": "#aaaaaa",
        "brightblack": "#555555",
        "brightred": "#ff5555",
        "brightgreen": "#55ff55",
        "brightbrown": "#ffff55",
        "brightblue": "#5555ff",
        "brightmagenta": "#ff55ff",
        "brightcyan": "#55ffff",
        "brightwhite": "#ffffff",
    }

    output_received = Signal(str)
    backend_exited = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        available_families = {
            family.casefold(): family for family in QFontDatabase.families()
        }
        font_family = next(
            (
                available_families[name.casefold()]
                for name in (
                    "Cascadia Mono",
                    "Consolas",
                    "Cascadia Code",
                    "JetBrains Mono",
                )
                if name.casefold() in available_families
            ),
            QFontDatabase.systemFont(
                QFontDatabase.SystemFont.FixedFont
            ).family(),
        )
        font = QFont(font_family)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(11)
        self.setFont(font)
        metrics = self.fontMetrics()
        self.cell_width = max(1, metrics.horizontalAdvance("M"))
        self.line_height = max(1, metrics.height())
        self.baseline = metrics.ascent()
        self._font_cache: dict[tuple[bool, bool, bool, bool], QFont] = {}
        self._color_cache: dict[str, QColor] = {}
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

        self.background = QColor("#111318")
        self.foreground = QColor("#f1f3f5")

        self.vt_screen = pyte.HistoryScreen(
            lines=30,
            columns=100,
            history=self.SCROLLBACK_LINES,
            ratio=self.SCROLLBACK_RATIO,
        )
        self.vt_stream = pyte.Stream(self.vt_screen)
        self._wheel_delta = 0.0

        self.terminal_input = TerminalInput()
        self.backend: TerminalBackend | None = None
        self.selection: tuple[tuple[int, int], tuple[int, int]] | None = None
        self.selection_anchor: tuple[int, int] | None = None

        self.output_received.connect(self._handle_output)
        self.backend_exited.connect(self.close)

        self.cursor_visible = True
        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self._blink_cursor)
        self.cursor_timer.start(530)

    def write_text(self, text):
        self.vt_stream.feed(text)
        self.update()

    def start_backend(self, backend, command):
        self.backend = backend
        columns, rows = self._terminal_dimensions()
        self.vt_screen.resize(lines=rows, columns=columns)

        self.backend.start(
            command,
            self.vt_screen.columns,
            self.vt_screen.lines,
            self.output_received.emit,
            self.backend_exited.emit,
        )

        self.setFocus()

    def _handle_output(self, data):
        self.vt_stream.feed(data)
        self.update()

    def keyPressEvent(self, event):
        if self.backend is None:
            super().keyPressEvent(event)
            return

        modifiers = event.modifiers()
        key = event.key()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_C and (
                modifiers & Qt.KeyboardModifier.ShiftModifier
                or self.selection is not None
            ):
                self.copy_selection()
                event.accept()
                return
            if key == Qt.Key.Key_Insert:
                self.copy_selection()
                event.accept()
                return

        control_shift = (
            modifiers & Qt.KeyboardModifier.ControlModifier
            and modifiers & Qt.KeyboardModifier.ShiftModifier
        )
        shift_insert = (
            modifiers & Qt.KeyboardModifier.ShiftModifier
            and key == Qt.Key.Key_Insert
        )
        if (control_shift and key == Qt.Key.Key_V) or shift_insert:
            self.paste_clipboard()
            event.accept()
            return

        data = self.terminal_input.encode_key(event)

        if data is not None:
            self.backend.write(data)
            event.accept()
            return

        super().keyPressEvent(event)

    def _cell_at(self, position):
        cell_width, line_height = self._cell_metrics()
        x = (position.x() - self.PADDING) // cell_width
        y = (position.y() - self.PADDING) // line_height
        x = max(0, min(x, self.vt_screen.columns - 1))
        y = max(0, min(y, self.vt_screen.lines - 1))
        return x, y

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selection_anchor = self._cell_at(event.position().toPoint())
            self.selection = None
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.selection_anchor is not None and (
            event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.selection = (
                self.selection_anchor,
                self._cell_at(event.position().toPoint()),
            )
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selection_anchor = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if not delta:
            pixel_delta = event.pixelDelta().y()
            if not pixel_delta:
                super().wheelEvent(event)
                return
            delta = pixel_delta * 120 / (self.line_height * 3)

        self._wheel_delta += delta
        steps = int(self._wheel_delta / 120)
        self._wheel_delta -= steps * 120

        if steps:
            scroll_page = (
                self.vt_screen.prev_page
                if steps > 0
                else self.vt_screen.next_page
            )
            for _ in range(abs(steps)):
                scroll_page()
            self.update()

        event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        copy_action.setEnabled(self.selection is not None)
        paste_action = menu.addAction("Paste")
        action = menu.exec(event.globalPos())
        if action == copy_action:
            self.copy_selection()
        elif action == paste_action:
            self.paste_clipboard()

    def _selected_text(self):
        if self.selection is None:
            return ""

        start, end = self.selection
        if (start[1], start[0]) > (end[1], end[0]):
            start, end = end, start

        lines = []
        for y in range(start[1], end[1] + 1):
            first_column = start[0] if y == start[1] else 0
            last_column = end[0] if y == end[1] else self.vt_screen.columns - 1
            line = "".join(
                self.vt_screen.buffer[y][x].data
                for x in range(first_column, last_column + 1)
            )
            if y != end[1]:
                line = line.rstrip()
            lines.append(line)
        return "\n".join(lines)

    def copy_selection(self):
        text = self._selected_text()
        if text:
            QApplication.clipboard().setText(text)

    def paste_clipboard(self):
        if self.backend is None:
            return
        text = QApplication.clipboard().text()
        if text:
            normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
            self.backend.write(normalized_text.replace("\n", "\r"))

    def _is_cell_selected(self, x, y):
        if self.selection is None:
            return False
        start, end = self.selection
        if (start[1], start[0]) > (end[1], end[0]):
            start, end = end, start
        return (
            start[1] <= y <= end[1]
            and (y != start[1] or x >= start[0])
            and (y != end[1] or x <= end[0])
        )

    def _cell_metrics(self):
        return self.cell_width, self.line_height

    def _terminal_dimensions(self):
        cell_width, line_height = self._cell_metrics()
        columns = max(1, (self.width() - 2 * self.PADDING) // cell_width)
        rows = max(1, (self.height() - 2 * self.PADDING) // line_height)
        return columns, rows

    def resizeEvent(self, event):
        columns, rows = self._terminal_dimensions()
        self.vt_screen.resize(lines=rows, columns=columns)

        if self.backend is not None:
            self.backend.resize(columns, rows)

        super().resizeEvent(event)
        self.update()

    def _get_color(self, color, default):
        if not color or color == "default":
            color = default

        cached = self._color_cache.get(color)
        if cached is None:
            result = QColor(self.ANSI_COLORS.get(color, color))
            if not result.isValid():
                result = QColor(default)
            self._color_cache[color] = result
            cached = result
        return cached

    def _get_cell_font(self, cell):
        style = (
            cell.bold,
            cell.italics,
            cell.underscore,
            cell.strikethrough,
        )
        return self._get_cell_font_from_style(style)

    def _get_cell_font_from_style(self, style):
        font = self._font_cache.get(style)
        if font is None:
            font = QFont(self.font())
            font.setBold(style[0])
            font.setItalic(style[1])
            font.setUnderline(style[2])
            font.setStrikeOut(style[3])
            self._font_cache[style] = font
        return font

    def _cell_render_key(self, cell, x, y, selection):
        selected = selection is not None and (
            selection[0][1] <= y <= selection[1][1]
            and (y != selection[0][1] or x >= selection[0][0])
            and (y != selection[1][1] or x <= selection[1][0])
        )
        reverse = cell.reverse
        foreground = cell.bg if reverse else cell.fg
        background = cell.fg if reverse else cell.bg
        if selected:
            foreground, background = "#ffffff", "#264f78"
        style = (
            cell.bold,
            cell.italics,
            cell.underscore,
            cell.strikethrough,
        )
        fill_background = selected or reverse or cell.bg != "default"
        return foreground, background, style, fill_background

    def _blink_cursor(self):
        self.cursor_visible = not self.cursor_visible
        cursor = self.vt_screen.cursor
        if not cursor.hidden:
            self.update(
                QRect(
                    self.PADDING + cursor.x * self.cell_width,
                    self.PADDING + cursor.y * self.line_height,
                    self.cell_width,
                    self.line_height,
                )
            )

    def paintEvent(self, event):
        painter = QPainter(self)

        try:
            painter.fillRect(self.rect(), self.background)
            cell_width = self.cell_width
            line_height = self.line_height
            baseline = self.baseline
            selection = self.selection
            if selection is not None and (
                (selection[0][1], selection[0][0])
                > (selection[1][1], selection[1][0])
            ):
                selection = selection[1], selection[0]

            paint_rect = event.rect()
            first_row = max(
                0, (paint_rect.top() - self.PADDING) // line_height
            )
            last_row = min(
                self.vt_screen.lines - 1,
                (paint_rect.bottom() - self.PADDING) // line_height,
            )
            first_column = max(
                0, (paint_rect.left() - self.PADDING) // cell_width
            )
            last_column = min(
                self.vt_screen.columns - 1,
                (paint_rect.right() - self.PADDING) // cell_width,
            )

            for y in range(first_row, last_row + 1):
                row = self.vt_screen.buffer[y]
                py = self.PADDING + y * line_height
                x = first_column

                while x <= last_column:
                    cell = row[x]
                    run_key = self._cell_render_key(cell, x, y, selection)
                    run_start = x
                    run_data = [cell.data]
                    x += 1

                    while x <= last_column:
                        next_cell = row[x]
                        if (
                            self._cell_render_key(
                                next_cell, x, y, selection
                            )
                            != run_key
                        ):
                            break
                        run_data.append(next_cell.data)
                        x += 1

                    foreground = self._get_color(
                        run_key[0], self.foreground.name()
                    )
                    background = self._get_color(
                        run_key[1], self.background.name()
                    )
                    run_width = (x - run_start) * cell_width
                    px = self.PADDING + run_start * cell_width
                    if run_key[3]:
                        painter.fillRect(
                            px, py, run_width, line_height, background
                        )

                    text = "".join(run_data)
                    if text.strip():
                        painter.setFont(
                            self._get_cell_font_from_style(run_key[2])
                        )
                        painter.setPen(foreground)
                        painter.drawText(px, py + baseline, text)

            cursor = self.vt_screen.cursor

            if not cursor.hidden and self.cursor_visible:
                x = min(cursor.x, self.vt_screen.columns - 1)
                y = min(cursor.y, self.vt_screen.lines - 1)

                px = self.PADDING + x * cell_width
                py = self.PADDING + y * line_height

                cell = self.vt_screen.buffer[y][x]

                cursor_fg = self._get_color(
                    cell.fg, self.foreground.name()
                )
                cursor_bg = self._get_color(
                    cell.bg, self.background.name()
                )

                if cell.reverse:
                    cursor_fg, cursor_bg = cursor_bg, cursor_fg

                # Classic block cursor.
                painter.fillRect(
                    px, py, cell_width, line_height, cursor_fg
                )

                # Redraw the character using inverted colours.
                if cell.data:
                    painter.setFont(self._get_cell_font(cell))
                    painter.setPen(cursor_bg)
                    painter.drawText(
                        px,
                        py + baseline,
                        cell.data,
                    )

        finally:
            if painter.isActive():
                painter.end()

    def sizeHint(self):
        return 800, 500
