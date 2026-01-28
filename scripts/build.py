"""
本地打包脚本

使用方法:
    # 打包为单文件 exe
    python -m scripts.build

    # 清理构建文件
    python -m scripts.build --clean
"""

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Callable

# 设置 UTF-8 输出编码（Windows 兼容）
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 导入 ensure_upx 模块
do_ensure_upx: Callable[[], str | None] | None = None
HAS_UPX_SCRIPT = False
try:
    from scripts.ensure_upx import ensure_upx as do_ensure_upx

    HAS_UPX_SCRIPT = True
except ImportError:
    pass


def get_project_version():
    """获取项目版本号"""
    toml_file = os.path.join(ROOT_DIR, "pyproject.toml")
    with open(toml_file, encoding="utf-8") as f:
        content = f.read()
        import re

        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    return "unknown"


def clean_build_files():
    """清理构建文件"""
    print("清理构建文件...")

    dirs_to_remove = ["build", "dist", "spec"]

    for dir_name in dirs_to_remove:
        dir_path = os.path.join(ROOT_DIR, dir_name)
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"  已删除: {dir_name}/")

    print("✓ 清理完成")


def ensure_upx():
    """确保 UPX 压缩工具可用"""
    print("检查 UPX 压缩工具...")

    if not HAS_UPX_SCRIPT or do_ensure_upx is None:
        print("警告: UPX 安装脚本不存在，跳过")
        return True

    try:
        upx_path = do_ensure_upx()
        return upx_path is not None
    except Exception as e:
        print(f"警告: UPX 检查失败: {e}")
        print("将继续打包，但压缩可能被禁用")
        return True


def build_exe():
    """使用 PyInstaller 打包为单文件 exe"""
    print("开始打包...")

    spec_file = os.path.join(ROOT_DIR, "remark.spec")
    if not os.path.exists(spec_file):
        print(f"错误: 找不到 {spec_file}")
        return False

    # 检查 PyInstaller 是否安装
    try:
        import PyInstaller

        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: 未安装 PyInstaller")
        print("请运行: pip install pyinstaller")
        return False

    # 确保 UPX 可用
    if not ensure_upx():
        print("警告: UPX 不可用，exe 体积会更大")

    # 运行 PyInstaller
    try:
        subprocess.run(
            ["pyinstaller", spec_file, "--clean"],
            cwd=ROOT_DIR,
            check=True,
        )
        print("✓ 打包完成")
        print("\n输出文件: dist/windows-folder-remark.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False
    except FileNotFoundError:
        print("错误: 找不到 pyinstaller 命令")
        print("请运行: pip install pyinstaller")
        return False


def main():
    parser = argparse.ArgumentParser(description="本地打包工具")
    parser.add_argument("--clean", "-c", action="store_true", help="仅清理构建文件，不进行打包")

    args = parser.parse_args()

    if args.clean:
        clean_build_files()
        return

    # 打包前先清理
    clean_build_files()
    print()

    # 开始打包
    version = get_project_version()
    print(f"项目版本: {version}")
    print()

    if build_exe():
        print("\n" + "=" * 50)
        print("打包成功!")
        print(f"版本: {version}")
        print("位置: dist/windows-folder-remark.exe")
        print("=" * 50)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
