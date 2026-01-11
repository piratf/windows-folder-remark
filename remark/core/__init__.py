"""
核心功能模块
"""

from remark.core.base import CommentHandler
from remark.core.file_handler import FileCommentHandler
from remark.core.folder_handler import FolderCommentHandler

__all__ = [
    'CommentHandler',
    'FileCommentHandler',
    'FolderCommentHandler',
]