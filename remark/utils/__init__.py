"""
工具模块
"""

from remark.utils.encoding import sys_encode
from remark.utils.platform import check_platform
from remark.utils.constants import MAX_COMMENT_LENGTH

__all__ = [
    'sys_encode',
    'check_platform',
    'MAX_COMMENT_LENGTH',
]