import faulthandler
faulthandler.enable()

import os
import platform
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from unified_terminal.terminal import TerminalWidget


def probe(label):
    from abc import ABC, abstractmethod

    class _P(ABC):
        @abstractmethod
        def f(self):
            pass

    class _Q(_P):
        def f(self):
            pass

    print(f"   probe ok na: {label}", flush=True)


def _icon_path() -> Path:
    base_path = Path(__file__).resolve().parent
    source_path = base_path.parents[1]

    paths = (
        base_path / "assets" / "UT.png",
        base_path / "assets" / "UT.ico",
        source_path / "assets" / "UT.png",
        source_path / "assets" / "UT.ico",
        Path(sys.prefix) / "share" / "unified-terminal" / "UT.png",
        Path(sys.prefix) / "share" / "unified-terminal" / "UT.ico",
    )

    for path in paths:
        if path.is_file():
            return path

    raise FileNotFoundError(
        "Unable to locate the Unified Terminal window icon."
    )


def _create_backend():
    system = platform.system()

    if system == "Windows":
        from unified_terminal.windows_backend import WindowsBackend

        return WindowsBackend(), ["powershell.exe", "-NoLogo"]

    if system == "Linux":
        from unified_terminal.linux_backend import LinuxBackend

        shell = os.environ.get("SHELL", "/bin/bash")
        return LinuxBackend(), [shell, "-i"]

    raise RuntimeError(f"Unsupported operating system: {system}")


def main():
    probe("start")

    print("1: creating QApplication", flush=True)
    app = QApplication(sys.argv)
    app.setApplicationName("Unified Terminal")
    probe("QApplication")

    if platform.system() == "Windows":
        print("2: icon", flush=True)
        app.setWindowIcon(QIcon(str(_icon_path())))
        probe("icon")

    print("3: widget", flush=True)
    terminal = TerminalWidget()
    probe("TerminalWidget")
    terminal.resize(1100, 700)
    probe("resize")

    print("4: backend", flush=True)
    backend, command = _create_backend()
    terminal.start_backend(backend, command)

    app.aboutToQuit.connect(backend.close)
    print("5: show", flush=True)
    terminal.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()