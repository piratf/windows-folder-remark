"""updater.py 单元测试"""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from remark.utils.constants import UPDATE_CACHE_FILE, UPDATE_CHECK_INTERVAL
from remark.utils.updater import (
    _create_opener,
    _get_cache_file_path,
    _get_proxies,
    check_updates_auto,
    check_updates_manual,
    create_update_script,
    download_update,
    get_executable_path,
    get_latest_release,
    should_check_update,
    trigger_update,
    update_next_check_time,
)


@pytest.mark.unit
class TestProxyFunctions:
    """测试代理相关函数"""

    def test_get_proxies_no_env(self, monkeypatch):
        """无环境变量时返回 None"""
        for key in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"]:
            monkeypatch.delenv(key, raising=False)

        result = _get_proxies()
        assert result is None

    def test_get_proxies_http_only(self, monkeypatch):
        """仅 HTTP_PROXY 时返回 http"""
        for key in ["http_proxy", "HTTPS_PROXY", "https_proxy"]:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.com:8080")

        result = _get_proxies()
        assert result == {"http": "http://proxy.example.com:8080"}

    def test_get_proxies_http_lowercase(self, monkeypatch):
        """小写 http_proxy 也能识别"""
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "https_proxy"]:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("http_proxy", "http://proxy.example.com:8080")

        result = _get_proxies()
        assert result == {"http": "http://proxy.example.com:8080"}

    def test_get_proxies_https_only(self, monkeypatch):
        """仅 HTTPS_PROXY 时返回 https"""
        for key in ["HTTP_PROXY", "http_proxy", "https_proxy"]:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("HTTPS_PROXY", "https://proxy.example.com:8443")

        result = _get_proxies()
        assert result == {"https": "https://proxy.example.com:8443"}

    def test_get_proxies_both(self, monkeypatch):
        """两者都有时返回两者"""
        for key in ["http_proxy", "https_proxy"]:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.com:8080")
        monkeypatch.setenv("HTTPS_PROXY", "https://proxy.example.com:8443")

        result = _get_proxies()
        assert result == {
            "http": "http://proxy.example.com:8080",
            "https": "https://proxy.example.com:8443",
        }

    def test_create_opener_no_proxy(self, monkeypatch):
        """无代理时创建默认 opener"""
        for key in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"]:
            monkeypatch.delenv(key, raising=False)

        opener = _create_opener()
        assert opener is not None

    def test_create_opener_with_proxy(self, monkeypatch):
        """有代理时创建带 ProxyHandler 的 opener"""
        for key in ["http_proxy", "HTTPS_PROXY", "https_proxy"]:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.com:8080")

        opener = _create_opener()
        assert opener is not None


@pytest.mark.unit
class TestCacheFilePath:
    """测试缓存文件路径获取"""

    def test_get_cache_file_path(self):
        """返回临时目录下的缓存文件路径"""
        result = _get_cache_file_path()
        expected = os.path.join(tempfile.gettempdir(), UPDATE_CACHE_FILE)
        assert result == expected


@pytest.mark.unit
class TestExecutablePath:
    """测试可执行文件路径获取"""

    def test_get_executable_path_frozen(self, monkeypatch):
        """frozen 状态下返回 sys.executable"""
        monkeypatch.setattr("sys.frozen", True, raising=False)
        monkeypatch.setattr("sys.executable", "/path/to/app.exe")

        result = get_executable_path()
        assert result == "/path/to/app.exe"

    def test_get_executable_path_not_frozen(self, monkeypatch):
        """非 frozen 状态下返回 __file__ 路径"""
        monkeypatch.delattr("sys", "frozen", raising=False)
        # 在实际测试中，__file__ 会是实际路径，所以我们不 mock 它
        # 只验证在 frozen=False 时的行为
        result = get_executable_path()
        # 结果应该是 remark/utils/updater.py 的路径
        assert result.endswith("updater.py")


