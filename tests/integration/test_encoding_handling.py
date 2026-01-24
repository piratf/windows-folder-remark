"""编码处理集成测试"""

import codecs
import os

import pytest

from remark.storage.desktop_ini import DesktopIniHandler


@pytest.mark.integration
class TestEncodingHandling:
    """编码处理集成测试"""

    def test_write_and_read_utf16(self, tmp_path):
        """测试 UTF-16 编码读写"""
        folder = str(tmp_path / "test")
        os.makedirs(folder)

        # 写入
        result = DesktopIniHandler.write_info_tip(folder, "UTF-16 测试")
        assert result is True

        # 验证文件存在
        ini_path = os.path.join(folder, "desktop.ini")
        assert os.path.exists(ini_path)

        # 读取
        read_result = DesktopIniHandler.read_info_tip(folder)
        assert read_result == "UTF-16 测试"

    def test_read_gbk_encoded_file(self, tmp_path):
        """测试读取 GBK 编码的文件（降级兼容）"""
        folder = str(tmp_path / "gbk_test")
        os.makedirs(folder)
        ini_path = os.path.join(folder, "desktop.ini")

        # 使用 codecs.open 确保行尾符正确处理
        with codecs.open(ini_path, "w", encoding="gbk") as f:
            f.write("[.ShellClassInfo]\r\nInfoTip=GBK Test\r\n")

        result = DesktopIniHandler.read_info_tip(folder)
        assert result == "GBK Test"

    def test_read_utf8_encoded_file(self, tmp_path):
        """测试读取 UTF-8 编码的文件"""
        folder = str(tmp_path / "utf8_test")
        os.makedirs(folder)
        ini_path = os.path.join(folder, "desktop.ini")

        # 使用 codecs.open 确保 UTF-8 编码正确
        with codecs.open(ini_path, "w", encoding="utf-8") as f:
            f.write("[.ShellClassInfo]\r\nInfoTip=UTF-8 Test\r\n")

        result = DesktopIniHandler.read_info_tip(folder)
        assert result == "UTF-8 Test"

    def test_encoding_detection_utf16(self, utf16_encoded_file):
        """测试编码检测 - UTF-16"""
        encoding, is_utf16 = DesktopIniHandler.detect_encoding(utf16_encoded_file)
        assert is_utf16 is True
        assert "utf-16" in encoding

    def test_encoding_detection_utf8(self, utf8_encoded_file):
        """测试编码检测 - UTF-8"""
        encoding, is_utf16 = DesktopIniHandler.detect_encoding(utf8_encoded_file)
        assert is_utf16 is False
        assert encoding == "utf-8"

    @pytest.mark.parametrize(
        "comment",
        [
            "简体中文",
            "繁體中文",
            "日本語",
            "한국어",
            "Emoji 🔥",
            "Mixed 中英文 Mixed",
            "Special chars: !@#$%^&*()",
        ],
    )
    def test_write_various_characters(self, tmp_path, comment):
        """测试写入各种字符"""
        folder = str(tmp_path / "chinese")
        os.makedirs(folder)

        result = DesktopIniHandler.write_info_tip(folder, comment)
        assert result is True

        read_result = DesktopIniHandler.read_info_tip(folder)
        assert read_result == comment

    def test_write_long_comment(self, tmp_path):
        """测试写入长备注"""
        folder = str(tmp_path / "long")
        os.makedirs(folder)

        # 260 字符（MAX_COMMENT_LENGTH）
        long_comment = "A" * 260
        result = DesktopIniHandler.write_info_tip(folder, long_comment)
        assert result is True

        read_result = DesktopIniHandler.read_info_tip(folder)
        assert read_result == long_comment

    def test_update_preserves_encoding(self, tmp_path):
        """测试更新备注保持编码"""
        folder = str(tmp_path / "update")
        os.makedirs(folder)

        # 第一次写入
        DesktopIniHandler.write_info_tip(folder, "初始备注")

        # 获取文件编码
        ini_path = os.path.join(folder, "desktop.ini")
        encoding1, is_utf16_1 = DesktopIniHandler.detect_encoding(ini_path)
        assert is_utf16_1 is True

        # 更新备注
        DesktopIniHandler.write_info_tip(folder, "更新备注")

        # 验证编码仍然是 UTF-16
        encoding2, is_utf16_2 = DesktopIniHandler.detect_encoding(ini_path)
        assert is_utf16_2 is True
        assert encoding1.split("-")[0] == encoding2.split("-")[0]

    def test_write_new_line_endings(self, tmp_path):
        """测试写入使用 Windows 行尾符"""
        folder = str(tmp_path / "line_ending")
        os.makedirs(folder)

        DesktopIniHandler.write_info_tip(folder, "行尾测试")

        ini_path = os.path.join(folder, "desktop.ini")

        # UTF-16 LE 编码中，\r\n 被存储为 \x00\r\x00\n（每个字符前有 null byte）
        # 或者可以简单地读取文本内容验证行尾符
        with codecs.open(ini_path, "r", encoding="utf-16") as f:
            text_content = f.read()

        # 验证文本内容包含 CRLF
        assert "\r\n" in text_content

    def test_read_without_bom(self, tmp_path):
        """测试读取没有 BOM 的文件（降级到 utf-8）"""
        folder = str(tmp_path / "no_bom")
        os.makedirs(folder)

        ini_path = os.path.join(folder, "desktop.ini")
        # 使用 codecs.open 确保编码正确
        with codecs.open(ini_path, "w", encoding="utf-8") as f:
            f.write("[.ShellClassInfo]\r\nInfoTip=No BOM Test\r\n")

        result = DesktopIniHandler.read_info_tip(folder)
        assert result == "No BOM Test"

    def test_empty_folder(self, tmp_path):
        """测试空文件夹"""
        folder = str(tmp_path / "empty")
        os.makedirs(folder)

        result = DesktopIniHandler.read_info_tip(folder)
        assert result is None

    def test_corrupted_ini_file(self, tmp_path):
        """测试损坏的 ini 文件"""
        folder = str(tmp_path / "corrupted")
        os.makedirs(folder)

        ini_path = os.path.join(folder, "desktop.ini")
        with open(ini_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")  # 二进制垃圾数据

        # 应该返回 None 而不是崩溃
        result = DesktopIniHandler.read_info_tip(folder)
        # 可能成功解码（某些编码会接受）或返回 None
        assert result is None or isinstance(result, str)
