# -*- coding: utf-8 -*-

"""
Desktop.ini 交互层

根据 Microsoft 官方文档要求，desktop.ini 文件必须使用 Unicode 格式
才能正确存储和显示本地化字符串。

参考文档:
https://learn.microsoft.com/en-us/windows/win32/shell/how-to-customize-folders-with-desktop-ini

引用: "Make sure the Desktop.ini file that you create is in the Unicode format.
This is necessary to store the localized strings that can be displayed to users."
"""

import os
import codecs


# Windows desktop.ini 标准编码格式
# 使用 'utf-16' 编码，codecs 会自动添加 UTF-16 LE BOM (0xFF 0xFE)
DESKTOP_INI_ENCODING = 'utf-16'
# Windows 行尾符
LINE_ENDING = '\r\n'


class DesktopIniHandler(object):
    """
    Desktop.ini 处理器

    提供对 desktop.ini 文件的读写操作，确保使用正确的编码格式
    以支持资源管理器正确显示中文等非 ASCII 字符。
    """

    # desktop.ini 文件名
    FILENAME = 'desktop.ini'
    # ShellClassInfo 段落
    SECTION_SHELL_CLASS_INFO = '[.ShellClassInfo]'
    # InfoTip 属性
    PROPERTY_INFOTIP = 'InfoTip'

    @staticmethod
    def get_path(folder_path):
        """
        获取 desktop.ini 文件路径

        Args:
            folder_path: 文件夹路径

        Returns:
            desktop.ini 文件的完整路径
        """
        return os.path.join(folder_path, DesktopIniHandler.FILENAME)

    @staticmethod
    def exists(folder_path):
        """
        检查 desktop.ini 是否存在

        Args:
            folder_path: 文件夹路径

        Returns:
            bool: desktop.ini 是否存在
        """
        return os.path.exists(DesktopIniHandler.get_path(folder_path))

    @staticmethod
    def read_info_tip(folder_path):
        """
        读取 desktop.ini 中的 InfoTip 值

        使用 UTF-16 编码读取，支持中文等非 ASCII 字符

        Args:
            folder_path: 文件夹路径

        Returns:
            str: InfoTip 值，如果不存在或读取失败返回 None
        """
        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        if not os.path.exists(desktop_ini_path):
            return None

        try:
            # 尝试多种编码读取，优先使用 UTF-16
            encodings = ['utf-16-le', 'utf-16', 'utf-8-sig', 'utf-8', 'gbk', 'mbcs']

            for encoding in encodings:
                try:
                    with codecs.open(desktop_ini_path, 'r', encoding=encoding) as f:
                        content = f.read()

                    # 解析 InfoTip
                    if DesktopIniHandler.PROPERTY_INFOTIP in content:
                        # 找到 InfoTip= 的位置
                        start = content.index(DesktopIniHandler.PROPERTY_INFOTIP + '=')
                        start += len(DesktopIniHandler.PROPERTY_INFOTIP + '=')

                        # 找到行尾
                        end = len(content)
                        for line_ending in ['\r\n', '\n', '\r']:
                            pos = content.find(line_ending, start)
                            if pos != -1 and pos < end:
                                end = pos
                                break

                        value = content[start:end].strip()
                        if value:
                            return value
                    # 如果找到了 InfoTip 但没有值，或者没找到 InfoTip，继续尝试下一个编码
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

        except Exception:
            pass

        return None

    @staticmethod
    def write_info_tip(folder_path, info_tip):
        """
        写入 InfoTip 到 desktop.ini

        使用 UTF-16 编码写入（自动添加 BOM），符合 Microsoft 官方文档要求。
        这确保中文等非 ASCII 字符在资源管理器中正确显示。

        Args:
            folder_path: 文件夹路径
            info_tip: 要写入的 InfoTip 值

        Returns:
            bool: 写入是否成功
        """
        if not info_tip:
            return False

        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        try:
            # 构建 desktop.ini 内容
            # 格式: [.ShellClassInfo]\r\nInfoTip=值\r\n
            content = (
                DesktopIniHandler.SECTION_SHELL_CLASS_INFO + LINE_ENDING +
                DesktopIniHandler.PROPERTY_INFOTIP + '=' + info_tip + LINE_ENDING
            )

            # 使用 UTF-16 编码写入，codecs 会自动添加 UTF-16 LE BOM (0xFF 0xFE)
            with codecs.open(desktop_ini_path, 'w', encoding=DESKTOP_INI_ENCODING) as f:
                f.write(content)

            return True

        except Exception as e:
            return False

    @staticmethod
    def delete(folder_path):
        """
        删除 desktop.ini 文件

        Args:
            folder_path: 文件夹路径

        Returns:
            bool: 删除是否成功
        """
        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        if not os.path.exists(desktop_ini_path):
            return True

        try:
            os.remove(desktop_ini_path)
            return True
        except Exception:
            return False

    @staticmethod
    def set_folder_system_attributes(folder_path):
        """
        设置文件夹为系统文件夹

        根据 Microsoft 文档，文件夹必须设置为系统文件夹
        Windows 才会读取 desktop.ini 中的自定义设置。

        参考: "Use PathMakeSystemFolder to make the folder a system folder.
        This sets the read-only bit on the folder to indicate that the special
        behavior reserved for Desktop.ini should be enabled."

        Args:
            folder_path: 文件夹路径

        Returns:
            bool: 设置是否成功
        """
        try:
            # 设置文件夹为只读/系统属性
            # read-only bit 通知 Windows 启用 desktop.ini 特殊行为
            import subprocess
            result = subprocess.call(
                'attrib +r "' + folder_path + '"',
                shell=True
            )
            return result == 0
        except Exception:
            return False

    @staticmethod
    def set_file_hidden_system_attributes(file_path):
        """
        设置 desktop.ini 文件为隐藏和系统属性

        根据 Microsoft 文档，desktop.ini 应该被标记为隐藏和系统文件
        以防止普通用户看到或修改它。

        Args:
            file_path: desktop.ini 文件路径

        Returns:
            bool: 设置是否成功
        """
        try:
            import subprocess
            result = subprocess.call(
                'attrib +h +s "' + file_path + '"',
                shell=True
            )
            return result == 0
        except Exception:
            return False

    @staticmethod
    def clear_file_attributes(file_path):
        """
        清除文件的隐藏和系统属性

        在修改 desktop.ini 之前需要调用，以便能够写入文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 清除是否成功
        """
        try:
            import subprocess
            result = subprocess.call(
                'attrib -s -h "' + file_path + '"',
                shell=True
            )
            return result == 0
        except Exception:
            return False