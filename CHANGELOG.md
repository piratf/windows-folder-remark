# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD for automated releases
- PyInstaller configuration for Windows executable builds
- Version management script for release automation
- Support for both 32-bit and 64-bit Windows builds

## [2.0.0] - Unreleased

### Added
- UTF-16 encoding detection and conversion for desktop.ini
- User confirmation prompt before encoding conversion
- EncodingConversionCanceled exception for safer error handling
- Smart delete logic: removes InfoTip while preserving other desktop.ini settings
- Top-level exception handling in CLI main()
- Windows platform check before running

### Changed
- Improved desktop.ini read/write operations with encoding safety
- Better error handling with exception-based flow control
- Enhanced folder comment handling with dedicated storage layer
- Refactored command-line argument parsing with argparse

### Fixed
- Fixed desktop.ini encoding issues
- Path handling with spaces using os.path.join()
- Exception handling for encoding conversion

### Removed
- File comment functionality (COM component and Property Store)
- notify_shell_update function (no longer needed)
- File-related imports and handlers

## [1.0] - 2022-05-03

### Added
- Interactive mode with continuous loop for batch processing
- Help system with usage instructions
- Comment length validation
- Complete exception handling mechanism

### Fixed
- Path with spaces handling issue
- Command injection vulnerability (subprocess replaced os.system)
- Encoding conversion exception handling
- Explicit file write encoding specification

### Changed
- Improved help messages and usage prompts
- Packaged as Windows executable

[Unreleased]: https://github.com/piratf/windows-folder-remark/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/piratf/windows-folder-remark/compare/v1.0...v2.0.0
[1.0]: https://github.com/piratf/windows-folder-remark/releases/tag/v1.0
