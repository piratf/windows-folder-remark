# -*- coding: utf-8 -*-

"""
平台检查工具
"""

import platform
from remark.utils.encoding import sys_encode


def check_platform():
    """检查是否为 Windows 系统"""
    if platform.system() != 'Windows':
        print(sys_encode(u"错误: 此工具为 Windows 系统中的文件/文件夹添加备注，暂不支持其他系统。"))
        print(sys_encode(u"当前系统: ") + platform.system())
        return False
    return True