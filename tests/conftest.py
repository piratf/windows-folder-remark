"""共享测试配置"""

import sys
from pathlib import Path

import pytest

# 项目根目录添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config):
    """pytest 配置钩子 - 定义 markers"""
    config.addinivalue_line("markers", "unit: 单元测试（使用 mock）")
    config.addinivalue_line("markers", "integration: 集成测试（真实文件系统）")
    config.addinivalue_line("markers", "windows: 仅在 Windows 上运行")
    config.addinivalue_line("markers", "slow: 慢速测试")


def pytest_collection_modifyitems(config, items):
    """自动跳过非 Windows 平台上的 Windows 测试"""
    if sys.platform != "win32":
        skip_windows = pytest.mark.skip(reason="Windows only test")
        for item in items:
            if "windows" in item.keywords:
                item.add_marker(skip_windows)
