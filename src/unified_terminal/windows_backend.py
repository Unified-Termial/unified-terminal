import threading
from collections.abc import Callable

from winpty import PtyProcess

from unified_terminal.backend import TerminalBackend


class WindowsBackend(TerminalBackend):
    def __init__(self):
        super().__init__()
        self.process = None
        self.reader_thread = None
        self.running = False
        self.on_output = None
        self.on_exit: Callable[[], None] | None = None
        self._lock = threading.Lock()

    def start(
        self,
        command: list[str],
        columns: int,
        rows: int,
        on_output: Callable[[str], None],
        on_exit: Callable[[], None],
    ) -> None:
        if self.running:
            raise RuntimeError("A terminal session is already running.")

        process = PtyProcess.spawn(
            command,
            dimensions=(rows, columns),
        )

        with self._lock:
            self.process = process
            self.on_output = on_output
            self.on_exit = on_exit
            self.running = True

        self.reader_thread = threading.Thread(
            target=self._read_output,
            daemon=True,
        )
        self.reader_thread.start()

    def _read_output(self):
        try:
            while self.running:
                process = self.process

                if process is None:
                    break

                data = process.read(16384)

                if not data:
                    break

                callback = self.on_output

                if callback is not None:
                    callback(data)

        except (EOFError, OSError):
            pass
        finally:
            self.running = False
            on_exit = self.on_exit
            self.on_exit = None
            if on_exit is not None:
                on_exit()

    def write(self, data: str) -> None:
        with self._lock:
            process = self.process

            if not self.running or process is None:
                return

            try:
                process.write(data)
            except (EOFError, OSError):
                self.running = False

    def resize(self, columns: int, rows: int) -> None:
        with self._lock:
            process = self.process

            if not self.running or process is None:
                return

            try:
                process.setwinsize(rows, columns)
            except (EOFError, OSError):
                self.running = False

    def close(self) -> None:
        with self._lock:
            self.running = False
            process = self.process
            self.process = None

        if process is not None:
            try:
                process.close(force=True)
            except (EOFError, OSError):
                pass
