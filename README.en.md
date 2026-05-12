# Windows Folder Remark Tool

**[中文文档](README.md)** | [English](README.en.md)

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Add remarks to Windows folders via `Desktop.ini`. Native GUI, fully local, no background process.

## Features

- **GUI-first** — no terminal needed to use
- **Right-click menu** — native dialog, no black console window
- **Unicode support** — UTF-16 LE encoding for all languages
- **Automatic updates** — checks GitHub Releases for new versions

## Installation

Download both files from [Releases](https://github.com/piratf/windows-folder-remark/releases), same directory:

| File | Purpose |
|------|---------|
| `windows-folder-remark.exe` | Main program, double-click to open |
| `windows-folder-remark-context.exe` | Context menu helper, invoked automatically |

## Usage

### Main Window

Double-click `windows-folder-remark.exe`:

- Browse / type a folder path
- View, set, or delete the remark
- Install / uninstall the right-click context menu
- Check for updates

### Context Menu

Click "Install Context Menu" in the main window:

- **Win10**: Right-click a folder → "Add Folder Remark"
- **Win11**: Right-click → Show more options → Add Folder Remark

### Command Line (optional)

```bash
windows-folder-remark.exe --install       # Install context menu
windows-folder-remark.exe --uninstall     # Uninstall context menu
windows-folder-remark.exe --update        # Check for updates
```

## How It Works

1. Creates/modifies `Desktop.ini` in the target folder
2. Writes `[.ShellClassInfo]` + `InfoTip=<remark>`
3. UTF-16 LE encoding
4. Sets hidden+system attributes on the file and read-only on the folder

Reference: [Microsoft Docs](https://learn.microsoft.com/en-us/windows/win32/shell/how-to-customize-folders-with-desktop-ini)

## Notes

- May take a minute or two to appear in File Explorer
- Network locations (NAS, mapped drives) are not supported
- Some third-party file managers do not display folder remarks

## License

MIT License
