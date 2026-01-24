"""核心业务逻辑单元测试"""

from unittest.mock import patch

import pytest

from remark.core.folder_handler import MAX_COMMENT_LENGTH, FolderCommentHandler


@pytest.mark.unit
class TestFolderCommentHandler:
    """文件夹备注处理器测试"""

    def test_init(self):
        """测试初始化"""
        handler = FolderCommentHandler()
        assert handler is not None

    @pytest.mark.parametrize(
        "is_dir,expected",
        [(True, True), (False, False)],
    )
    def test_supports(self, is_dir, expected):
        """测试支持检测"""
        with patch("os.path.isdir", return_value=is_dir):
            handler = FolderCommentHandler()
            result = handler.supports("/folder")
            assert result is expected

    def test_set_comment_not_folder(self, capsys):
        """测试对非文件夹路径设置备注"""
        with patch("os.path.isdir", return_value=False):
            handler = FolderCommentHandler()
            result = handler.set_comment("/file.txt", "备注")
            assert result is False
            captured = capsys.readouterr()
            assert "不是文件夹" in captured.out

    def test_set_comment_too_long(self, capsys):
        """测试备注长度超过限制"""
        with (
            patch("os.path.isdir", return_value=True),
            patch.object(
                FolderCommentHandler, "_set_comment_desktop_ini", return_value=True
            ) as mock_set,
        ):
            handler = FolderCommentHandler()
            long_comment = "A" * 300  # 超过 MAX_COMMENT_LENGTH

            handler.set_comment("/folder", long_comment)

            # 应该被截断到 MAX_COMMENT_LENGTH
            mock_set.assert_called_once()
            args = mock_set.call_args[0]
            assert len(args[1]) == MAX_COMMENT_LENGTH
            assert args[1] == "A" * MAX_COMMENT_LENGTH

    def test_set_comment_success(self):
        """测试成功设置备注"""
        with (
            patch("os.path.isdir", return_value=True),
            patch.object(FolderCommentHandler, "_set_comment_desktop_ini", return_value=True),
        ):
            handler = FolderCommentHandler()
            result = handler.set_comment("/folder", "测试备注")
            assert result is True

    @pytest.mark.parametrize(
        "read_return,expected",
        [
            ("测试备注", "测试备注"),
            ("English Comment", "English Comment"),
            (None, None),
        ],
    )
    def test_get_comment(self, read_return, expected):
        """测试获取备注"""
        with patch(
            "remark.storage.desktop_ini.DesktopIniHandler.read_info_tip",
            return_value=read_return,
        ):
            handler = FolderCommentHandler()
            result = handler.get_comment("/folder")
            assert result == expected

    def test_delete_comment_no_ini(self, capsys):
        """测试删除不存在的备注"""
        with patch("remark.storage.desktop_ini.DesktopIniHandler.exists", return_value=False):
            handler = FolderCommentHandler()
            result = handler.delete_comment("/folder")
            assert result is True
            captured = capsys.readouterr()
            assert "没有备注" in captured.out

    def test_delete_comment_with_ini(self):
        """测试删除存在的备注"""
        with (
            patch("remark.storage.desktop_ini.DesktopIniHandler.exists", return_value=True),
            patch(
                "remark.storage.desktop_ini.DesktopIniHandler.clear_file_attributes",
                return_value=True,
            ),
            patch(
                "remark.storage.desktop_ini.DesktopIniHandler.remove_info_tip",
                return_value=True,
            ),
        ):
            handler = FolderCommentHandler()
            result = handler.delete_comment("/folder")
            assert result is True

    def test_delete_comment_clear_failure(self):
        """测试删除时清除属性失败"""
        with (
            patch("remark.storage.desktop_ini.DesktopIniHandler.exists", return_value=True),
            patch(
                "remark.storage.desktop_ini.DesktopIniHandler.clear_file_attributes",
                return_value=False,
            ),
        ):
            handler = FolderCommentHandler()
            result = handler.delete_comment("/folder")
            assert result is False

    def test_set_comment_desktop_ini(self):
        """测试 desktop.ini 设置备注的内部方法"""
        with (
            patch(
                "remark.storage.desktop_ini.DesktopIniHandler.write_info_tip",
                return_value=True,
            ),
            patch(
                "remark.storage.desktop_ini.DesktopIniHandler.clear_file_attributes",
                return_value=True,
            ),
            patch(
                "remark.storage.desktop_ini.DesktopIniHandler.set_file_hidden_system_attributes",
                return_value=True,
            ),
            patch(
                "remark.storage.desktop_ini.DesktopIniHandler.set_folder_system_attributes",
                return_value=True,
            ),
        ):
            handler = FolderCommentHandler()
            result = handler._set_comment_desktop_ini("/folder", "备注")
            assert result is True

    def test_max_comment_length_constant(self):
        """测试最大备注长度常量"""
        assert MAX_COMMENT_LENGTH == 260
