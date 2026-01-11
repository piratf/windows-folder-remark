# -*- coding: utf-8 -*-

"""
文件夹备注处理器 - 使用 desktop.ini

使用 Windows Property System API (IPropertyStore) 来设置文件夹备注。
相比 desktop.ini，Property Store 是更现代和推荐的方式，支持即时刷新显示。

注意：由于 Windows 文件夹不支持通过 Property Store 写入 PKEY_Comment，
此实现回退到使用 desktop.ini 方式，这是 Microsoft 官方支持的方法。
"""

import os
import sys

from remark.core.base import CommentHandler
from remark.utils.encoding import sys_encode
from remark.utils.constants import MAX_COMMENT_LENGTH
from remark.storage.desktop_ini import DesktopIniHandler


class FolderCommentHandler(CommentHandler):
    """文件夹备注处理器"""

    def set_comment(self, folder_path, comment):
        """设置文件夹备注"""
        if not os.path.isdir(folder_path):
            print(sys_encode(u"路径不是文件夹: ") + folder_path)
            return False

        if len(comment) > MAX_COMMENT_LENGTH:
            print(sys_encode(u"备注长度超过限制，最大长度为 ") + str(MAX_COMMENT_LENGTH) + sys_encode(u" 个字符"))
            comment = comment[:MAX_COMMENT_LENGTH]

        # Windows 文件夹不支持 Property Store 写入备注，使用 desktop.ini
        return self._set_comment_desktop_ini(folder_path, comment)

    def _set_comment_desktop_ini(self, folder_path, comment):
        """使用 desktop.ini 设置备注"""
        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        try:
            # 清除文件属性以便修改
            if DesktopIniHandler.exists(folder_path):
                if not DesktopIniHandler.clear_file_attributes(desktop_ini_path):
                    print(sys_encode(u"清除文件属性失败"))
                    return False

            # 使用 UTF-16 编码写入 desktop.ini
            if not DesktopIniHandler.write_info_tip(folder_path, comment):
                print(sys_encode(u"写入 desktop.ini 失败"))
                return False

            # 设置 desktop.ini 文件为隐藏和系统属性
            if not DesktopIniHandler.set_file_hidden_system_attributes(desktop_ini_path):
                print(sys_encode(u"设置文件属性失败"))
                return False

            # 设置文件夹为只读属性（使 desktop.ini 生效）
            if not DesktopIniHandler.set_folder_system_attributes(folder_path):
                print(sys_encode(u"设置文件夹属性失败"))
                return False

            # 通知 Windows Shell 刷新显示
            DesktopIniHandler.notify_shell_update(folder_path)

            print(sys_encode(u"备注添加成功"))
            return True
        except Exception as e:
            print(sys_encode(u"设置备注失败: ") + str(e))
            return False

    def get_comment(self, folder_path):
        """获取文件夹备注"""
        # 使用 desktop.ini 读取
        return DesktopIniHandler.read_info_tip(folder_path)

    def delete_comment(self, folder_path):
        """删除文件夹备注"""
        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        if not DesktopIniHandler.exists(folder_path):
            print(sys_encode(u"该文件夹没有备注"))
            return True

        # 清除文件属性以便删除
        if not DesktopIniHandler.clear_file_attributes(desktop_ini_path):
            print(sys_encode(u"去除文件属性失败"))
            return False

        # 删除 desktop.ini
        if DesktopIniHandler.delete(folder_path):
            # 通知 Windows Shell 刷新显示
            DesktopIniHandler.notify_shell_update(folder_path)
            print(sys_encode(u"备注删除成功"))
            return True
        else:
            print(sys_encode(u"删除文件失败"))
            return False

    def supports(self, path):
        """检查是否支持该路径"""
        return os.path.isdir(path)
