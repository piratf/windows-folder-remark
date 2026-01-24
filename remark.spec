# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for windows-folder-remark

Usage:
    pyinstaller remark.spec
"""

import os
import sys

from PyInstaller.utils.hooks import collect_submodules

# =============================================================================
# Configuration
# =============================================================================

block_cipher = None
app_name = "windows-folder-remark"
app_version = "2.0.0"
app_description = "Windows 文件夹备注工具"

# =============================================================================
# Analysis
# =============================================================================

# Collect all submodules from remark package
hiddenimports = collect_submodules('remark')

a = Analysis(
    [os.path.join("remark", "cli", "commands.py")],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# =============================================================================
# PYZ
# =============================================================================

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# =============================================================================
# EXE
# =============================================================================

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console application for interactive mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
