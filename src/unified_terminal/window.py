from PySide6.QtWidgets import QMainWindow

from unified_terminal.terminal import TerminalWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Unified Terminal")
        self.resize(1100, 700)

        self.terminal = TerminalWidget()
        self.setCentralWidget(self.terminal)