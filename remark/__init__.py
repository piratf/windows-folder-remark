"""
Windows Folder Remark - 为 Windows 文件和文件夹添加备注工具
"""

__version__ = '2.0.0'
__author__ = 'Piratf'

from remark.core.base import CommentHandler
from remark.core.file_handler import FileCommentHandler
from remark.core.folder_handler import FolderCommentHandler

__all__ = [
    'CommentHandler',
    'FileCommentHandler',
    'FolderCommentHandler',
]