@pytest.mark.unit
class TestGitHubAPI:
    """测试 GitHub API 相关函数"""

    def test_get_latest_release_success(self):
        """成功获取最新 release"""
        mock_data = {
            "tag_name": "v2.0.3",
            "html_url": "https://github.com/piratf/windows-folder-remark/releases/tag/v2.0.3",
            "body": "New release",
            "prerelease": False,
            "draft": False,
            "assets": [
                {
                    "name": "windows-folder-remark-2.0.3.exe",
                    "browser_download_url": "https://github.com/.../exe",
                }
            ],
        }

        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with (
            patch("urllib.request.OpenerDirector.open", return_value=mock_response),
            patch("json.load", return_value=mock_data),
        ):
            result = get_latest_release()

        assert result is not None
        assert result["tag_name"] == "2.0.3"
        assert (
            result["html_url"]
            == "https://github.com/piratf/windows-folder-remark/releases/tag/v2.0.3"
        )
        assert result["body"] == "New release"

    def test_get_latest_release_prerelease_filtered(self):
        """过滤掉 prerelease 版本"""
        mock_data = {
            "tag_name": "v2.1.0-beta",
            "prerelease": True,
            "draft": False,
            "assets": [
                {
                    "name": "windows-folder-remark-2.1.0-beta.exe",
                    "browser_download_url": "https://github.com/.../exe",
                }
            ],
        }

        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with (
            patch("urllib.request.OpenerDirector.open", return_value=mock_response),
            patch("json.load", return_value=mock_data),
        ):
            result = get_latest_release()

        assert result is None

    def test_get_latest_release_draft_filtered(self):
        """过滤掉 draft 版本"""
        mock_data = {
            "tag_name": "v2.1.0",
            "prerelease": False,
            "draft": True,
            "assets": [
                {
                    "name": "windows-folder-remark-2.1.0.exe",
                    "browser_download_url": "https://github.com/.../exe",
                }
            ],
        }

        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with (
            patch("urllib.request.OpenerDirector.open", return_value=mock_response),
            patch("json.load", return_value=mock_data),
        ):
            result = get_latest_release()

        assert result is None

    def test_get_latest_release_no_exe_asset(self):
        """无 exe 文件时返回 None"""
        mock_data = {
            "tag_name": "v2.0.3",
            "prerelease": False,
            "draft": False,
            "assets": [
                {"name": "README.md", "browser_download_url": "https://github.com/.../README.md"}
            ],
        }

        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with (
            patch("urllib.request.OpenerDirector.open", return_value=mock_response),
            patch("json.load", return_value=mock_data),
        ):
            result = get_latest_release()

        assert result is None

    def test_get_latest_release_api_error(self):
        """API 请求失败时返回 None"""
        # 使用 parse_headers 创建空的 HTTPMessage
        # HTTPError(url, code, msg, hdrs, fp)
        import http.client
        import urllib.error
        from io import BytesIO

        hdrs = http.client.parse_headers(BytesIO())
        with patch(
            "urllib.request.OpenerDirector.open",
            side_effect=urllib.error.HTTPError("url", 500, "Error", hdrs, BytesIO(b"error body")),
        ):
            result = get_latest_release()

        assert result is None

    def test_get_latest_release_json_error(self):
        """JSON 解析失败时返回 None"""
        with patch("json.load", side_effect=json.JSONDecodeError("error", "", 0)):
            result = get_latest_release()

        assert result is None

    def test_get_latest_release_non_200_status(self):
        """HTTP 状态码不是 200 时返回 None"""
        mock_response = Mock()
        mock_response.status = 404
        mock_response.headers = {}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.OpenerDirector.open", return_value=mock_response):
            result = get_latest_release()

        assert result is None


