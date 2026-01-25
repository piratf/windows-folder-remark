"""
右键菜单集成测试

这些测试需要在 Windows 系统上运行，并且会实际操作注册表。
"""

import sys
import winreg

import pytest

from remark.utils import registry

REGISTRY_ROOT = winreg.HKEY_CURRENT_USER
REGISTRY_PATH = r"Software\Classes\Directory\shell\WindowsFolderRemark"


@pytest.mark.windows
@pytest.mark.integration
class TestContextMenu:
    """右键菜单集成测试（仅 Windows）"""

    def setup_method(self):
        """每个测试方法前执行：确保菜单未安装"""
        registry.uninstall_context_menu()

    def teardown_method(self):
        """每个测试方法后执行：清理注册表"""
        registry.uninstall_context_menu()

    def test_install_and_uninstall(self):
        """测试完整的安装和卸载流程"""
        # 1. 安装
        assert registry.install_context_menu() is True

        # 2. 验证注册表键存在
        key = winreg.OpenKey(REGISTRY_ROOT, REGISTRY_PATH)
        assert key is not None
        winreg.CloseKey(key)

        # 3. 验证 command 子键存在
        command_path = f"{REGISTRY_PATH}\\command"
        command_key = winreg.OpenKey(REGISTRY_ROOT, command_path)
        assert command_key is not None
        winreg.CloseKey(command_key)

        # 4. 卸载
        assert registry.uninstall_context_menu() is True

        # 5. 验证注册表键不存在
        with pytest.raises(FileNotFoundError):
            winreg.OpenKey(REGISTRY_ROOT, REGISTRY_PATH)

    def test_install_twice(self):
        """测试重复安装的幂等性"""
        # 第一次安装
        assert registry.install_context_menu() is True

        # 第二次安装应该成功（覆盖）
        assert registry.install_context_menu() is True

    def test_uninstall_not_installed(self):
        """测试卸载未安装的菜单"""
        # 未安装时卸载应该返回 True（幂等）
        assert registry.uninstall_context_menu() is True

    def test_get_executable_path(self):
        """测试获取可执行文件路径"""
        path = registry.get_executable_path()
        assert path is not None
        assert isinstance(path, str)
        # 验证路径是有效的
        import os

        if hasattr(sys, "frozen"):
            # 打包后，路径应该是 exe 文件
            assert os.path.isfile(path)
        else:
            # 开发环境，路径应该是 remark.py
            assert "remark.py" in path
