"""desktop.ini 读写单元测试"""

import os
from unittest.mock import MagicMock, patch

import pytest

from remark.storage.desktop_ini import (
    DESKTOP_INI_ENCODING,
    LINE_ENDING,
    DesktopIniHandler,
    EncodingConversionCanceled,
)


@pytest.mark.unit
class TestDesktopIniHandler:
    """desktop.ini 处理器测试"""

    def test_get_path(self):
        """测试获取路径"""
        result = DesktopIniHandler.get_path("/test/folder")
        # 使用 normpath 比较以兼容不同平台的路径分隔符
        assert os.path.normpath(result) == os.path.normpath("/test/folder/desktop.ini")

    @pytest.mark.parametrize(
        "exists_return,expected",
        [(True, True), (False, False)],
    )
    def test_exists(self, exists_return, expected):
        """测试文件存在检测"""
        with patch("os.path.exists", return_value=exists_return):
            result = DesktopIniHandler.exists("/folder")
            assert result is expected

    def test_read_info_tip_no_file(self):
        """测试读取不存在的文件"""
        with patch("os.path.exists", return_value=False):
            result = DesktopIniHandler.read_info_tip("/folder")
            assert result is None

    @pytest.mark.parametrize(
        "content,expected",
        [
            ("[.ShellClassInfo]\r\nInfoTip=测试备注\r\n", "测试备注"),
            ("[.ShellClassInfo]\nInfoTip=测试备注\n", "测试备注"),
            ("[.ShellClassInfo]\r\nInfoTip=English Comment\r\n", "English Comment"),
            ("[.ShellClassInfo]\r\nInfoTip=备注\r\nIconResource=icon.dll\r\n", "备注"),
            ("[.ShellClassInfo]\r\nIconResource=icon.dll\r\n", None),
            ("[.ShellClassInfo]\r\n", None),
            ("No InfoTip here", None),
        ],
    )
    def test_read_info_tip_with_content(self, content, expected):
        """测试读取各种内容格式"""
        with patch("os.path.exists", return_value=True), patch("codecs.open") as mock_open_func:
            mock_file = MagicMock()
            mock_file.read.return_value = content
            mock_open_func.return_value.__enter__.return_value = mock_file

            result = DesktopIniHandler.read_info_tip("/folder")
            assert result == expected

    def test_write_info_tip_empty(self):
        """测试写入空备注"""
        result = DesktopIniHandler.write_info_tip("/folder", "")
        assert result is False

    def test_write_info_tip_new_file(self):
        """测试写入新文件"""
        with patch("os.path.exists", return_value=False), patch("codecs.open") as mock_open_func:
            mock_file = MagicMock()
            mock_open_func.return_value.__enter__.return_value = mock_file

            result = DesktopIniHandler.write_info_tip("/folder", "新备注")
            assert result is True
            mock_file.write.assert_called_once()

    def test_write_info_tip_update_existing(self):
        """测试更新已有文件"""
        existing_content = "[.ShellClassInfo]\r\nInfoTip=旧备注\r\n"
        with (
            patch("os.path.exists", return_value=True),
            patch("remark.storage.desktop_ini.DesktopIniHandler.ensure_utf16_encoding"),
            patch("codecs.open") as mock_open_func,
        ):
            mock_file_read = MagicMock()
            mock_file_read.read.return_value = existing_content
            mock_file_write = MagicMock()
            mock_open_func.side_effect = [mock_file_read, mock_file_write]

            result = DesktopIniHandler.write_info_tip("/folder", "新备注")
            assert result is True

    def test_detect_encoding_utf16_le(self):
        """测试检测 UTF-16 LE 编码"""
        with patch("builtins.open") as mock_open_func:
            mock_file = MagicMock()
            mock_file.read.return_value = b"\xff\xfe\x00\x00"
            mock_open_func.return_value.__enter__.return_value = mock_file

            encoding, is_utf16 = DesktopIniHandler.detect_encoding("/test.ini")
            assert encoding == "utf-16-le"
            assert is_utf16 is True

    def test_detect_encoding_utf16_be(self):
        """测试检测 UTF-16 BE 编码"""
        with patch("builtins.open") as mock_open_func:
            mock_file = MagicMock()
            mock_file.read.return_value = b"\xfe\xff\x00\x00"
            mock_open_func.return_value.__enter__.return_value = mock_file

            encoding, is_utf16 = DesktopIniHandler.detect_encoding("/test.ini")
            assert encoding == "utf-16-be"
            assert is_utf16 is True

    def test_detect_encoding_utf8_bom(self):
        """测试检测 UTF-8 BOM 编码"""
        with patch("builtins.open") as mock_open_func:
            mock_file = MagicMock()
            mock_file.read.return_value = b"\xef\xbb\xbf"
            mock_open_func.return_value.__enter__.return_value = mock_file

            encoding, is_utf16 = DesktopIniHandler.detect_encoding("/test.ini")
            assert encoding == "utf-8-sig"
            assert is_utf16 is False

    def test_set_file_hidden_system_attributes(self):
        """测试设置文件隐藏系统属性"""
        with patch("subprocess.call", return_value=0) as mock_call:
            result = DesktopIniHandler.set_file_hidden_system_attributes("/file")
            assert result is True
            mock_call.assert_called_once()
            args = mock_call.call_args[0][0]
            assert "attrib +h +s" in args
            assert "/file" in args or '"file"' in args or "file" in args

    def test_clear_file_attributes(self):
        """测试清除文件属性"""
        with patch("subprocess.call", return_value=0) as mock_call:
            result = DesktopIniHandler.clear_file_attributes("/file")
            assert result is True
            mock_call.assert_called_once()
            args = mock_call.call_args[0][0]
            assert "attrib -s -h" in args

    def test_delete_file_exists(self):
        """测试删除存在的文件"""
        with patch("os.path.exists", return_value=True), patch("os.remove"):
            result = DesktopIniHandler.delete("/folder")
            assert result is True

    def test_delete_no_file(self):
        """测试删除不存在的文件"""
        with patch("os.path.exists", return_value=False):
            result = DesktopIniHandler.delete("/folder")
            assert result is True

    def test_constants(self):
        """测试常量定义"""
        assert DESKTOP_INI_ENCODING == "utf-16"
        assert LINE_ENDING == "\r\n"


@pytest.mark.unit
class TestEncodingConversionCanceled:
    """编码转换取消异常测试"""

    def test_exception_creation(self):
        """测试异常创建"""
        exc = EncodingConversionCanceled("用户取消")
        assert str(exc) == "用户取消"
        assert isinstance(exc, Exception)
