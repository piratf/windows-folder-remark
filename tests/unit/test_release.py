"""release.py 脚本单元测试"""

from unittest.mock import Mock, patch

import pytest

from scripts.release import (
    check_branch,
    check_remote_sync,
    check_working_directory_clean,
    validate_version_increment,
)


class TestValidateVersionIncrement:
    """测试版本号递增验证"""

    def test_patch_increment(self):
        """测试补丁版本递增"""
        assert validate_version_increment("1.0.0", "1.0.1")
        assert validate_version_increment("2.3.4", "2.3.5")

    def test_minor_increment(self):
        """测试次版本递增"""
        assert validate_version_increment("1.0.0", "1.1.0")
        assert validate_version_increment("2.3.4", "2.4.0")

    def test_major_increment(self):
        """测试主版本递增"""
        assert validate_version_increment("1.0.0", "2.0.0")
        assert validate_version_increment("2.3.4", "3.0.0")

    def test_same_version_fails(self):
        """测试相同版本号应失败"""
        assert not validate_version_increment("1.0.0", "1.0.0")

    def test_lower_version_fails(self):
        """测试更低版本号应失败"""
        assert not validate_version_increment("2.0.0", "1.9.9")
        assert not validate_version_increment("1.2.3", "1.2.2")
        assert not validate_version_increment("2.5.0", "2.4.9")


@pytest.mark.parametrize(
    ("status_output", "expected_result"),
    [
        ("", True),  # 无输出表示干净
        ("M file.txt", False),  # 有修改
        ("?? new.txt", False),  # 有新文件
        ("M modified.txt\n?? new.txt", False),  # 多种改动
    ],
)
def test_check_working_directory_clean(status_output, expected_result):
    """测试工作目录状态检查"""
    with patch("subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.stdout = status_output
        mock_run.return_value = mock_result

        result = check_working_directory_clean()
        assert result is expected_result


@pytest.mark.parametrize(
    ("branch_name", "is_main"),
    [
        ("main", True),
        ("master", True),
        ("develop", False),
        ("feat-new-feature", False),
    ],
)
def test_check_branch(branch_name, is_main):
    """测试分支检查"""
    with patch("subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.stdout = branch_name
        mock_run.return_value = mock_result

        result = check_branch()
        assert result == branch_name


@pytest.mark.parametrize(
    ("status_output", "is_synced"),
    [
        ("## main...origin/main", True),
        ("## master...origin/master", True),
        ("## main...origin/main [behind 3]", False),
        ("## main...origin/main [ahead 2]", True),
        ("## main...origin/main [ahead 1, behind 1]", False),
    ],
)
def test_check_remote_sync(status_output, is_synced):
    """测试远程同步检查"""
    with patch("subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.stdout = status_output
        mock_run.return_value = mock_result

        result = check_remote_sync()
        assert result is is_synced


class TestPushCommitInteraction:
    """测试 --push 和 --commit 的联动"""

    def test_push_implies_commit(self, capsys):
        """测试 --push 自动包含 --commit"""
        with (
            patch(
                "sys.argv", ["release.py", "patch", "--push", "--dry-run", "--skip-branch-check"]
            ),
            patch("scripts.release.check_working_directory_clean", return_value=True),
            patch("scripts.release.check_remote_sync", return_value=True),
            patch("scripts.release.get_current_version", return_value="1.0.0"),
            patch("scripts.release.check_branch", return_value="main"),
        ):
            from scripts.release import main

            main()
            captured = capsys.readouterr()
            # 应该包含 "提交版本变更" 因为 --push 自动启用 --commit
            assert "提交版本变更" in captured.out
