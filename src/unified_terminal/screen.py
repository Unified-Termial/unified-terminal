from dataclasses import dataclass


@dataclass
class Cell:
    character: str = " "
    foreground: str = "#f1f3f5"
    background: str = "#111318"
    bold: bool = False


class ScreenBuffer:
    def __init__(self, columns=100, rows=30):
        self.columns = columns
        self.rows = rows
        self.cursor_x = 0
        self.cursor_y = 0
        self.cells = self._create_cells()

    def _create_cells(self):
        return [
            [Cell() for _ in range(self.columns)]
            for _ in range(self.rows)
        ]

    def put_character(
        self,
        character,
        foreground=None,
        background=None,
        bold=False
    ):
        if not character:
            return

        if self.cursor_x >= self.columns:
            self.cursor_x = 0
            self.cursor_y += 1

        if self.cursor_y >= self.rows:
            self.scroll_up()
            self.cursor_y = self.rows - 1

        self.cells[self.cursor_y][self.cursor_x] = Cell(
            character=character,
            foreground=foreground or "#f1f3f5",
            background=background or "#111318",
            bold=bold
        )
        self.cursor_x += 1

    def move_cursor(self, x, y):
        self.cursor_x = max(0, min(x, self.columns - 1))
        self.cursor_y = max(0, min(y, self.rows - 1))

    def clear(self):
        self.cells = self._create_cells()
        self.cursor_x = 0
        self.cursor_y = 0

    def resize(self, columns, rows):
        columns = max(1, columns)
        rows = max(1, rows)

        new_cells = [
            [Cell() for _ in range(columns)]
            for _ in range(rows)
        ]

        for y in range(min(self.rows, rows)):
            for x in range(min(self.columns, columns)):
                new_cells[y][x] = self.cells[y][x]

        self.columns = columns
        self.rows = rows
        self.cells = new_cells

        self.cursor_x = min(self.cursor_x, columns - 1)
        self.cursor_y = min(self.cursor_y, rows - 1)

    def scroll_up(self):
        self.cells.pop(0)
        self.cells.append([
            Cell() for _ in range(self.columns)
        ])