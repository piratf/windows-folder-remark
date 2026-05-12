# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for context menu helper exe.

Minimal build — only includes codecs + tkinter + inline desktop.ini logic.
No remark/ package imports to keep startup fast.
"""

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

block_cipher = None
app_name = "windows-folder-remark-context"

options = [("X utf8", None, "OPTION")]

a = Analysis(
    [os.path.join("remark", "cli", "context_entry.py")],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["tkinter", "codecs"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "setuptools",
        "setuptools.*",
        "distutils",
        "distutils.*",
        "unittest",
        "pydoc",
        "pydoc_data",
        "remark",
        "remark.*",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    options,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
