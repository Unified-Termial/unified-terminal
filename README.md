<!-- <div align="center">
  <img src="https://raw.githubusercontent.com/Unified-Termial/unified-terminal-assets/refs/heads/master/img/v0.1.0.jpg" alt="Unified Terminal logo" width="">
  <h1>Unified Terminal</h1>
  <p>A lightweight desktop terminal emulator for Windows and Linux.</p>
</div> -->

# Unified Terminal

A lightweight desktop terminal emulator for Windows and Linux

Unified Terminal is a Python and Qt terminal application. It uses
[pyte](https://github.com/selectel/pyte) to render terminal output and launches
the platform's shell through a pseudo-terminal backend.

## Downloads

Check the [GitHub Releases](https://github.com/Unified-Termial/unified-terminal/releases)
page for prebuilt binaries. If no release or downloadable assets are listed,
install from source using the instructions below.

### Windows
Run the installer or the portable zip

### Linux
extract the tarball and install with the `install.sh` file, `remove.sh` is the file to remove Unified Terminal on Linux

## Features

- **Windows and Linux support** — starts PowerShell on Windows and the
  interactive shell configured in `$SHELL` on Linux (or `/bin/bash` if unset).
- **Terminal output rendering** — pyte-backed handling of ANSI colors, cursor
  movement, and screen updates.
- **Resizable terminal** — adjusts the terminal grid and shell dimensions when
  the window is resized.
- **Scrollback** — use the mouse wheel to review up to 1,000 lines of terminal
  history on Windows and Linux.
- **Copy and paste** — select text by dragging; use the keyboard shortcuts or
  right-click menu.
- **Keyboard input** — supports common control sequences, navigation keys,
  and function keys.
- **Monospace display** — prefers an installed terminal font and falls back to
  the system fixed-width font.
- **Shell lifecycle** — the application window closes when the shell exits.

Unified Terminal is under active development and does not yet implement every
feature supported by mature terminal emulators.

## Requirements

- Python **3.13 or newer** for running from source
- Windows or Linux
- On Windows: PowerShell; `pywinpty` is installed automatically
- On Linux: an interactive shell available at `$SHELL` or `/bin/bash`
- On Debian/Ubuntu systems using Qt's XCB platform plugin: `libxcb-cursor0`

Install the XCB runtime dependency on Debian or Ubuntu if needed:

```shell
sudo apt install libxcb-cursor0
```

## Install from source

Clone the repository and install the application:

```shell
git clone https://github.com/Unified-Termial/unified-terminal.git
cd unified-terminal
python -m pip install .
```

Start it with the installed command:

```shell
unified-terminal
```

For development, use an editable install:

```shell
python -m pip install -e .
```

You can also launch the package directly:

```shell
python -m unified_terminal
```

## Keyboard shortcuts

| Action | Shortcut |
| --- | --- |
| Copy selected text | `Ctrl+Shift+C` or `Ctrl+Insert` |
| Paste from clipboard | `Ctrl+Shift+V` or `Shift+Insert` |
| Interrupt a running command | `Ctrl+C` when no text is selected |

You can also copy or paste from the terminal's right-click menu.

## Dependencies

The runtime dependencies are declared in [`pyproject.toml`](pyproject.toml):

| Package | Required on | Purpose |
| --- | --- | --- |
| [PySide6](https://pypi.org/project/PySide6/) `>=6.8` | Windows and Linux | Qt desktop UI |
| [pyte](https://pypi.org/project/pyte/) `>=0.8.2` | Windows and Linux | Terminal screen and escape-sequence handling |
| [pywinpty](https://pypi.org/project/pywinpty/) `>=2.0` | Windows only | Windows pseudo-terminal backend |

The Linux backend uses Python's standard-library PTY and terminal modules.
Packaging uses setuptools.
