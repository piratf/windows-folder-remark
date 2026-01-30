# Windows Folder Remark/Comment Tool

[![PyPI](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![en](https://img.shields.io/badge/lang-en-blue.svg)](README.en.md)
[![zh](https://img.shields.io/badge/lang-zh-red.svg)](README.md)

A lightweight CLI tool to add remarks/comments to Windows folders via Desktop.ini. No background processes, privacy-first, ~12MB portable exe. Perfect for organizing your files with custom descriptions.

## ⭐ Star Us

If you find this tool helpful, please consider giving it a star on GitHub!

## Why This Tool

- **No Background Processes**: Runs when needed, exits when done — zero background footprint
- **Lightweight**: Only ~12 MB, minimal system resource usage
- **Privacy-First**: Completely local operation, no data sent to any server

## Features

- Multi-language character support (UTF-16 encoding)
- Multi-language interface support (English, Chinese)
- Command-line and interactive modes
- Automatic encoding detection and repair
- Automatic update checking to stay current
- Right-click menu integration for quick access
- Single-file exe packaging, no Python environment required

## Installation

### Method 1: Using exe file (Recommended)

Download `windows-folder-remark.exe` from [releases](https://github.com/piratf/windows-folder-remark/releases) and use directly.

### Method 2: Install from source

```bash
# Clone repository
git clone https://github.com/piratf/windows-folder-remark.git
cd windows-folder-remark

# Install dependencies (no external dependencies)
pip install -e .

# Run
python -m remark.cli --help
```

## Usage

### Command-line Mode

```bash
# Add remark
windows-folder-remark.exe "C:\MyFolder" "This is my folder"

# View remark
windows-folder-remark.exe --view "C:\MyFolder"

# Delete remark
windows-folder-remark.exe --delete "C:\MyFolder"

# Check updates
windows-folder-remark.exe --update

# Install right-click menu
windows-folder-remark.exe --install

# Uninstall right-click menu
windows-folder-remark.exe --uninstall
```

### Interactive Mode

```bash
# Follow prompts after running
windows-folder-remark.exe
```

### Right-click Menu (Recommended)

After installing the right-click menu, you can add remarks directly in File Explorer by right-clicking folders:

```bash
# Install right-click menu
windows-folder-remark.exe --install
```

- **Windows 10**: Right-click folder to see "Add Folder Remark"
- **Windows 11**: Right-click folder → Click "Show more options" → Add Folder Remark

### Auto Update

The program automatically checks for updates on exit (once every 24 hours) and prompts if a new version is available.

You can also manually check for updates:

```bash
windows-folder-remark.exe --update
```

## Encoding Detection

When viewing remarks with `--view`, if the `desktop.ini` file is not in standard UTF-16 encoding, the tool will prompt you:

```
Warning: desktop.ini file encoding is utf-8, not standard UTF-16.
This may cause Chinese and other special characters to display abnormally.
Fix encoding to UTF-16? [Y/n]:
```

Select `Y` to automatically fix the encoding.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code check
ruff check .
ruff format .

# Type check
mypy remark/

# Build exe locally
python -m scripts.build
```

## How It Works

This tool implements folder remarks through these steps:

1. Create/modify `Desktop.ini` file in the folder
2. Write `[.ShellClassInfo]` section and `InfoTip` property
3. Save file with UTF-16 encoding
4. Set `Desktop.ini` as hidden and system attributes
5. Set folder as read-only (makes Windows read `Desktop.ini`)

Reference: [Microsoft Official Documentation](https://learn.microsoft.com/en-us/windows/win32/shell/how-to-customize-folders-with-desktop-ini)

## Notes

- May take a few minutes to display in File Explorer after modification
- Some file managers may not support folder remarks
- The tool modifies system attributes of folders

## License

MIT License
