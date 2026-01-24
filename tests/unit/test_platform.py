"""平台检测单元测试"""

from unittest.mock import patch

import pytest

from remark.utils.platform import check_platform


@pytest.mark.unit
class TestPlatform:
    """平台检测测试"""

    @pytest.mark.parametrize(
        "system_name,expected",
        [
            ("Windows", True),
            # 注意：check_platform 使用 == "Windows" 比较，是大小写敏感的
            # ("windows", True),   # 小写会失败
            # ("WINDOWS", True),   # 大写会失败
        ],
    )
    def test_check_platform_windows(self, system_name, expected):
        """测试 Windows 平台检测"""
        with patch("remark.utils.platform.platform.system", return_value=system_name):
            result = check_platform()
            assert result is expected

    @pytest.mark.parametrize(
        "system_name",
        ["Linux", "Darwin", "FreeBSD", "SunOS"],
    )
    def test_check_platform_non_windows(self, system_name, capsys):
        """测试非 Windows 平台"""
        with patch("remark.utils.platform.platform.system", return_value=system_name):
            result = check_platform()
            assert result is False
            captured = capsys.readouterr()
            assert "此工具为 Windows 系统" in captured.out

    @pytest.mark.parametrize(
        "system_name",
        ["windows", "WINDOWS", "WiNdOwS"],  # 大小写不匹配
    )
    def test_check_platform_case_sensitive(self, system_name, capsys):
        """测试平台检测大小写敏感"""
        with patch("remark.utils.platform.platform.system", return_value=system_name):
            result = check_platform()
            # 这些会返回 False 因为不等于 "Windows"
            assert result is False
            captured = capsys.readouterr()
            assert "此工具为 Windows 系统" in captured.out
