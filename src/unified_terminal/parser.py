from unified_terminal.screen import ScreenBuffer


class TerminalParser:
    DEFAULT_FOREGROUND = "#f1f3f5"
    DEFAULT_BACKGROUND = "#111318"

    COLORS = {
        30: "#000000",
        31: "#cd3131",
        32: "#0dbc79",
        33: "#e5e510",
        34: "#2472c8",
        35: "#bc3fbc",
        36: "#11a8cd",
        37: "#e5e5e5",
        90: "#666666",
        91: "#f14c4c",
        92: "#23d18b",
        93: "#f5f543",
        94: "#3b8eea",
        95: "#d670d6",
        96: "#29b8db",
        97: "#ffffff",
    }

    def __init__(self, screen):
        self.screen = screen
        self.foreground = self.DEFAULT_FOREGROUND
        self.background = self.DEFAULT_BACKGROUND
        self.bold = False
        self.pending = ""
        self.cursor_visible = True
        self.saved_cursor = (0, 0)

    def feed(self, text):
        text = self.pending + text
        self.pending = ""
        i = 0

        while i < len(text):
            character = text[i]

            if character == "\x1b":
                if i + 1 >= len(text):
                    self.pending = text[i:]
                    break

                if text[i + 1] == "[":
                    end = i + 2

                    while end < len(text) and not (
                        "@" <= text[end] <= "~"
                    ):
                        end += 1

                    if end >= len(text):
                        self.pending = text[i:]
                        break

                    parameters = text[i + 2:end]
                    self._handle_csi(parameters, text[end])
                    i = end + 1
                    continue

                if text[i + 1] == "]":
                    end = i + 2

                    while end < len(text):
                        if text[end] == "\x07":
                            break

                        if text.startswith("\x1b\\", end):
                            break

                        end += 1

                    if end >= len(text):
                        self.pending = text[i:]
                        break

                    if text.startswith("\x1b\\", end):
                        i = end + 2
                    else:
                        i = end + 1

                    continue

                i += 2
                continue

            if character == "\r":
                self.screen.cursor_x = 0
            elif character == "\n":
                self._next_line()
            elif character == "\b":
                self.screen.cursor_x = max(
                    0, self.screen.cursor_x - 1
                )
            elif character == "\t":
                spaces = 8 - (self.screen.cursor_x % 8)

                for _ in range(spaces):
                    self._put_character(" ")
            elif character >= " " and character != "\x7f":
                self._put_character(character)

            i += 1

    def _handle_csi(self, parameters, command):
        private = parameters.startswith("?")
        values = parameters.lstrip("?").lstrip(">").lstrip("!")

        if command in ("h", "l") and private:
            for value in values.split(";"):
                if value == "25":
                    self.cursor_visible = command == "h"
            return

        if command == "m":
            self._apply_sgr(values)
            return

        if command == "J":
            self._erase_display(values)
            return

        if command == "K":
            self._erase_line(values)
            return

        parts = values.split(";") if values else []
        numbers = [
            int(value) if value.isdigit() else 0
            for value in parts
        ]

        first = numbers[0] if numbers else 0
        second = numbers[1] if len(numbers) > 1 else 0

        if command in ("H", "f"):
            row = first or 1
            column = second or 1
            self.screen.move_cursor(column - 1, row - 1)
        elif command == "A":
            self._move_cursor(self.screen.cursor_x, self.screen.cursor_y - (first or 1))
        elif command == "B":
            self._move_cursor(self.screen.cursor_x, self.screen.cursor_y + (first or 1))
        elif command == "C":
            self._move_cursor(self.screen.cursor_x + (first or 1), self.screen.cursor_y)
        elif command == "D":
            self._move_cursor(self.screen.cursor_x - (first or 1), self.screen.cursor_y)
        elif command == "E":
            self._move_cursor(0, self.screen.cursor_y + (first or 1))
        elif command == "F":
            self._move_cursor(0, self.screen.cursor_y - (first or 1))
        elif command == "G":
            self._move_cursor((first or 1) - 1, self.screen.cursor_y)
        elif command == "d":
            self._move_cursor(self.screen.cursor_x, (first or 1) - 1)
        elif command == "s":
            self.saved_cursor = (
                self.screen.cursor_x,
                self.screen.cursor_y,
            )
        elif command == "u":
            self._move_cursor(*self.saved_cursor)

    def _move_cursor(self, x, y):
        self.screen.move_cursor(x, y)

    def _put_character(self, character):
        self.screen.put_character(
            character,
            foreground=self.foreground,
            background=self.background,
            bold=self.bold,
        )

    def _next_line(self):
        self.screen.cursor_y += 1

        if self.screen.cursor_y >= self.screen.rows:
            self.screen.scroll_up()
            self.screen.cursor_y = self.screen.rows - 1

    def _erase_display(self, parameters):
        mode = int(parameters or "0")

        if mode in (2, 3):
            self.screen.cells = self.screen._create_cells()
        elif mode == 0:
            for y in range(self.screen.cursor_y, self.screen.rows):
                start = self.screen.cursor_x if y == self.screen.cursor_y else 0

                for x in range(start, self.screen.columns):
                    self.screen.cells[y][x] = self.screen.cells[y][x].__class__()
        elif mode == 1:
            for y in range(self.screen.cursor_y + 1):
                end = self.screen.cursor_x + 1 if y == self.screen.cursor_y else self.screen.columns

                for x in range(end):
                    self.screen.cells[y][x] = self.screen.cells[y][x].__class__()

    def _erase_line(self, parameters):
        mode = int(parameters or "0")
        y = self.screen.cursor_y

        if mode == 0:
            start, end = self.screen.cursor_x, self.screen.columns
        elif mode == 1:
            start, end = 0, self.screen.cursor_x + 1
        elif mode == 2:
            start, end = 0, self.screen.columns
        else:
            return

        for x in range(start, end):
            self.screen.cells[y][x] = self.screen.cells[y][x].__class__()

    def _apply_sgr(self, parameters):
        codes = [
            int(value) if value else 0
            for value in parameters.split(";")
        ] if parameters else [0]

        for code in codes:
            if code == 0:
                self.foreground = self.DEFAULT_FOREGROUND
                self.background = self.DEFAULT_BACKGROUND
                self.bold = False
            elif code == 1:
                self.bold = True
            elif code == 22:
                self.bold = False
            elif code == 39:
                self.foreground = self.DEFAULT_FOREGROUND
            elif code == 49:
                self.background = self.DEFAULT_BACKGROUND
            elif code in self.COLORS:
                self.foreground = self.COLORS[code]
            elif 40 <= code <= 47:
                self.background = self.COLORS[code - 10]
            elif 100 <= code <= 107:
                self.background = self.COLORS[code - 10]