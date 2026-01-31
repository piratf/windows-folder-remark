"""
文件夹备注处理器 - 使用 desktop.ini

使用 Microsoft 官方支持的 desktop.ini 方式设置文件夹备注。

参考文档:
https://learn.microsoft.com/en-us/windows/win32/shell/how-to-customize-folders-with-desktop-ini
"""

import os

from remark.core.base import CommentHandler
from remark.i18n import _ as _
from remark.storage.desktop_ini import DesktopIniHandler
from remark.utils.constants import MAX_COMMENT_LENGTH


class FolderCommentHandler(CommentHandler):
    """文件夹备注处理器"""

    def set_comment(self, folder_path: str, comment: str) -> bool:
        """设置文件夹备注"""
        if not os.path.isdir(folder_path):
            print(_("Path is not a folder: {folder_path}").format(folder_path=folder_path))
            return False

        if len(comment) > MAX_COMMENT_LENGTH:
            print(
                _("Remark length exceeds limit, maximum length is {length} characters").format(
                    length=MAX_COMMENT_LENGTH
                )
            )
            comment = comment[:MAX_COMMENT_LENGTH]

        return self._set_comment_desktop_ini(folder_path, comment)

    @staticmethod
    def _set_comment_desktop_ini(folder_path: str, comment: str) -> bool:
        """使用 desktop.ini 设置备注"""
        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        try:
            # 清除文件属性以便修改
            if DesktopIniHandler.exists(
                folder_path
            ) and not DesktopIniHandler.clear_file_attributes(desktop_ini_path):
                print(_("Failed to clear file attributes"))
                return False

            # 使用 UTF-16 编码写入 desktop.ini
            if not DesktopIniHandler.write_info_tip(folder_path, comment):
                print(_("Failed to write desktop.ini"))
                return False

            # 设置 desktop.ini 文件为隐藏和系统属性
            if not DesktopIniHandler.set_file_hidden_system_attributes(desktop_ini_path):
                print(_("Failed to set file attributes"))
                return False

            # 设置文件夹为只读属性（使 desktop.ini 生效）
            if not DesktopIniHandler.set_folder_system_attributes(folder_path):
                print(_("Failed to set folder attributes"))
                return False

            print(
                _("Remark [{remark}] has been set for folder [{folder_path}]").format(
                    remark=comment, folder_path=folder_path
                )
            )
            print(_("Remark added successfully, may take a few minutes to display"))
            return True
        except Exception as e:
            print(_("Failed to set remark: {error}").format(error=str(e)))
            return False

    def get_comment(self, folder_path: str) -> str | None:
        """获取文件夹备注"""
        return DesktopIniHandler.read_info_tip(folder_path)

    def delete_comment(self, folder_path: str) -> bool:
        """删除文件夹备注"""
        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        if not DesktopIniHandler.exists(folder_path):
            print(_("This folder has no remark"))
            return True

        # 清除文件属性以便修改
        if not DesktopIniHandler.clear_file_attributes(desktop_ini_path):
            print(_("Failed to clear file attributes"))
            return False

        # 移除 InfoTip 行（保留其他设置如 IconResource）
        if not DesktopIniHandler.remove_info_tip(folder_path):
            print(_("Failed to remove remark"))
            return False

        # 如果 desktop.ini 仍存在，恢复文件属性
        if DesktopIniHandler.exists(
            folder_path
        ) and not DesktopIniHandler.set_file_hidden_system_attributes(desktop_ini_path):
            print(_("Failed to restore file attributes"))
            return False

        print(_("Remark deleted successfully"))
        return True

    def supports(self, path: str) -> bool:
        """检查是否支持该路径"""
        return os.path.isdir(path)
