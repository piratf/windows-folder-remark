"""完整工作流测试（仅 Windows）"""

import ctypes
import os
import sys

import pytest

from remark.core.folder_handler import FolderCommentHandler
from remark.storage.desktop_ini import DesktopIniHandler


@pytest.mark.windows
@pytest.mark.integration
@pytest.mark.slow
class TestFullWorkflow:
    """完整工作流测试"""

    def test_complete_add_workflow(self, tmp_path):
        """测试完整的添加工作流"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        handler = FolderCommentHandler()
        folder = str(tmp_path / "workflow_test")
        os.makedirs(folder)

        # 1. 设置备注
        result = handler.set_comment(folder, "完整工作流测试")
        assert result is True

        # 2. 验证文件存在
        ini_path = os.path.join(folder, "desktop.ini")
        assert os.path.exists(ini_path)

        # 3. 读取备注
        comment = handler.get_comment(folder)
        assert comment == "完整工作流测试"

        # 4. 验证文件属性（Windows API）
        GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW  # noqa: N806
        FILE_ATTRIBUTE_HIDDEN = 0x02  # noqa: N806
        FILE_ATTRIBUTE_SYSTEM = 0x04  # noqa: N806

        attrs = GetFileAttributesW(ini_path)
        assert attrs != 0xFFFFFFFF
        assert attrs & FILE_ATTRIBUTE_HIDDEN
        assert attrs & FILE_ATTRIBUTE_SYSTEM

    def test_complete_delete_workflow(self, tmp_path):
        """测试完整的删除工作流"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        handler = FolderCommentHandler()
        folder = str(tmp_path / "delete_test")
        os.makedirs(folder)

        # 1. 先添加备注
        handler.set_comment(folder, "待删除的备注")

        # 2. 验证备注存在
        assert handler.get_comment(folder) == "待删除的备注"

        # 3. 删除备注
        result = handler.delete_comment(folder)
        assert result is True

        # 4. 验证备注已删除
        comment = handler.get_comment(folder)
        assert comment is None

    def test_update_existing_comment(self, tmp_path):
        """测试更新已有备注"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        handler = FolderCommentHandler()
        folder = str(tmp_path / "update_test")
        os.makedirs(folder)

        # 1. 设置初始备注
        handler.set_comment(folder, "原始备注")
        assert handler.get_comment(folder) == "原始备注"

        # 2. 更新备注
        result = handler.set_comment(folder, "更新后的备注")
        assert result is True

        # 3. 验证更新
        comment = handler.get_comment(folder)
        assert comment == "更新后的备注"

        # 验证文件只有一个 InfoTip
        ini_path = os.path.join(folder, "desktop.ini")
        with open(ini_path, encoding="utf-16") as f:
            content = f.read()
        # 计算出现次数
        count = content.count("InfoTip=")
        assert count == 1, "应该只有一个 InfoTip 行"

    def test_multiple_folders(self, tmp_path):
        """测试多个文件夹"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        handler = FolderCommentHandler()

        folders = []
        for i in range(5):
            folder = str(tmp_path / f"folder_{i}")
            os.makedirs(folder)
            folders.append(folder)

        # 为所有文件夹设置备注
        for i, folder in enumerate(folders):
            result = handler.set_comment(folder, f"备注 {i}")
            assert result is True

        # 验证所有备注
        for i, folder in enumerate(folders):
            comment = handler.get_comment(folder)
            assert comment == f"备注 {i}"

    def test_preserve_other_settings(self, tmp_path):
        """测试保留其他 desktop.ini 设置"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        import codecs

        folder = str(tmp_path / "preserve_test")
        os.makedirs(folder)

        # 创建包含 IconResource 的 desktop.ini
        ini_path = os.path.join(folder, "desktop.ini")
        content = "[.ShellClassInfo]\r\nIconResource=C:\\icon.ico,0\r\n"
        with codecs.open(ini_path, "w", encoding="utf-16") as f:
            f.write(content)

        # 添加 InfoTip
        handler = FolderCommentHandler()
        handler.set_comment(folder, "备注")

        # 验证 IconResource 仍然存在
        with codecs.open(ini_path, "r", encoding="utf-16") as f:
            new_content = f.read()

        assert "InfoTip=备注" in new_content
        assert "IconResource" in new_content

    def test_empty_comment_removal(self, tmp_path):
        """测试删除备注后保留文件（如果有其他设置）"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        import codecs

        folder = str(tmp_path / "empty_removal")
        os.makedirs(folder)

        # 创建包含 InfoTip 和 IconResource 的文件
        ini_path = os.path.join(folder, "desktop.ini")
        content = "[.ShellClassInfo]\r\nInfoTip=备注\r\nIconResource=C:\\icon.ico,0\r\n"
        with codecs.open(ini_path, "w", encoding="utf-16") as f:
            f.write(content)

        # 删除备注
        handler = FolderCommentHandler()
        handler.delete_comment(folder)

        # 验证文件仍存在（因为有 IconResource）
        assert os.path.exists(ini_path)

        # 验证 InfoTip 已删除
        comment = handler.get_comment(folder)
        assert comment is None

    def test_special_characters_in_comment(self, tmp_path):
        """测试备注中的特殊字符"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        handler = FolderCommentHandler()
        folder = str(tmp_path / "special")
        os.makedirs(folder)

        special_comments = [
            "换行\n测试",  # 包含换行符（会被处理）
            "制表符\t测试",
            '引号 "测试"',
            "单引号 '测试'",
            "反斜杠 \\测试",
            "斜杠 /测试",
        ]

        for comment in special_comments:
            result = handler.set_comment(folder, comment)
            assert result is True

            read_result = handler.get_comment(folder)
            assert read_result == comment

    def test_comment_length_truncation(self, tmp_path):
        """测试备注长度截断"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        from remark.core.folder_handler import MAX_COMMENT_LENGTH

        handler = FolderCommentHandler()
        folder = str(tmp_path / "truncation")
        os.makedirs(folder)

        # 超长备注
        long_comment = "A" * 300
        handler.set_comment(folder, long_comment)

        # 验证被截断
        read_result = handler.get_comment(folder)
        assert len(read_result) == MAX_COMMENT_LENGTH
        assert read_result == "A" * MAX_COMMENT_LENGTH


