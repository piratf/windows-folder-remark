"""
文件夹备注处理器 - 使用 desktop.ini

使用 Microsoft 官方支持的 desktop.ini 方式设置文件夹备注。

参考文档:
https://learn.microsoft.com/en-us/windows/win32/shell/how-to-customize-folders-with-desktop-ini
"""

import os

from remark.core.base import CommentHandler
from remark.storage.desktop_ini import DesktopIniHandler
from remark.utils.constants import MAX_COMMENT_LENGTH


class FolderCommentHandler(CommentHandler):
    """文件夹备注处理器"""

    def set_comment(self, folder_path, comment):
        """设置文件夹备注"""
        if not os.path.isdir(folder_path):
            print("路径不是文件夹:", folder_path)
            return False

        if len(comment) > MAX_COMMENT_LENGTH:
            print("备注长度超过限制，最大长度为", MAX_COMMENT_LENGTH, "个字符")
            comment = comment[:MAX_COMMENT_LENGTH]

        return self._set_comment_desktop_ini(folder_path, comment)

    @staticmethod
    def _set_comment_desktop_ini(folder_path, comment):
        """使用 desktop.ini 设置备注"""
        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        try:
            # 清除文件属性以便修改
            if DesktopIniHandler.exists(
                folder_path
            ) and not DesktopIniHandler.clear_file_attributes(desktop_ini_path):
                print("清除文件属性失败")
                return False

            # 使用 UTF-16 编码写入 desktop.ini
            if not DesktopIniHandler.write_info_tip(folder_path, comment):
                print("写入 desktop.ini 失败")
                return False

            # 设置 desktop.ini 文件为隐藏和系统属性
            if not DesktopIniHandler.set_file_hidden_system_attributes(desktop_ini_path):
                print("设置文件属性失败")
                return False

            # 设置文件夹为只读属性（使 desktop.ini 生效）
            if not DesktopIniHandler.set_folder_system_attributes(folder_path):
                print("设置文件夹属性失败")
                return False

            print("备注添加成功")
            return True
        except Exception as e:
            print("设置备注失败:", str(e))
            return False

    def get_comment(self, folder_path):
        """获取文件夹备注"""
        return DesktopIniHandler.read_info_tip(folder_path)

    def delete_comment(self, folder_path):
        """删除文件夹备注"""
        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        if not DesktopIniHandler.exists(folder_path):
            print("该文件夹没有备注")
            return True

        # 清除文件属性以便修改
        if not DesktopIniHandler.clear_file_attributes(desktop_ini_path):
            print("清除文件属性失败")
            return False

        # 移除 InfoTip 行（保留其他设置如 IconResource）
        if not DesktopIniHandler.remove_info_tip(folder_path):
            print("移除备注失败")
            return False

        # 如果 desktop.ini 仍存在，恢复文件属性
        if DesktopIniHandler.exists(
            folder_path
        ) and not DesktopIniHandler.set_file_hidden_system_attributes(desktop_ini_path):
            print("恢复文件属性失败")
            return False

        print("备注删除成功")
        return True

    def supports(self, path):
        """检查是否支持该路径"""
        return os.path.isdir(path)
