<div align="center">
  <img src="assets/UT.png" alt="Unified Terminal logo" width="128">
  <h1>Unified Terminal</h1>
  <p>A lightweight, cross-platform terminal emulator built with Python, Qt, and pyte.</p>
</div>

Unified Terminal brings a native desktop window to your shell, with a custom
terminal display and platform-specific pseudo-terminal backends for Windows
and Linux.

## Features

- **Windows and Linux support** — launches PowerShell on Windows and your
  configured interactive shell on Linux.
- **ANSI terminal rendering** — uses [pyte](https://github.com/selectel/pyte)
  to interpret terminal output, including cursor movement and colors.
- **Responsive terminal grid** — updates the shell's rows and columns when
  the window is resized.
- **Clipboard support** — drag to select text, then copy and paste from the
  keyboard or the right-click menu.
- **Keyboard input** — supports common terminal keys, control sequences,
  navigation keys, and function keys.
- **Readable by default** — dark colors and a monospace font, choosing an
  available terminal font where possible.
- **Closes with the shell** — the application window exits when its shell
  session ends.

## Requirements

- Python **3.13 or newer**
- Windows or Linux
- On Windows, PowerShell and the `pywinpty` dependency (installed
  automatically)
- On Linux, an interactive shell available at `$SHELL` (or `/bin/bash`)
- On Debian-based Linux, the Qt XCB platform plugin requires `libxcb-cursor0`

Install the XCB runtime dependency on Debian or Ubuntu with:

```shell
sudo apt install libxcb-cursor0
```

## Install and run

Clone the repository and install the project in editable mode:

```shell
git clone <repository-url>
cd unified-terminal
python -m pip install -e .
```

Launch the application:

```shell
unified-terminal
```

You can also launch it as a Python module:

```shell
python -m unified_terminal
```

On Windows, the application starts PowerShell without loading a profile. On
Linux, it starts the interactive shell named by the `SHELL` environment
variable; if `SHELL` is not set, it starts `/bin/bash`.

## Keyboard shortcuts

| Action | Shortcut |
| --- | --- |
| Copy selected text | `Ctrl+Shift+C` or `Ctrl+Insert` |
| Paste from clipboard | `Ctrl+Shift+V` or `Shift+Insert` |
| Interrupt the running command | `Ctrl+C` (when no text is selected) |

You can also select text by dragging with the left mouse button and use the
right-click menu to copy or paste.

## Development

Install the project and its runtime dependencies with:

```shell
python -m pip install -e .
```

The application entry point is `src/unified_terminal/__main__.py`.

## Project status

Terminal feature support is evolving. Some advanced terminal-emulator
features and application-specific behavior may not yet be supported.
