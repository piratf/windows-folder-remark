"""CLI 命令单元测试"""

import os

import pytest

from remark.cli.commands import CLI, get_version


@pytest.mark.unit
class TestCLI:
    """CLI 命令测试"""

    @pytest.fixture(autouse=True)
    def disable_background_update_check(self, monkeypatch):
        """禁用后台更新检查，避免 pyfakefs 隔离被后台线程破坏"""
        monkeypatch.setattr(
            "remark.cli.commands.CLI._check_update_in_background",
            lambda self: None,
        )

    def test_init(self):
        """测试 CLI 初始化"""
        cli = CLI()
        assert cli.handler is not None

    def test_validate_folder_not_exists(self, capsys):
        """测试验证不存在的路径"""
        cli = CLI()
        result = cli._validate_folder("/invalid/path")
        assert result is False
        captured = capsys.readouterr()
        assert "路径不存在" in captured.out

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_validate_folder_not_dir(self, fs, capsys):
        """测试验证非文件夹路径"""
        fs.create_file("/file.txt")
        cli = CLI()
        result = cli._validate_folder("/file.txt")
        assert result is False
        captured = capsys.readouterr()
        assert "不是文件夹" in captured.out

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_validate_folder_success(self, fs):
        """测试验证有效文件夹"""
        fs.create_dir("/valid/folder")
        cli = CLI()
        result = cli._validate_folder("/valid/folder")
        assert result is True

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_add_comment_success(self, fs):
        """测试添加备注成功"""
        fs.create_dir("/test/folder")
        cli = CLI()
        result = cli.add_comment("/test/folder", "测试备注")
        assert result is True

    def test_add_comment_invalid_folder(self):
        """测试添加备注到无效路径"""
        cli = CLI()
        result = cli.add_comment("/invalid/path", "备注")
        assert result is False

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_delete_comment_success(self, fs):
        """测试删除备注成功"""
        fs.create_dir("/test/folder")
        cli = CLI()
        result = cli.delete_comment("/test/folder")
        assert result is True

    def test_delete_comment_invalid_folder(self):
        """测试删除备注失败（无效路径）"""
        cli = CLI()
        result = cli.delete_comment("/invalid/path")
        assert result is False

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_view_comment_with_content(self, fs, capsys):
        """测试查看有备注的文件夹"""
        fs.create_dir("/test/folder")
        from remark.core.folder_handler import FolderCommentHandler

        with pytest.MonkeyPatch().context() as m:
            m.setattr(FolderCommentHandler, "get_comment", lambda self, path: "测试备注")
            cli = CLI()
            cli.view_comment("/test/folder")
            captured = capsys.readouterr()
            assert "测试备注" in captured.out

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_view_comment_without_content(self, fs, capsys):
        """测试查看无备注的文件夹"""
        fs.create_dir("/test/folder")
        from remark.core.folder_handler import FolderCommentHandler

        with pytest.MonkeyPatch().context() as m:
            m.setattr(FolderCommentHandler, "get_comment", lambda self, path: None)
            cli = CLI()
            cli.view_comment("/test/folder")
            captured = capsys.readouterr()
            assert "没有备注" in captured.out

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_view_comment_with_encoding_issue_and_fix(self, fs, capsys):
        """测试查看有编码问题的文件夹并选择修复"""
        from remark.core.folder_handler import FolderCommentHandler
        from remark.storage.desktop_ini import DesktopIniHandler

        fs.create_dir("/test/folder")
        fs.create_file("/test/folder/desktop.ini", contents="test content")

        with pytest.MonkeyPatch().context() as m:
            m.setattr(DesktopIniHandler, "detect_encoding", lambda file_path: ("utf-8", False))
            m.setattr(DesktopIniHandler, "fix_encoding", lambda file_path, current_encoding: True)
            m.setattr(FolderCommentHandler, "get_comment", lambda self, path: "测试备注")
            m.setattr("builtins.input", lambda *args, **kwargs: "y")

            cli = CLI()
            cli.view_comment("/test/folder")
            captured = capsys.readouterr()
            assert "编码为 utf-8" in captured.out
            assert "已修复为 UTF-16 编码" in captured.out
            assert "测试备注" in captured.out

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_view_comment_with_encoding_issue_and_skip(self, fs, capsys):
        """测试查看有编码问题的文件夹但选择跳过修复"""
        from remark.core.folder_handler import FolderCommentHandler
        from remark.storage.desktop_ini import DesktopIniHandler

        fs.create_dir("/test/folder")
        fs.create_file("/test/folder/desktop.ini", contents="test content")

        with pytest.MonkeyPatch().context() as m:
            m.setattr(DesktopIniHandler, "detect_encoding", lambda file_path: ("gbk", False))
            m.setattr(FolderCommentHandler, "get_comment", lambda self, path: "测试备注")
            m.setattr("builtins.input", lambda *args, **kwargs: "n")

            cli = CLI()
            cli.view_comment("/test/folder")
            captured = capsys.readouterr()
            assert "编码为 gbk" in captured.out
            assert "跳过编码修复" in captured.out
            assert "测试备注" in captured.out

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_view_comment_with_correct_encoding(self, fs, capsys):
        """测试查看编码正确的文件夹"""
        from remark.core.folder_handler import FolderCommentHandler
        from remark.storage.desktop_ini import DesktopIniHandler

        fs.create_dir("/test/folder")
        fs.create_file("/test/folder/desktop.ini", contents="test content")

        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                DesktopIniHandler,
                "detect_encoding",
                lambda file_path: ("utf-16-le", True),
            )
            m.setattr(FolderCommentHandler, "get_comment", lambda self, path: "测试备注")

            cli = CLI()
            cli.view_comment("/test/folder")
            captured = capsys.readouterr()
            # 不应该显示编码警告
            assert "编码" not in captured.out
            assert "测试备注" in captured.out

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_interactive_mode_valid_input(self, fs, monkeypatch):
        """测试交互模式有效输入"""
        fs.create_dir("/folder")

        input_sequence = ["/folder", "测试备注"]

        def mock_input(prompt):
            if input_sequence:
                return input_sequence.pop(0)
            raise KeyboardInterrupt()

        cli = CLI()

        # Mock input to control user input and exit after first iteration
        monkeypatch.setattr("builtins.input", mock_input)

        # Mock add_comment to verify it was called
        original_add_comment = cli.add_comment
        calls = []

        def mock_add_comment(path, comment):
            calls.append((path, comment))
            return original_add_comment(path, comment)

        monkeypatch.setattr(cli, "add_comment", mock_add_comment)

        cli.interactive_mode()

        # 验证 add_comment 被正确调用
        assert len(calls) == 1
        assert calls[0] == ("/folder", "测试备注")

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_interactive_mode_invalid_path_then_valid(self, fs, monkeypatch, capsys):
        """测试交互模式先输入无效路径再输入有效路径"""
        fs.create_dir("/valid_folder")

        input_sequence = ["/invalid", "/valid_folder", "备注内容"]

        def mock_input(prompt):
            if input_sequence:
                return input_sequence.pop(0)
            raise KeyboardInterrupt()

        cli = CLI()
        monkeypatch.setattr("builtins.input", mock_input)

        # Mock add_comment to verify it was called
        original_add_comment = cli.add_comment
        calls = []

        def mock_add_comment(path, comment):
            calls.append((path, comment))
            return original_add_comment(path, comment)

        monkeypatch.setattr(cli, "add_comment", mock_add_comment)

        cli.interactive_mode()

        # 验证无效路径被提示，最终有效路径被处理
        captured = capsys.readouterr()
        assert "路径不存在" in captured.out
        assert len(calls) == 1
        assert calls[0] == ("/valid_folder", "备注内容")

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_interactive_mode_empty_comment_retry(self, fs, monkeypatch, capsys):
        """测试交互模式空备注重试"""
        fs.create_dir("/folder")

        input_sequence = ["/folder", "", "有效备注"]

        def mock_input(prompt):
            if input_sequence:
                return input_sequence.pop(0)
            raise KeyboardInterrupt()

        cli = CLI()
        monkeypatch.setattr("builtins.input", mock_input)

        # Mock add_comment to verify it was called
        original_add_comment = cli.add_comment
        calls = []

        def mock_add_comment(path, comment):
            calls.append((path, comment))
            return original_add_comment(path, comment)

        monkeypatch.setattr(cli, "add_comment", mock_add_comment)

        cli.interactive_mode()

        # 验证空备注被提示重新输入，最终有效备注被处理
        captured = capsys.readouterr()
        assert "备注不要为空" in captured.out
        assert len(calls) == 1
        assert calls[0] == ("/folder", "有效备注")

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
        cli = CLI()
        cli.run(["--help"])
        captured = capsys.readouterr()
        assert "Windows 文件夹备注工具" in captured.out

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_run_with_delete(self, fs):
        """测试运行 --delete 参数"""
        fs.create_dir("/test/folder")
        cli = CLI()
        cli.run(["--delete", "/test/folder"])

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_run_with_view(self, fs):
        """测试运行 --view 参数"""
        fs.create_dir("/test/folder")
        cli = CLI()
        cli.run(["--view", "/test/folder"])

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_run_with_path_and_comment(self, fs, monkeypatch):
        """测试运行带路径和备注参数"""
        fs.create_dir("/folder")
        # Mock input to auto-confirm when path is detected
        monkeypatch.setattr("builtins.input", lambda *args, **kwargs: "y")
        cli = CLI()
        cli.run(["/folder", "备注"])

    def test_run_interactive_mode(self, monkeypatch):
        """测试运行进入交互模式"""
        # Mock interactive_mode to avoid actually entering interactive mode
        monkeypatch.setattr(CLI, "interactive_mode", lambda cli: None)
        cli = CLI()
        cli.run([])

    def test_run_platform_check_fail(self):
        """测试非 Windows 平台"""
        # check_platform 在 CLI.run 开始时被调用，如果返回 False 会 sys.exit(1)
        # 由于 sys.exit 会抛出 SystemExit，我们需要捕获它或 mock 它
        with pytest.MonkeyPatch().context() as m:
            m.setattr("remark.cli.commands.check_platform", lambda: False)
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
        with pytest.MonkeyPatch().context() as m:
            m.setattr("importlib.metadata.version", lambda *args, **kwargs: "2.0.0")
            version = get_version()
            assert version == "2.0.0"

    def test_get_version_fallback(self):
        """测试获取版本失败时返回 unknown"""
        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                "importlib.metadata.version",
                lambda *args, **kwargs: (_ for _ in ()).throw(Exception()),
            )
            version = get_version()
            assert version == "unknown"
