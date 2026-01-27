"""
Windows 注册表操作工具

用于安装/卸载右键菜单到 Windows 资源管理器。
"""

import contextlib
import os
import sys
import winreg

# =============================================================================
# 常量定义
# =============================================================================

REGISTRY_ROOT = winreg.HKEY_CURRENT_USER
REGISTRY_PATH = r"Software\Classes\Directory\shell\WindowsFolderRemark"
MENU_NAME = "添加文件夹备注"
ICON_INDEX = 0


# =============================================================================
# 工具函数
# =============================================================================


def get_executable_path() -> str:
    """
    获取可执行文件路径

    Returns:
        开发环境: 返回 python 脚本路径（用于测试）
        打包后: 返回 exe 文件完整路径
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后，sys.executable 指向 exe 文件
        return sys.executable
    else:
        # 开发环境，从 __file__ 推导脚本路径
        current_file = os.path.abspath(__file__)
        # remark/utils/registry.py -> remark.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(current_file)), "remark.py")
        return os.path.abspath(script_path)


def install_context_menu() -> bool:
    r"""
    安装右键菜单到注册表

    创建的注册表结构:
    HKCU\Software\Classes\Directory\shell\WindowsFolderRemark
        @="添加文件夹备注"
        Icon="[exe_path],0"
        \command
            @="[exe_path] --gui "%1""

    Returns:
        成功返回 True，失败返回 False
    """
    exe_path = get_executable_path()

    try:
        # 创建主键
        key = winreg.CreateKey(REGISTRY_ROOT, REGISTRY_PATH)

        # 设置默认值（菜单显示文本）
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_NAME)

        # 设置图标（使用 exe 文件的第一个图标）
        icon_value = f'"{exe_path}",{ICON_INDEX}'
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_value)

        winreg.CloseKey(key)

        # 创建 command 子键
        command_path = f"{REGISTRY_PATH}\\command"
        command_key = winreg.CreateKey(REGISTRY_ROOT, command_path)

        # 设置命令
        command_value = f'"{exe_path}" --gui "%1"'
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, command_value)

        winreg.CloseKey(command_key)

        return True

    except PermissionError:
        return False
    except OSError:
        return False


def uninstall_context_menu() -> bool:
    """
    从注册表卸载右键菜单

    Returns:
        成功返回 True（包括键不存在的情况），失败返回 False
    """
    try:
        # 先删除 command 子键
        command_path = f"{REGISTRY_PATH}\\command"
        with contextlib.suppress(FileNotFoundError):
            winreg.DeleteKey(REGISTRY_ROOT, command_path)

        # 删除主键
        with contextlib.suppress(FileNotFoundError):
            winreg.DeleteKey(REGISTRY_ROOT, REGISTRY_PATH)

        return True

    except PermissionError:
        return False
    except OSError:
        return False
