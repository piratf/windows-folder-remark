"""CLI 命令单元测试"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from remark.cli.commands import CLI, get_version


@pytest.mark.unit
class TestCLI:
    """CLI 命令测试"""

    def test_init(self):
        """测试 CLI 初始化"""
        cli = CLI()
        assert cli.handler is not None

    def test_validate_folder_not_exists(self, capsys):
        """测试验证不存在的路径"""
        with patch("os.path.exists", return_value=False):
            cli = CLI()
            result = cli._validate_folder("/invalid/path")
            assert result is False
            captured = capsys.readouterr()
            assert "路径不存在" in captured.out

    def test_validate_folder_not_dir(self, capsys):
        """测试验证非文件夹路径"""
        with patch("os.path.exists", return_value=True), patch(
            "os.path.isdir", return_value=False
        ):
            cli = CLI()
            result = cli._validate_folder("/file.txt")
            assert result is False
            captured = capsys.readouterr()
            assert "不是文件夹" in captured.out

    def test_validate_folder_success(self):
        """测试验证有效文件夹"""
        with patch("os.path.exists", return_value=True), patch(
            "os.path.isdir", return_value=True
        ):
            cli = CLI()
            result = cli._validate_folder("/valid/folder")
            assert result is True

    def test_add_comment_success(self):
        """测试添加备注成功"""
        with patch("os.path.exists", return_value=True), patch("os.path.isdir", return_value=True), patch("remark.core.folder_handler.FolderCommentHandler.set_comment", return_value=True):
            cli = CLI()
            result = cli.add_comment("/test/folder", "测试备注")
            assert result is True

    def test_add_comment_invalid_folder(self):
        """测试添加备注到无效路径"""
        with patch("os.path.exists", return_value=False):
            cli = CLI()
            result = cli.add_comment("/invalid/path", "备注")
            assert result is False

    def test_delete_comment_success(self):
        """测试删除备注成功"""
        with patch("os.path.exists", return_value=True), patch("os.path.isdir", return_value=True), patch("remark.core.folder_handler.FolderCommentHandler.delete_comment", return_value=True):
            cli = CLI()
            result = cli.delete_comment("/test/folder")
            assert result is True

    def test_delete_comment_invalid_folder(self):
        """测试删除备注失败（无效路径）"""
        with patch("os.path.exists", return_value=False):
            cli = CLI()
            result = cli.delete_comment("/invalid/path")
            assert result is False

    def test_view_comment_with_content(self, capsys):
        """测试查看有备注的文件夹"""
        with patch("os.path.exists", return_value=True), patch("os.path.isdir", return_value=True), patch("remark.core.folder_handler.FolderCommentHandler.get_comment", return_value="测试备注"):
            cli = CLI()
            cli.view_comment("/test/folder")
            captured = capsys.readouterr()
            assert "测试备注" in captured.out

    def test_view_comment_without_content(self, capsys):
        """测试查看无备注的文件夹"""
        with patch("os.path.exists", return_value=True), patch("os.path.isdir", return_value=True), patch("remark.core.folder_handler.FolderCommentHandler.get_comment", return_value=None):
            cli = CLI()
            cli.view_comment("/test/folder")
            captured = capsys.readouterr()
            assert "没有备注" in captured.out

    @pytest.mark.parametrize(
        "inputs,expected_add_calls",
        [
            # 有效输入
            (["/folder", "备注", KeyboardInterrupt()], 1),
            # 第一次路径无效，第二次有效
            (["/invalid", "/folder", "备注", KeyboardInterrupt()], 1),
            # 第一次备注重试，第二次有效
            (["/folder", "", "有效备注", KeyboardInterrupt()], 1),
        ],
    )
    def test_interactive_mode_scenarios(self, inputs, expected_add_calls):
        """测试交互模式各种场景"""
        with patch("builtins.input", side_effect=inputs), patch(
            "os.path.exists", return_value=True
        ), patch("os.path.isdir", return_value=True), patch.object(
            CLI, "add_comment"
        ) as mock_add:
            cli = CLI()
            cli.interactive_mode()
            assert mock_add.call_count == expected_add_calls

    def test_show_help(self, capsys):
        """测试帮助信息"""
        cli = CLI()
        cli.show_help()
        captured = capsys.readouterr()
        assert "Windows 文件夹备注工具" in captured.out
        assert "使用方法" in captured.out
        assert "交互模式" in captured.out

    def test_run_with_help(self, capsys):
        """测试运行 --help 参数"""
        with patch("remark.cli.commands.check_platform", return_value=True):
            cli = CLI()
            cli.run(["--help"])
            captured = capsys.readouterr()
            assert "Windows 文件夹备注工具" in captured.out

    def test_run_with_delete(self):
        """测试运行 --delete 参数"""
        with patch("remark.cli.commands.check_platform", return_value=True), patch.object(
            CLI, "delete_comment"
        ) as mock_delete:
            cli = CLI()
            cli.run(["--delete", "/test/folder"])
            mock_delete.assert_called_once_with("/test/folder")

    def test_run_with_view(self):
        """测试运行 --view 参数"""
        with patch("remark.cli.commands.check_platform", return_value=True), patch.object(
            CLI, "view_comment"
        ) as mock_view:
            cli = CLI()
            cli.run(["--view", "/test/folder"])
            mock_view.assert_called_once_with("/test/folder")

    def test_run_with_path_and_comment(self):
        """测试运行带路径和备注参数"""
        with patch("remark.cli.commands.check_platform", return_value=True), patch.object(
            CLI, "add_comment"
        ) as mock_add:
            cli = CLI()
            cli.run(["/folder", "备注"])
            mock_add.assert_called_once_with("/folder", "备注")

    def test_run_interactive_mode(self):
        """测试运行进入交互模式"""
        with patch("remark.cli.commands.check_platform", return_value=True), patch.object(
            CLI, "interactive_mode"
        ) as mock_interactive:
            cli = CLI()
            cli.run([])
            mock_interactive.assert_called_once()

    def test_run_platform_check_fail(self):
        """测试非 Windows 平台"""
        # check_platform 在 CLI.run 开始时被调用，如果返回 False 会 sys.exit(1)
        # 由于 sys.exit 会抛出 SystemExit，我们需要捕获它或 mock 它
        with patch("remark.cli.commands.check_platform", return_value=False):
            cli = CLI()
            with pytest.raises(SystemExit) as exc_info:
                cli.run([])
            # sys.exit(1) 会被调用
            assert exc_info.value.code == 1


@pytest.mark.unit
class TestGetVersion:
    """get_version 函数测试"""

    def test_get_version_from_package(self):
        """测试从包获取版本"""
        with patch("importlib.metadata.version", return_value="2.0.0"):
            version = get_version()
            assert version == "2.0.0"

    def test_get_version_fallback(self):
        """测试获取版本失败时返回 unknown"""
        with patch("importlib.metadata.version", side_effect=Exception()):
            version = get_version()
            assert version == "unknown"