@pytest.mark.unit
class TestCacheFunctions:
    """测试缓存相关函数（核心逻辑）"""

    def test_should_check_update_no_cache_file(self, fs):
        """无缓存文件时返回 True（首次检查）"""
        result = should_check_update()
        assert result is True

    def test_should_check_update_invalid_content(self, fs):
        """缓存文件内容无效时返回 True"""
        cache_file = _get_cache_file_path()
        fs.create_file(cache_file, contents="invalid_content")

        result = should_check_update()
        assert result is True

    def test_should_check_update_cache_expired(self, fs):
        """缓存过期时返回 True"""
        # 设置一个过去的时间戳（2024-01-01）
        past_time = 1704067200.0
        cache_file = _get_cache_file_path()
        fs.create_file(cache_file, contents=str(past_time))

        # Mock 当前时间为 2024-01-02
        with patch("time.time", return_value=1704153600.0):
            result = should_check_update()

        assert result is True

    def test_should_check_update_cache_valid(self, fs):
        """缓存未过期时返回 False"""
        current_time = 1704067200.0
        cache_file = _get_cache_file_path()
        # 缓存设置为未来时间
        next_check = current_time + UPDATE_CHECK_INTERVAL
        fs.create_file(cache_file, contents=str(next_check))

        with patch("time.time", return_value=current_time):
            result = should_check_update()

        assert result is False

    def test_update_next_check_time(self, fs):
        """更新下次检查时间为当前时间 + 24 小时"""
        current_time = 1704067200.0

        with patch("time.time", return_value=current_time):
            update_next_check_time()

        cache_file = _get_cache_file_path()
        with open(cache_file, encoding="utf-8") as f:
            cached_time = float(f.read().strip())

        expected = current_time + UPDATE_CHECK_INTERVAL
        assert cached_time == expected

    def test_update_next_check_time_silent_failure(self, fs):
        """写入失败时静默处理（不抛异常）"""
        current_time = 1704067200.0

        with (
            patch("time.time", return_value=current_time),
            patch("builtins.open", side_effect=OSError("Permission denied")),
        ):
            update_next_check_time()

    def test_check_updates_auto_skips_when_not_needed(self, fs):
        """不需要检查时直接返回 None，不调用 API"""
        current_time = 1704067200.0
        cache_file = _get_cache_file_path()
        next_check = current_time + UPDATE_CHECK_INTERVAL
        fs.create_file(cache_file, contents=str(next_check))

        with (
            patch("time.time", return_value=current_time),
            patch("remark.utils.updater.get_latest_release") as mock_api,
        ):
            result = check_updates_auto("2.0.2")

        assert result is None
        mock_api.assert_not_called()

    def test_check_updates_auto_updates_cache_after_check(self, fs):
        """检查后立即更新缓存时间"""
        current_time = 1704067200.0

        with (
            patch("time.time", return_value=current_time),
            patch("remark.utils.updater.get_latest_release", return_value=None),
        ):
            check_updates_auto("2.0.2")

        cache_file = _get_cache_file_path()
        with open(cache_file, encoding="utf-8") as f:
            cached_time = float(f.read().strip())

        expected = current_time + UPDATE_CHECK_INTERVAL
        assert cached_time == expected

    def test_check_updates_auto_has_new_version(self, fs):
        """有新版本时返回 release 信息"""
        current_time = 1704067200.0
        mock_release = {
            "tag_name": "2.0.3",
            "html_url": "https://github.com/.../2.0.3",
            "body": "New version",
            "download_url": "https://github.com/.../exe",
        }

        with (
            patch("time.time", return_value=current_time),
            patch("remark.utils.updater.get_latest_release", return_value=mock_release),
        ):
            result = check_updates_auto("2.0.2")

        assert result is not None
        assert result["tag_name"] == "2.0.3"

    def test_check_updates_auto_no_new_version(self, fs):
        """无新版本时返回 None"""
        current_time = 1704067200.0
        mock_release = {
            "tag_name": "2.0.2",
            "html_url": "https://github.com/.../2.0.2",
            "body": "Current version",
            "download_url": "https://github.com/.../exe",
        }

        with (
            patch("time.time", return_value=current_time),
            patch("remark.utils.updater.get_latest_release", return_value=mock_release),
        ):
            result = check_updates_auto("2.0.2")

        assert result is None

    def test_check_updates_auto_api_failure(self, fs):
        """API 失败时返回 None"""
        current_time = 1704067200.0

        with (
            patch("time.time", return_value=current_time),
            patch("remark.utils.updater.get_latest_release", return_value=None),
        ):
            result = check_updates_auto("2.0.2")

        assert result is None

    def test_check_updates_manual_ignores_cache(self, fs):
        """check_updates_manual 忽略缓存，直接调用 API"""
        current_time = 1704067200.0
        cache_file = _get_cache_file_path()
        next_check = current_time + UPDATE_CHECK_INTERVAL
        fs.create_file(cache_file, contents=str(next_check))

        mock_release = {
            "tag_name": "2.0.3",
            "html_url": "https://github.com/.../2.0.3",
            "body": "New version",
            "download_url": "https://github.com/.../exe",
        }

        with patch(
            "remark.utils.updater.get_latest_release", return_value=mock_release
        ) as mock_api:
            result = check_updates_manual("2.0.2")

        mock_api.assert_called_once()
        assert result is not None
        assert result["tag_name"] == "2.0.3"

    def test_check_updates_manual_no_new_version(self):
        """无新版本时返回 None"""
        mock_release = {
            "tag_name": "2.0.2",
            "html_url": "https://github.com/.../2.0.2",
            "body": "Current version",
            "download_url": "https://github.com/.../exe",
        }

        with patch("remark.utils.updater.get_latest_release", return_value=mock_release):
            result = check_updates_manual("2.0.2")

        assert result is None

    def test_check_updates_manual_api_returns_none(self):
        """API 返回 None 时返回 None"""
        with patch("remark.utils.updater.get_latest_release", return_value=None):
            result = check_updates_manual("2.0.2")

        assert result is None


