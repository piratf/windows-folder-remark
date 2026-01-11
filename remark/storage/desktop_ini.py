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
import sys
import codecs


class EncodingConversionCanceled(Exception):
    """编码转换被用户取消"""
    pass


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

        如果 desktop.ini 已存在且包含其他设置（如 IconResource），会保留这些设置。

        Args:
            folder_path: 文件夹路径
            info_tip: 要写入的 InfoTip 值

        Returns:
            bool: 写入是否成功

        Raises:
            EncodingConversionCanceled: 用户拒绝编码转换
        """
        if not info_tip:
            return False

        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        try:
            # 如果文件已存在，读取并更新
            if os.path.exists(desktop_ini_path):
                # 确保是 UTF-16 编码（用户拒绝会抛出异常）
                DesktopIniHandler.ensure_utf16_encoding(desktop_ini_path)

                with codecs.open(desktop_ini_path, 'r', encoding=DESKTOP_INI_ENCODING) as f:
                    content = f.read()

                # 检查是否已有 InfoTip
                lines = content.splitlines()
                new_lines = []
                info_tip_updated = False

                for line in lines:
                    stripped = line.strip()
                    # 更新现有 InfoTip 行
                    if stripped.startswith(DesktopIniHandler.PROPERTY_INFOTIP + '=') or \
                       stripped.startswith(DesktopIniHandler.PROPERTY_INFOTIP + ' '):
                        new_lines.append(DesktopIniHandler.PROPERTY_INFOTIP + '=' + info_tip)
                        info_tip_updated = True
                    else:
                        new_lines.append(line)

                # 如果没有 InfoTip，添加它
                if not info_tip_updated:
                    # 找到 [.ShellClassInfo] 后插入
                    inserted = False
                    for i, line in enumerate(new_lines):
                        if line.strip().startswith('[.ShellClassInfo]'):
                            new_lines.insert(i + 1, DesktopIniHandler.PROPERTY_INFOTIP + '=' + info_tip)
                            inserted = True
                            break
                    if not inserted:
                        # 没找到 section，添加整个 section
                        new_lines = [
                            DesktopIniHandler.SECTION_SHELL_CLASS_INFO,
                            DesktopIniHandler.PROPERTY_INFOTIP + '=' + info_tip
                        ]

                new_content = LINE_ENDING.join(new_lines)
            else:
                # 新建文件
                new_content = (
                    DesktopIniHandler.SECTION_SHELL_CLASS_INFO + LINE_ENDING +
                    DesktopIniHandler.PROPERTY_INFOTIP + '=' + info_tip + LINE_ENDING
                )

            # 使用 UTF-16 编码写入
            with codecs.open(desktop_ini_path, 'w', encoding=DESKTOP_INI_ENCODING) as f:
                f.write(new_content)

            return True

        except EncodingConversionCanceled:
            return False
        except Exception:
            return False

    @staticmethod
    def detect_encoding(file_path):
        """
        检测文件编码

        Args:
            file_path: 文件路径

        Returns:
            tuple: (encoding_name, is_utf16)
                - encoding_name: 检测到的编码名称
                - is_utf16: 是否为 UTF-16 编码
        """
        # 检查 BOM
        try:
            with open(file_path, 'rb') as f:
                bom = f.read(4)

            if bom[:2] == b'\xff\xfe':  # UTF-16 LE BOM
                return 'utf-16-le', True
            elif bom[:2] == b'\xfe\xff':  # UTF-16 BE BOM
                return 'utf-16-be', True
            elif bom[:3] == b'\xef\xbb\xbf':  # UTF-8 BOM
                return 'utf-8-sig', False
        except Exception:
            pass

        # 尝试检测其他编码
        for encoding in ['utf-8', 'gbk', 'mbcs']:
            try:
                with codecs.open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding, False
            except (UnicodeDecodeError, UnicodeError):
                continue

        return None, False

    @staticmethod
    def ensure_utf16_encoding(file_path):
        """
        确保文件是 UTF-16 编码，如果不是则提示用户确认转换

        如果用户拒绝转换，抛出 EncodingConversionCanceled 异常。

        Args:
            file_path: 文件路径

        Raises:
            EncodingConversionCanceled: 用户拒绝转换
        """
        encoding, is_utf16 = DesktopIniHandler.detect_encoding(file_path)

        if is_utf16:
            return  # 已经是 UTF-16

        # 文件不是 UTF-16，需要用户确认
        print(f"警告：desktop.ini 文件编码为 {encoding or '未知'}，不是标准的 UTF-16。")
        print("修改此文件前需要先转换为 UTF-16 编码。")
        print("原内容会被保留，仅改变编码格式。")

        try:
            # 显示文件预览
            with codecs.open(file_path, 'r', encoding=encoding or 'utf-8') as f:
                content = f.read()

            print("\n当前文件内容:")
            print("-" * 40)
            print(content)
            print("-" * 40)

            # 用户确认
            while True:
                response = input("\n是否转换为 UTF-16 编码后继续？[Y/n]: ").strip().lower()
                if response in ('', 'y', 'yes'):
                    break
                elif response in ('n', 'no'):
                    print("操作已取消。")
                    raise EncodingConversionCanceled("用户拒绝编码转换")
                else:
                    print("请输入 Y 或 n")

            # 执行转换
            with codecs.open(file_path, 'w', encoding=DESKTOP_INI_ENCODING) as f:
                f.write(content)

            print("✓ 已转换为 UTF-16 编码。")

        except EncodingConversionCanceled:
            raise
        except Exception as e:
            print(f"转换失败: {e}")
            print("操作已取消。")
            raise EncodingConversionCanceled(f"编码转换失败: {e}")

    @staticmethod
    def remove_info_tip(folder_path):
        """
        移除 desktop.ini 中的 InfoTip

        只删除 InfoTip 行，保留其他设置（如 IconResource, Logo 等）。

        Args:
            folder_path: 文件夹路径

        Returns:
            bool: 操作是否成功

        Raises:
            EncodingConversionCanceled: 用户拒绝编码转换
        """
        desktop_ini_path = DesktopIniHandler.get_path(folder_path)

        if not os.path.exists(desktop_ini_path):
            return True

        try:
            # 确保文件是 UTF-16 编码
            DesktopIniHandler.ensure_utf16_encoding(desktop_ini_path)

            # 读取内容（UTF-16）
            with codecs.open(desktop_ini_path, 'r', encoding=DESKTOP_INI_ENCODING) as f:
                content = f.read()

            # 移除 InfoTip 行
            lines = content.splitlines()
            new_lines = []
            for line in lines:
                # 跳过 InfoTip 行（支持 = 前后有/无空格）
                stripped = line.strip()
                if stripped.startswith(DesktopIniHandler.PROPERTY_INFOTIP + '=') or \
                   stripped.startswith(DesktopIniHandler.PROPERTY_INFOTIP + ' '):
                    continue
                new_lines.append(line)

            # 检查是否还有有效内容
            has_content = False
            for line in new_lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('[.ShellClassInfo]'):
                    has_content = True
                    break

            # 如果没有其他内容，删除文件
            if not has_content:
                os.remove(desktop_ini_path)
                return True

            # 用 UTF-16 写回
            new_content = LINE_ENDING.join(new_lines)
            with codecs.open(desktop_ini_path, 'w', encoding=DESKTOP_INI_ENCODING) as f:
                f.write(new_content)

            return True

        except EncodingConversionCanceled:
            return False
        except Exception:
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
        设置文件夹为只读属性

        根据 Microsoft 文档和社区讨论，文件夹必须设置为只读属性
        Windows 才会读取 desktop.ini 中的自定义设置。

        参考: "Apply the read-only attribute for each folder.
        This will make Explorer process the desktop.ini file for that folder."
        https://superuser.com/questions/1117824/how-to-get-windows-to-read-copied-desktop-ini-file

        Args:
            folder_path: 文件夹路径

        Returns:
            bool: 设置是否成功
        """
        try:
            import subprocess
            import ctypes

            # 使用 Windows API 检查文件夹是否已有只读属性
            FILE_ATTRIBUTE_READONLY = 0x01
            GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW

            attrs = GetFileAttributesW(folder_path)
            if attrs == 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
                return False

            # 如果已有只读属性，无需再次设置
            if attrs & FILE_ATTRIBUTE_READONLY:
                return True

            # 设置文件夹为只读属性
            result = subprocess.call(
                'attrib +r "' + folder_path + '"',
                shell=True,
                stdout=subprocess.DEVNULL,  # 抑制输出
                stderr=subprocess.DEVNULL
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