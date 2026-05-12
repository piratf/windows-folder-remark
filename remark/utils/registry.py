"""
Windows 注册表操作工具

用于安装/卸载右键菜单到 Windows 资源管理器。
优先使用 context exe (轻量)，不可用时回退到主 exe。
"""

import contextlib
import os
import sys
import winreg

REGISTRY_ROOT = winreg.HKEY_CURRENT_USER
REGISTRY_PATH = r"Software\Classes\Directory\shell\WindowsFolderRemark"
MENU_NAME = "添加文件夹备注"
ICON_INDEX = 0


def _find_context_exe() -> str | None:
    """Find the lightweight context-menu exe, or fall back to main exe."""
    candidates = []

    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "windows-folder-remark-context.exe"))

    # Development fallback
    try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidates.append(
            os.path.join(root, "dist_new", "windows-folder-remark-context.exe"))
        candidates.append(os.path.join(root, "dist", "windows-folder-remark-context.exe"))
    except NameError:
        pass

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _get_main_exe() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    else:
        current_file = os.path.abspath(__file__)
        script_path = os.path.join(os.path.dirname(os.path.dirname(current_file)), "remark.py")
        return os.path.abspath(script_path)


def is_context_menu_installed() -> bool:
    try:
        winreg.OpenKey(REGISTRY_ROOT, REGISTRY_PATH)
        return True
    except FileNotFoundError:
        return False


def install_context_menu() -> bool:
    r"""
    Install right-click menu.

    Prefers the lightweight context exe (windows-folder-remark-context.exe).
    Falls back to main exe + --gui.

    Registry structure:
    HKCU\Software\Classes\Directory\shell\WindowsFolderRemark
        @="添加文件夹备注"
        Icon="[exe_path],0"
        \command
            @="[exe_path] "%1""
    """
    context_exe = _find_context_exe()
    if context_exe:
        exe_path = context_exe
        command_value = f'"{exe_path}" "%1"'
    else:
        exe_path = _get_main_exe()
        command_value = f'"{exe_path}" --gui "%1"'

    try:
        key = winreg.CreateKey(REGISTRY_ROOT, REGISTRY_PATH)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_NAME)
        icon_value = f'"{exe_path}",{ICON_INDEX}'
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_value)
        winreg.CloseKey(key)

        command_path = f"{REGISTRY_PATH}\\command"
        command_key = winreg.CreateKey(REGISTRY_ROOT, command_path)
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, command_value)
        winreg.CloseKey(command_key)

        return True
    except (PermissionError, OSError):
        return False


def uninstall_context_menu() -> bool:
    try:
        command_path = f"{REGISTRY_PATH}\\command"
        with contextlib.suppress(FileNotFoundError):
            winreg.DeleteKey(REGISTRY_ROOT, command_path)
        with contextlib.suppress(FileNotFoundError):
            winreg.DeleteKey(REGISTRY_ROOT, REGISTRY_PATH)
        return True
    except (PermissionError, OSError):
        return False