@pytest.mark.windows
class TestDesktopIniIntegration:
    """desktop.ini 集成测试"""

    def test_write_read_cycle(self, tmp_path):
        """测试写入读取循环"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        folder = str(tmp_path / "cycle")
        os.makedirs(folder)

        test_comments = ["第一次", "第二次", "第三次"]
        for comment in test_comments:
            DesktopIniHandler.write_info_tip(folder, comment)
            read = DesktopIniHandler.read_info_tip(folder)
            assert read == comment

    def test_remove_info_tip(self, tmp_path):
        """测试移除 InfoTip"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        folder = str(tmp_path / "remove")
        os.makedirs(folder)

        # 写入备注
        DesktopIniHandler.write_info_tip(folder, "待移除")
        assert DesktopIniHandler.read_info_tip(folder) == "待移除"

        # 移除备注
        result = DesktopIniHandler.remove_info_tip(folder)
        assert result is True

        # 验证已移除
        assert DesktopIniHandler.read_info_tip(folder) is None

    def test_file_attributes_workflow(self, tmp_path):
        """测试文件属性工作流"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        folder = str(tmp_path / "attributes")
        os.makedirs(folder)

        DesktopIniHandler.write_info_tip(folder, "属性测试")

        ini_path = os.path.join(folder, "desktop.ini")

        # 测试清除属性
        assert DesktopIniHandler.clear_file_attributes(ini_path) is True

        # 测试设置隐藏系统属性
        assert DesktopIniHandler.set_file_hidden_system_attributes(ini_path) is True

        # 验证属性
        GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW  # noqa: N806
        FILE_ATTRIBUTE_HIDDEN = 0x02  # noqa: N806
        FILE_ATTRIBUTE_SYSTEM = 0x04  # noqa: N806

        attrs = GetFileAttributesW(ini_path)
        assert attrs & FILE_ATTRIBUTE_HIDDEN
        assert attrs & FILE_ATTRIBUTE_SYSTEM

    def test_folder_readonly_workflow(self, tmp_path):
        """测试文件夹只读属性工作流"""
        if sys.platform != "win32":
            pytest.skip("Windows only test")

        folder = str(tmp_path / "readonly")
        os.makedirs(folder)

        # 设置只读属性
        result = DesktopIniHandler.set_folder_system_attributes(folder)
        assert result is True

        # 验证只读属性
        FILE_ATTRIBUTE_READONLY = 0x01  # noqa: N806
        GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW  # noqa: N806

        attrs = GetFileAttributesW(folder)
        assert attrs != 0xFFFFFFFF
        assert attrs & FILE_ATTRIBUTE_READONLY

        # 再次设置（应该跳过，已经设置）
        result2 = DesktopIniHandler.set_folder_system_attributes(folder)
        assert result2 is True
