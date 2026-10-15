from abc import ABC, abstractmethod
from collections.abc import Callable


class TerminalBackend(ABC):
    def __init__(self):
        self.on_output: Callable[[str], None] | None = None

    @abstractmethod
    def start(
        self,
        command: list[str],
        columns: int,
        rows: int,
        on_output: Callable[[str], None],
        on_exit: Callable[[], None],
    ) -> None:
        pass

    @abstractmethod
    def write(self, data: str) -> None:
        pass

    @abstractmethod
    def resize(self, columns: int, rows: int) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass