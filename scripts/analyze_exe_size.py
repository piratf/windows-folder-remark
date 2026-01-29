"""
PyInstaller EXE 大小分析工具

使用方法:
    python scripts/analyze_exe_size.py

功能:
    1. 运行 pyi-archive_viewer -r 获取 exe 内容
    2. 分析各组件大小
    3. 生成详细报告到 tmp/ 目录
"""

import os
import re
import subprocess
from datetime import datetime


def run_archive_viewer(exe_path: str) -> str:
    """运行 pyi-archive_viewer -r 并获取输出"""
    print(f"Analyzing {exe_path}...")

    result = subprocess.run(
        ["pyi-archive_viewer", "-r", exe_path],
        capture_output=True,
        text=True,
    )

    return result.stdout


def parse_archive_content(content: str) -> dict[str, int]:
    """解析 archive_viewer 输出，返回 {name: size} 字典"""
    components: dict[str, int] = {}
    for line in content.split("\n"):
        if not line.strip() or line.startswith("position") or line.startswith("Options"):
            continue
        match = re.match(r"^\s*\d+,\s*(\d+),\s*\d+,\s*\d+,\s*'[^']+',\s*'([^']+)'", line)
        if match:
            size = int(match.group(1))
            name = match.group(2)
            components[name] = components.get(name, 0) + size
    return components


def parse_pyz_content(content: str) -> dict[str, int]:
    """解析 PYZ.pyz 内部内容"""
    if "Contents of 'PYZ.pyz'" not in content:
        return {}

    pyz_section = content.split("Contents of 'PYZ.pyz'")[1]
    lines = pyz_section.split("\n")[:5000]

    packages: dict[str, int] = {}
    for line in lines:
        if not line.strip() or line.startswith("Contents") or line.startswith("typecode"):
            continue
        parts = line.split(",")
        if len(parts) >= 4:
            try:
                length = int(parts[2].strip())
                name = parts[3].strip().strip("'")

                # 按包分组
                if "." in name:
                    pkg = name.split(".")[0]
                else:
                    pkg = name

                packages[pkg] = packages.get(pkg, 0) + length
            except (ValueError, IndexError):
                pass
    return packages


def generate_report(
    exe_path: str,
    components: dict[str, int],
    pyz_packages: dict[str, int],
    output_path: str,
) -> None:
    """生成分析报告"""
    exe_size = os.path.getsize(exe_path)

    lines = []
    lines.append("=" * 80)
    lines.append("PyInstaller EXE Size Analysis Report")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"EXE: {exe_path}")
    lines.append(f"Current EXE Size: {exe_size / (1024 * 1024):.2f} MB ({exe_size:,} bytes)")
    lines.append(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 1. 最大的文件
    lines.append("=" * 80)
    lines.append("1. Top 50 Largest Files/Components")
    lines.append("=" * 80)
    lines.append("")
    sorted_all = sorted(components.items(), key=lambda x: x[1], reverse=True)
    for i, (name, size) in enumerate(sorted_all[:50], 1):
        name_short = name[:47] + "..." if len(name) > 50 else name
        lines.append(f"{i:3d}. {name_short:<50} {size // 1024:6d} KB")

    # 2. DLL 文件
    lines.append("")
    lines.append("=" * 80)
    lines.append("2. DLL Files (Windows System Libraries)")
    lines.append("=" * 80)
    lines.append("")
    dlls = [(n, s) for n, s in components.items() if n.endswith(".dll")]
    dlls.sort(key=lambda x: x[1], reverse=True)
    for name, size in dlls[:30]:
        lines.append(f"{name:<60} {size // 1024:6d} KB")

    # 3. PYD 文件
    lines.append("")
    lines.append("=" * 80)
    lines.append("3. PYD Files (Python Extension Modules)")
    lines.append("=" * 80)
    lines.append("")
    pyds = [(n, s) for n, s in components.items() if n.endswith(".pyd")]
    pyds.sort(key=lambda x: x[1], reverse=True)
    for name, size in pyds[:20]:
        lines.append(f"{name:<60} {size // 1024:6d} KB")

    # 4. Tcl/Tk 文件
    lines.append("")
    lines.append("=" * 80)
    lines.append("4. Tcl/Tk Data Files")
    lines.append("=" * 80)
    lines.append("")
    tcl_files = [(n, s) for n, s in components.items() if "_tcl_data" in n or "tcl8" in n]
    tcl_files.sort(key=lambda x: x[1], reverse=True)
    for name, size in tcl_files[:30]:
        lines.append(f"{name:<60} {size // 1024:6d} KB")

    # 5. PYZ.pyz 内部模块
    if pyz_packages:
        lines.append("")
        lines.append("=" * 80)
        lines.append("PYZ.pyz Internal Python Modules Analysis")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Total PYZ.pyz size: {sum(pyz_packages.values()) // 1024} KB")
        lines.append("")

        lines.append("=" * 80)
        lines.append("5. Python Packages by Size (Top 50)")
        lines.append("=" * 80)
        lines.append("")
        sorted_packages = sorted(pyz_packages.items(), key=lambda x: x[1], reverse=True)
        for pkg, size in sorted_packages[:50]:
            lines.append(f"{pkg:<30} {size // 1024:6d} KB")

        # 可移除的模块
        excludable = ["setuptools", "unittest", "email", "distutils", "pydoc", "pydoc_data", "test"]
        lines.append("")
        lines.append("=" * 80)
        lines.append("6. Potentially Removable Modules")
        lines.append("=" * 80)
        lines.append("")
        excludable_packages = [
            (p, s) for p, s in sorted_packages if any(e in p for e in excludable)
        ]
        total_removable = sum(s for p, s in excludable_packages)
        for pkg, size in excludable_packages:
            lines.append(f"{pkg:<30} {size // 1024:6d} KB")
        lines.append("")
        lines.append(
            f"Total potentially removable: {total_removable // 1024} KB ({total_removable // 1024 / 1024:.2f} MB)"
        )

    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    # 获取 exe 路径
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exe_path = os.path.join(script_dir, "dist", "windows-folder-remark.exe")

    if not os.path.exists(exe_path):
        print(f"Error: {exe_path} not found!")
        print("Please build the exe first with: pyinstaller remark.spec")
        return 1

    # 运行 archive_viewer
    recursive_content = run_archive_viewer(exe_path)

    # 解析内容
    components = parse_archive_content(recursive_content)
    pyz_packages = parse_pyz_content(recursive_content)

    # 生成带时间戳的输出文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = os.path.join(script_dir, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    output_path = os.path.join(tmp_dir, f"exe_size_analysis_{timestamp}.txt")

    # 生成报告
    generate_report(exe_path, components, pyz_packages, output_path)

    print(f"\nReport saved to: {output_path}")

    # 打印摘要
    exe_size = os.path.getsize(exe_path)
    print("\nSummary:")
    print(f"  EXE Size: {exe_size / (1024 * 1024):.2f} MB")
    print(f"  Largest component: {max(components.items(), key=lambda x: x[1])[0]}")
    if pyz_packages and "setuptools" in pyz_packages:
        print(f"  setuptools size: {pyz_packages['setuptools'] // 1024} KB (removable)")

    return 0


if __name__ == "__main__":
    exit(main())
