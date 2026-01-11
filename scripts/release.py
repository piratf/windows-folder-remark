"""
版本发布脚本

使用方法:
    # 查看当前版本
    python scripts/release.py

    # 递增补丁版本 (2.0.0 -> 2.0.1)
    python scripts/release.py patch

    # 递增次版本 (2.0.0 -> 2.1.0)
    python scripts/release.py minor

    # 递增主版本 (2.0.0 -> 3.0.0)
    python scripts/release.py major

    # 设置特定版本
    python scripts/release.py 2.1.0

    # 创建并推送 release tag
    python scripts/release.py patch --push
"""

import argparse
import os
import re
import subprocess
import sys

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_current_version():
    """获取当前版本号（从 pyproject.toml）"""
    toml_file = os.path.join(ROOT_DIR, "pyproject.toml")
    with open(toml_file, encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    raise ValueError("无法在 pyproject.toml 中找到版本号")


def update_version(new_version):
    """更新 pyproject.toml 中的版本号"""
    toml_file = os.path.join(ROOT_DIR, "pyproject.toml")
    with open(toml_file, encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'(version\s*=\s*["\'])([^"\']+)(["\'])', rf"\g<1>{new_version}\g<3>", content)
    with open(toml_file, "w", encoding="utf-8") as f:
        f.write(content)
    return new_version


def bump_version(current, part="patch"):
    """递增版本号"""
    major, minor, patch = map(int, current.split("."))

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f"{major}.{minor}.{patch}"


def create_tag(version):
    """创建 git tag"""
    tag_name = f"v{version}"
    subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], check=True)
    print(f"已创建 tag: {tag_name}")
    return tag_name


def push_tag(tag_name):
    """推送 tag 到远程仓库"""
    subprocess.run(["git", "push", "origin", tag_name], check=True)
    print(f"已推送 tag: {tag_name}")


def commit_version_changes():
    """提交版本变更"""
    current_version = get_current_version()
    subprocess.run(["git", "add", "pyproject.toml"], check=True)
    subprocess.run(["git", "commit", "-m", f"bump: version to {current_version}"], check=True)
    print(f"已提交版本变更: {current_version}")


def main():
    parser = argparse.ArgumentParser(description="版本发布管理工具")
    parser.add_argument(
        "version", nargs="?", help="新版本号 (如: 2.1.0) 或递增类型: patch/minor/major"
    )
    parser.add_argument(
        "--push", "-p", action="store_true", help="创建并推送 tag 到远程仓库（触发 GitHub Actions）"
    )
    parser.add_argument("--commit", "-c", action="store_true", help="提交版本变更到 git")
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="只显示将要执行的操作，不实际执行"
    )

    args = parser.parse_args()

    current = get_current_version()
    print(f"当前版本: {current}")

    if not args.version:
        return

    # 确定新版本号
    if args.version in ("patch", "minor", "major"):
        new_version = bump_version(current, args.version)
    else:
        # 验证版本号格式
        if not re.match(r"^\d+\.\d+\.\d+$", args.version):
            print("错误: 版本号格式应为 x.y.z")
            sys.exit(1)
        new_version = args.version

    print(f"新版本: {new_version}")

    if args.dry_run:
        print("\n[DRY RUN] 将执行以下操作:")
        print(f"  1. 更新版本号: {current} -> {new_version}")
        if args.commit:
            print("  2. 提交版本变更")
        if args.push:
            print(f"  3. 创建并推送 tag v{new_version}")
        return

    # 更新版本文件
    update_version(new_version)
    print(f"已更新版本号到: {new_version}")

    # 提交变更
    if args.commit:
        commit_version_changes()

    # 创建并推送 tag
    if args.push:
        tag_name = create_tag(new_version)
        push_tag(tag_name)
        print(f"\n✓ Release v{new_version} 已准备就绪!")
        print("  GitHub Actions 将自动构建并发布")
    else:
        print("\n提示: 使用 --push 参数创建并推送 tag 以触发 release")


if __name__ == "__main__":
    main()
