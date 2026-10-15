import codecs
import fcntl
import os
import pty
import signal
import struct
import termios
import threading
from collections.abc import Callable

from unified_terminal.backend import TerminalBackend


class LinuxBackend(TerminalBackend):
    def __init__(self):
        super().__init__()
        self.process_id: int | None = None
        self.master_fd: int | None = None
        self.reader_thread: threading.Thread | None = None
        self.running = False
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
        if not command:
            raise ValueError("The terminal command cannot be empty.")

        process_id, master_fd = pty.fork()

        if process_id == 0:
            try:
                os.execvp(command[0], command)
            except OSError as error:
                os.write(2, f"Unable to start {command[0]}: {error}\n".encode())
                os._exit(127)

        try:
            self._set_window_size(master_fd, columns, rows)
        except OSError:
            try:
                os.killpg(process_id, signal.SIGHUP)
            except ProcessLookupError:
                pass
            os.close(master_fd)
            try:
                os.waitpid(process_id, 0)
            except ChildProcessError:
                pass
            raise

        with self._lock:
            self.process_id = process_id
            self.master_fd = master_fd
            self.on_output = on_output
            self.on_exit = on_exit
            self.running = True

        self.reader_thread = threading.Thread(
            target=self._read_output,
            args=(master_fd, process_id),
            daemon=True,
        )
        self.reader_thread.start()

    def _read_output(self, master_fd: int, process_id: int) -> None:
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

        try:
            while self.running:
                try:
                    data = os.read(master_fd, 16384)
                except OSError:
                    break

                if not data:
                    break

                text = decoder.decode(data)
                if text and self.on_output is not None:
                    self.on_output(text)
        finally:
            remaining = decoder.decode(b"", final=True)
            if remaining and self.on_output is not None:
                self.on_output(remaining)
            with self._lock:
                if self.master_fd == master_fd:
                    self.master_fd = None
                    self.running = False
                if self.process_id == process_id:
                    self.process_id = None
                on_exit = self.on_exit
                self.on_exit = None
            if on_exit is not None:
                on_exit()
            try:
                os.close(master_fd)
            except OSError:
                pass
            try:
                os.waitpid(process_id, 0)
            except ChildProcessError:
                pass

    def write(self, data: str) -> None:
        with self._lock:
            master_fd = self.master_fd
            if not self.running or master_fd is None:
                return
            try:
                os.write(master_fd, data.encode("utf-8"))
            except OSError:
                self.running = False

    def resize(self, columns: int, rows: int) -> None:
        with self._lock:
            if self.running and self.master_fd is not None:
                self._set_window_size(self.master_fd, columns, rows)

    @staticmethod
    def _set_window_size(master_fd: int, columns: int, rows: int) -> None:
        dimensions = struct.pack("HHHH", rows, columns, 0, 0)
        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, dimensions)

    def close(self) -> None:
        with self._lock:
            self.running = False
            process_id = self.process_id

        if process_id is not None:
            try:
                os.killpg(process_id, signal.SIGHUP)
            except ProcessLookupError:
                pass
