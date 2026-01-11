# -*- coding: utf-8 -*-

"""
编码处理工具
"""

import sys

defEncoding = sys.getfilesystemencoding()


def sys_encode(content):
    """将代码中的字符转换为系统编码"""
    try:
        return content.encode(defEncoding).decode(defEncoding)
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        print(sys_encode(u"编码转换错误: ") + str(e))
        return content