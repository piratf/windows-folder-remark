"""
UPX 下载脚本

自动从 GitHub releases 下载最新版本的 UPX 压缩工具。

使用方法:
    python scripts/ensure_upx.py
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

# 设置 UTF-8 输出编码（Windows 兼容）
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# UPX 安装目录
UPX_DIR = os.path.join(ROOT_DIR, "tools", "upx")

# GitHub API 配
GITHUB_API_RELEASES = "https://api.github.com/repos/upx/upx/releases/latest"


def get_proxies() -> dict[str, str] | None:
    """从环境变量获取代理配置"""
    proxies = []
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

    if http_proxy:
        proxies.append(("http", http_proxy))
    if https_proxy:
        proxies.append(("https", https_proxy))

    return dict(proxies) if proxies else None


def create_opener():
    """创建带代理的 URL opener"""
    proxies = get_proxies()
    if proxies:
        proxy_handler = urllib.request.ProxyHandler(proxies)
        return urllib.request.build_opener(proxy_handler)
    return urllib.request.build_opener()


def get_system_info():
    """获取系统信息"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        if machine in ("amd64", "x86_64"):
            return "win_amd64"
        elif machine in ("i386", "i686", "x86"):
            return "win32"
    return None


def get_latest_upx_version() -> tuple[str, str, str] | None:
    """从 GitHub API 获取最新 UPX 版本和下载信息

    Returns:
        (version, download_url, asset_name) 或 None
    """
    try:
        proxies = get_proxies()
        if proxies:
            print(f"  使用代理: {proxies.get('https', proxies.get('http'))}")

        request = urllib.request.Request(
            GITHUB_API_RELEASES,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "windows-folder-remark",
            },
        )
        opener = create_opener()
        with opener.open(request, timeout=10) as response:
            if response.status != 200:
                return None
            data = json.load(response)

        version = data["tag_name"].lstrip("v")

        # 获取目标平台
        target_platform = get_system_info()
        if not target_platform:
            return None

        # 查找匹配的 asset
        platform_keywords = {
            "win_amd64": ["win", "64"],
            "win32": ["win", "32"],
        }

        keywords = platform_keywords.get(target_platform, [])

        for asset in data.get("assets", []):
            name = asset["name"].lower()
            # 检查是否匹配平台关键词
            if all(kw in name for kw in keywords):
                return version, asset["browser_download_url"], asset["name"]

        print(f"错误: 找不到适合 {target_platform} 的 UPX 包")
        print("可用的包:")
        for asset in data.get("assets", []):
            print(f"  - {asset['name']}")
        return None

    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"警告: 无法获取 UPX 版本信息: {e}")
        return None


def find_upx_executable() -> str | None:
    """查找已存在的 UPX 可执行文件"""
    # 优先使用项目本地的 UPX
    local_upx = os.path.join(UPX_DIR, "upx.exe")
    if os.path.exists(local_upx):
        return local_upx

    # 检查系统 PATH 中是否有 UPX
    try:
        result = subprocess.run(
            ["where", "upx"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except FileNotFoundError:
        pass

    return None


def download_upx(version: str, download_url: str, asset_name: str) -> str | None:
    """下载 UPX 并解压到指定目录

    Args:
        version: UPX 版本号
        download_url: 实际的下载 URL（从 API 获取）
        asset_name: 资源文件名

    Returns:
        UPX 可执行文件路径，失败返回 None
    """
    print(f"正在下载 UPX {version}...")
    print(f"  文件: {asset_name}")
    print(f"  URL: {download_url}")

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, asset_name)

        # 下载文件
        try:
            request = urllib.request.Request(
                download_url,
                headers={"User-Agent": "windows-folder-remark"},
            )
            opener = create_opener()

            with opener.open(request, timeout=60) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 8192

                with open(zip_path, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 显示进度
                        if total_size > 0:
                            progress = int(50 * downloaded / total_size)
                            downloaded_mb = downloaded / 1024 / 1024
                            print(
                                f"\r  进度: [{'#' * progress}{'.' * (50 - progress)}] {downloaded_mb:.1f}MB",
                                end="",
                            )

            print()  # 换行

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"\n错误: 下载失败: {e}")
            return None

        # 解压文件
        print("正在解压...")
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile as e:
            print(f"错误: 解压失败: {e}")
            return None

        # 查找 upx.exe
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file == "upx.exe":
                    src = os.path.join(root, file)
                    # 创建目标目录
                    os.makedirs(UPX_DIR, exist_ok=True)
                    dst = os.path.join(UPX_DIR, file)
                    shutil.copy2(src, dst)
                    return dst

        print("错误: 在下载的包中找不到 upx.exe")
        return None


def verify_upx(upx_path: str) -> bool:
    """验证 UPX 是否可用"""
    try:
        result = subprocess.run(
            [upx_path, "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # 检查输出是否包含 UPX
        if "upx" in result.stdout.lower():
            version_line = result.stdout.split("\n")[0]
            print(f"  版本: {version_line.strip()}")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return False


def ensure_upx() -> str | None:
    """确保 UPX 可用，返回 UPX 可执行文件路径"""
    # 检查平台
    target_platform = get_system_info()
    if not target_platform:
        print("错误: 不支持的平台")
        print("  UPX 自动下载仅支持 Windows")
        return None

    print("检查 UPX 压缩工具...")

    # 查找已存在的 UPX
    upx_path = find_upx_executable()
    if upx_path:
        print(f"  找到 UPX: {upx_path}")
        if verify_upx(upx_path):
            return upx_path
        print("  警告: 现有 UPX 不可用")

    # 获取最新版本和下载信息
    release_info = get_latest_upx_version()
    if not release_info:
        print("错误: 无法获取 UPX 最新版本")
        return None

    version, download_url, asset_name = release_info
    print(f"  最新版本: {version}")

    # 下载 UPX
    upx_path = download_upx(version, download_url, asset_name)
    if not upx_path:
        return None

    # 验证下载的 UPX
    if verify_upx(upx_path):
        print(f"✓ UPX 已安装到: {upx_path}")
        return upx_path

    print("错误: UPX 验证失败")
    return None


def main():
    """主入口"""
    upx_path = ensure_upx()
    if upx_path:
        print(f"\nUPX 路径: {upx_path}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
