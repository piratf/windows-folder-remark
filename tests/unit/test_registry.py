"""
注册表操作单元测试
"""

from unittest.mock import MagicMock, patch

import pytest

from remark.utils import registry


@pytest.mark.unit
class TestRegistry:
    """注册表操作测试"""

    @patch("remark.utils.registry.sys")
    def test_get_executable_path_frozen(self, mock_sys):
        """测试获取打包后的 exe 路径"""
        mock_sys.frozen = True
        mock_sys.executable = r"C:\Program Files\windows-folder-remark.exe"

        result = registry.get_executable_path()

        assert result == r"C:\Program Files\windows-folder-remark.exe"

    @patch("remark.utils.registry.sys")
    @patch("remark.utils.registry.os.path")
    def test_get_executable_path_dev(self, mock_path, mock_sys):
        """测试获取开发环境的脚本路径"""
        mock_sys.frozen = False
        mock_path.abspath.side_effect = lambda x: x.replace("..", "abs")
        mock_path.dirname.side_effect = lambda x: x.replace("registry.py", "").replace(
            "utils\\", ""
        )
        mock_path.join.return_value = "remark.py"

        with patch("remark.utils.registry.__file__", "remark/utils/registry.py"):
            result = registry.get_executable_path()

        assert result == "remark.py"

    @patch("remark.utils.registry.winreg")
    @patch("remark.utils.registry.get_executable_path")
    def test_install_context_menu_success(self, mock_get_exe, mock_winreg):
        """测试成功安装右键菜单"""
        mock_get_exe.return_value = r"C:\test.exe"
        mock_key = MagicMock()
        mock_winreg.CreateKey.return_value = mock_key

        result = registry.install_context_menu()

        assert result is True
        # 验证注册表键被创建
        assert mock_winreg.CreateKey.call_count == 2
        # 验证 SetValueEx 被调用（设置默认值和图标）
        assert mock_winreg.SetValueEx.call_count == 3

    @patch("remark.utils.registry.winreg")
    def test_install_context_menu_permission_error(self, mock_winreg):
        """测试权限不足时的安装"""
        mock_winreg.CreateKey.side_effect = PermissionError()

        result = registry.install_context_menu()

        assert result is False

    @patch("remark.utils.registry.winreg")
    @patch("remark.utils.registry.get_executable_path")
    def test_uninstall_context_menu_success(self, mock_get_exe, mock_winreg):
        """测试成功卸载右键菜单"""
        mock_get_exe.return_value = r"C:\test.exe"

        result = registry.uninstall_context_menu()

        assert result is True
        # 验证 DeleteKey 被调用两次（command 和主键）
        assert mock_winreg.DeleteKey.call_count == 2

    @patch("remark.utils.registry.winreg")
    def test_uninstall_context_menu_not_installed(self, mock_winreg):
        """测试卸载未安装的菜单（键不存在）"""
        mock_winreg.DeleteKey.side_effect = FileNotFoundError()

        result = registry.uninstall_context_menu()

        assert result is True

    @patch("remark.utils.registry.winreg")
    def test_uninstall_context_menu_permission_error(self, mock_winreg):
        """测试权限不足时的卸载"""
        mock_winreg.DeleteKey.side_effect = PermissionError()

        result = registry.uninstall_context_menu()

        assert result is False
