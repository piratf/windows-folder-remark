"""
自动更新模块

提供版本检测、下载更新、创建更新脚本等功能。
"""

import os
import sys
import tempfile
from typing import Any

import requests
from packaging import version
from tqdm import tqdm

from remark.utils.constants import (
    GITHUB_API_RELEASES,
    UPDATE_CACHE_FILE,
    UPDATE_CHECK_INTERVAL,
)


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

    Returns:
        包含 tag_name, html_url, body, download_url 的字典，如果获取失败则返回 None
    """
    try:
        response = requests.get(GITHUB_API_RELEASES, timeout=10)
        response.raise_for_status()
        data = response.json()

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
    except requests.RequestException:
        return None


def check_update_cache() -> bool:
    """
    检查是否在更新缓存时间内

    Returns:
        True 表示需要检查更新，False 表示在缓存期内
    """
    cache_file = _get_cache_file_path()
    if not os.path.exists(cache_file):
        return True

    try:
        with open(cache_file, encoding="utf-8") as f:
            last_check = float(f.read().strip())
        import time

        return time.time() - last_check > UPDATE_CHECK_INTERVAL
    except (ValueError, OSError):
        return True


def update_check_cache() -> None:
    """更新检查时间缓存"""
    cache_file = _get_cache_file_path()
    try:
        import time

        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except OSError:
        pass


def check_for_updates(current_version: str) -> dict[str, Any] | None:
    """
    检查是否有新版本可用

    Args:
        current_version: 当前版本号

    Returns:
        最新 release 信息字典，如果没有新版本则返回 None
    """
    # 检查缓存
    if not check_update_cache():
        return None

    # 获取最新 release
    latest = get_latest_release()
    if not latest:
        return None

    # 比较版本号
    try:
        if version.parse(latest["tag_name"]) > version.parse(current_version):
            update_check_cache()
            return latest
    except version.InvalidVersion:
        return None

    update_check_cache()
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
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    total_size = int(response.headers.get("content-length", 0))

    with (
        open(dest, "wb") as f,
        tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc="下载中",
        ) as progress_bar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                progress_bar.update(len(chunk))

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
