"""
平台检查工具
"""

import platform

from remark.i18n import _ as _


def check_platform() -> bool:
    """检查是否为 Windows 系统"""
    if platform.system() != "Windows":
        print(_("Error: This tool adds remarks to files/folders on Windows, other systems are not supported."))
        print(_("Current system: {system}").format(system=platform.system()))
        return False
    return True
