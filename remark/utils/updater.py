"""
自动更新模块

提供版本检测、下载更新、创建更新脚本等功能。
"""

import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from typing import Any

from packaging import version

from remark.utils.constants import (
    GITHUB_API_RELEASES,
    UPDATE_CACHE_FILE,
    UPDATE_CHECK_INTERVAL,
)


def _get_proxies() -> dict[str, str] | None:
    """从环境变量获取代理配置"""
    proxies = []
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

    if http_proxy:
        proxies.append(("http", http_proxy))
    if https_proxy:
        proxies.append(("https", https_proxy))

    return dict(proxies) if proxies else None


def _create_opener():
    """创建带代理的 URL opener"""
    proxies = _get_proxies()
    if proxies:
        proxy_handler = urllib.request.ProxyHandler(proxies)
        return urllib.request.build_opener(proxy_handler)
    return urllib.request.build_opener()


def _get_cache_file_path() -> str:
    """获取缓存文件的完整路径（放在临时目录）"""
    return os.path.join(tempfile.gettempdir(), UPDATE_CACHE_FILE)


def get_executable_path() -> str:
    """获取当前可执行文件路径"""
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后的 exe
        return sys.executable
    else:
        # 开发环境下的 Python 脚本
        return os.path.abspath(__file__)


def get_latest_release() -> dict[str, Any] | None:
    """
    从 GitHub API 获取最新 release 信息
    使用 urllib 而不是 requests 是为了减少打包体积，减轻用户下载负担

    Returns:
        包含 tag_name, html_url, body, download_url 的字典，如果获取失败则返回 None
    """
    try:
        request = urllib.request.Request(
            GITHUB_API_RELEASES,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "windows-folder-remark",
            },
        )
        opener = _create_opener()
        with opener.open(request, timeout=10) as response:
            if response.status != 200:
                return None
            data = json.load(response)

        # 过滤掉 prerelease 和 draft
        if data.get("prerelease") or data.get("draft"):
            return None

        # 查找 windows-folder-remark-*.exe 文件
        download_url = None
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if name.startswith("windows-folder-remark-") and name.endswith(".exe"):
                download_url = asset.get("browser_download_url")
                break

        if not download_url:
            return None

        return {
            "tag_name": data.get("tag_name", "").lstrip("v"),
            "html_url": data.get("html_url", ""),
            "body": data.get("body", ""),
            "download_url": download_url,
        }
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, OSError):
        return None


def should_check_update() -> bool:
    """
    检查是否应该进行更新检查

    Returns:
        True 表示应该检查，False 表示还没到检查时间
    """
    cache_file = _get_cache_file_path()
    if not os.path.exists(cache_file):
        return True  # 没有记录，进行第一次检查

    try:
        import time

        with open(cache_file, encoding="utf-8") as f:
            next_check_time = float(f.read().strip())
        return time.time() >= next_check_time
    except (ValueError, OSError):
        return True


def update_next_check_time() -> None:
    """更新下次检查时间为当前时间 + 24小时"""
    cache_file = _get_cache_file_path()
    try:
        import time

        next_check = time.time() + UPDATE_CHECK_INTERVAL
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(str(next_check))
    except OSError:
        pass


def check_for_updates(current_version: str) -> dict[str, Any] | None:
    """
    检查是否有新版本可用（仅在需要时检查）

    Args:
        current_version: 当前版本号

    Returns:
        最新 release 信息字典，如果没有新版本则返回 None
    """
    if not should_check_update():
        return None

    # 决定检查，立即更新下次检查时间
    update_next_check_time()

    latest = get_latest_release()
    if not latest:
        return None

    try:
        if version.parse(latest["tag_name"]) > version.parse(current_version):
            return latest
    except version.InvalidVersion:
        return None

    return None


def force_check_updates(current_version: str) -> dict[str, Any] | None:
    """
    强制检查更新，不受缓存影响

    Args:
        current_version: 当前版本号

    Returns:
        最新 release 信息字典，如果没有新版本则返回 None
    """
    latest = get_latest_release()
    if not latest:
        return None

    try:
        if version.parse(latest["tag_name"]) > version.parse(current_version):
            return latest
    except version.InvalidVersion:
        return None

    return None


def download_update(url: str, dest: str) -> str:
    """
    下载新版本 exe

    Args:
        url: 下载 URL
        dest: 目标路径（文件名）

    Returns:
        下载的文件路径
    """
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "windows-folder-remark"},
    )
    opener = _create_opener()

    with opener.open(request, timeout=30) as response:
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 8192

        with open(dest, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)

                # 显示进度
                if total_size > 0:
                    percent = min(downloaded * 100 / total_size, 100)
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total_size / 1024 / 1024
                    print(
                        f"\r下载进度: {percent:.1f}% ({downloaded_mb:.1f}MB / {total_mb:.1f}MB)",
                        end="",
                    )
        print()  # 换行

    return dest


def create_update_script(old_exe: str, new_exe: str) -> str:
    """
    创建更新批处理脚本

    Args:
        old_exe: 旧 exe 路径
        new_exe: 新 exe 路径

    Returns:
        批处理脚本路径
    """
    script_content = f"""@echo off
REM 等待主进程退出
timeout /t 3 /nobreak >nul

REM 替换 exe
move /Y "{new_exe}" "{old_exe}"

REM 删除自己
del "%~f0"

REM 更新完成
echo 更新完成！请手动启动新版本程序。
pause
"""

    # 创建临时脚本文件
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "update_windows_folder_remark.bat")

    with open(script_path, "w", encoding="gbk") as f:
        f.write(script_content)

    return script_path


def trigger_update(script_path: str) -> None:
    """
    触发更新流程：启动批处理脚本并退出程序

    Args:
        script_path: 批处理脚本路径
    """
    import subprocess

    # 启动批处理脚本（新窗口，不阻塞）
    subprocess.Popen(
        ["cmd.exe", "/c", script_path],
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