@pytest.mark.unit
class TestDownloadUpdate:
    """测试下载更新函数"""

    def test_download_update_success(self, tmp_path):
        """正常下载文件"""
        dest = str(tmp_path / "test.exe")

        mock_response = Mock()
        mock_response.headers = {"content-length": "100"}
        mock_response.read.side_effect = [b"chunk1", b"chunk2", b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.OpenerDirector.open", return_value=mock_response):
            result = download_update("http://example.com/test.exe", dest)

        assert result == dest

    def test_download_update_progress(self, tmp_path, capsys):
        """显示下载进度"""
        dest = str(tmp_path / "test.exe")

        mock_response = Mock()
        mock_response.headers = {"content-length": "100"}
        mock_response.read.side_effect = [b"x" * 25, b"x" * 25, b"x" * 25, b"x" * 25, b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.OpenerDirector.open", return_value=mock_response):
            download_update("http://example.com/test.exe", dest)

        captured = capsys.readouterr()
        assert "下载进度" in captured.out

    def test_download_update_network_error(self):
        """网络错误时抛出异常"""
        import urllib.error

        with (
            patch(
                "urllib.request.OpenerDirector.open",
                side_effect=urllib.error.URLError("Network error"),
            ),
            pytest.raises(urllib.error.URLError),
        ):
            download_update("http://example.com/test.exe", "/tmp/test.exe")


@pytest.mark.unit
class TestUpdateScript:
    """测试更新脚本相关函数"""

    def test_create_update_script(self, tmp_path):
        """创建批处理脚本"""
        old_exe = "C:/Program Files/old.exe"
        new_exe = str(tmp_path / "new.exe")

        result = create_update_script(old_exe, new_exe)

        assert os.path.exists(result)
        with open(result, encoding="gbk") as f:
            content = f.read()

        assert old_exe in content
        assert new_exe in content
        assert "move" in content

    def test_trigger_update(self):
        """使用 subprocess.Popen 启动"""
        with patch("subprocess.Popen") as mock_popen:
            trigger_update("/tmp/update.bat")

            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            assert call_args[0][0] == ["cmd.exe", "/c", "/tmp/update.bat"]
            assert call_args[1]["shell"] is True
            assert "creationflags" in call_args[1]


@pytest.mark.unit
class TestInvalidVersion:
    """测试无效版本号处理"""

    def test_check_updates_auto_invalid_version(self, fs):
        """当前版本号无效时返回 None"""
        current_time = 1704067200.0
        mock_release = {
            "tag_name": "invalid-version",
            "html_url": "https://github.com/.../invalid",
            "body": "Invalid",
            "download_url": "https://github.com/.../exe",
        }

        with (
            patch("time.time", return_value=current_time),
            patch("remark.utils.updater.get_latest_release", return_value=mock_release),
        ):
            result = check_updates_auto("2.0.2")

        assert result is None

    def test_check_updates_manual_invalid_version(self):
        """强制检查时，版本号无效返回 None"""
        mock_release = {
            "tag_name": "invalid-version",
            "html_url": "https://github.com/.../invalid",
            "body": "Invalid",
            "download_url": "https://github.com/.../exe",
        }

        with patch("remark.utils.updater.get_latest_release", return_value=mock_release):
            result = check_updates_manual("2.0.2")

        assert result is None
