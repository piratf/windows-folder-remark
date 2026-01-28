# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for windows-folder-remark

Usage:
    pyinstaller remark.spec
"""

import os
import re
import sys
import subprocess

from PyInstaller.utils.hooks import collect_submodules

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def get_upx_dir():
    local_upx_dir = os.path.join(SPECPATH, "tools", "upx")
    upx_exe = os.path.join(local_upx_dir, "upx.exe")

    if os.path.exists(upx_exe):
        return local_upx_dir

    print("WARNING: UPX not available, compression disabled (exe will be larger)")
    print("HINT: Run 'python scripts/ensure_upx.py' to install UPX automatically")
    return None

# =============================================================================
# Configuration
# =============================================================================

block_cipher = None
app_name = "windows-folder-remark"


def get_app_version():
    """从 pyproject.toml 的 [project] 部分读取版本号，确保版本同步"""
    # SPECPATH 是 PyInstaller 提供的内置全局变量，指向 spec 文件所在目录
    toml_file = os.path.join(SPECPATH, "pyproject.toml")
    with open(toml_file, encoding="utf-8") as f:
        lines = f.readlines()

    # 只查找 [project] 部分的 version 字段
    in_project_section = False
    for line in lines:
        if line.strip() == "[project]":
            in_project_section = True
        elif line.startswith("[") and not line.startswith("[["):
            in_project_section = False
        elif in_project_section and line.strip().startswith("version"):
            match = re.search(r'=\s*["\']([^"\']+)["\']', line)
            if match:
                return match.group(1)
    return "unknown"


app_version = get_app_version()
app_description = "Windows 文件夹备注工具"

# =============================================================================
# Python Interpreter Options
# =============================================================================

# 强制启用 UTF-8 模式，支持中文等特殊字符输出
# See: https://pyinstaller.org/en/stable/spec-files.html#specifying-python-interpreter-options
options = [
    ('X utf8', None, 'OPTION'),
]

# =============================================================================
# Analysis
# =============================================================================

# Collect all submodules from remark package
hiddenimports = collect_submodules('remark') + [
    'tkinter',
    'packaging',
    'packaging.version',
]

a = Analysis(
    [os.path.join("remark", "cli", "commands.py")],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'setuptools',
        'setuptools.*',
        'distutils',
        'distutils.*',
        'unittest',
        'pydoc',
        'pydoc_data',
    ],
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

upx_dir = get_upx_dir()

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    options,  # Python 解释器选项：启用 UTF-8 模式
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=upx_dir is not None,
    upx_dir=upx_dir if upx_dir is not None else "",
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console application for interactive mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
