"""共享测试配置"""

import os
import sys

from pathlib import Path

import pytest

# 项目根目录添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 在导入任何模块之前设置语言环境变量，确保翻译使用中文
os.environ["LANG"] = "zh"


def pytest_configure(config):
    """pytest 配置钩子 - 定义 markers"""
    config.addinivalue_line("markers", "unit: 单元测试（使用 mock）")
    config.addinivalue_line("markers", "integration: 集成测试（真实文件系统）")
    config.addinivalue_line("markers", "windows: 仅在 Windows 上运行")
    config.addinivalue_line("markers", "slow: 慢速测试")

    # 强制使用 UTF-8 编码输出，支持 emoji 等特殊字符
    import io

    if sys.stdout.encoding.lower() not in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding.lower() not in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    # 强制重新初始化翻译器为中文
    from remark.i18n import set_language
    set_language("zh")


def pytest_collection_modifyitems(config, items):
    """自动跳过非 Windows 平台上的 Windows 测试"""
    if sys.platform != "win32":
        skip_windows = pytest.mark.skip(reason="Windows only test")
        for item in items:
            if "windows" in item.keywords:
                item.add_marker(skip_windows)
