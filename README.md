# Windows Folder Remark/Comment Tool - Windows 文件夹备注工具

**[English Documentation](README.en.md)** | [中文文档](README.md)

[![PyPI](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![en](https://img.shields.io/badge/lang-en-blue.svg)](README.en.md)
[![zh](https://img.shields.io/badge/lang-zh-red.svg)](README.md)

A lightweight CLI tool to add remarks/comments to Windows folders via Desktop.ini. No background processes, privacy-first, ~12MB portable exe. / 一个轻量级的命令行工具，通过 Desktop.ini 为 Windows 文件夹添加备注/评论。无后台进程，隐私优先，约 12MB 便携版 exe。

**Documentation**: [Full Documentation](https://piratf.github.io/windows-folder-remark/en/) | [完整文档](https://piratf.github.io/windows-folder-remark/zh/)

## ⭐ 支持

如果这个工具对你有帮助，请在 GitHub 上给个 Star！

## 工具优势

- **用完即走**：需要时运行，用完即退出，无后台进程占用
- **轻量小巧**：仅约 12 MB，不占用系统资源
- **隐私优先**：完全本地运行，数据不传输至任何服务器

## 特性

- 支持中文等多语言字符（UTF-16 编码）
- 支持中英文界面切换
- 命令行模式和交互模式
- 自动编码检测和修复
- 自动更新检查，保持最新版本
- 右键菜单集成，快速访问
- 单文件 exe 打包，无需 Python 环境

## 安装

### 方式一：使用 exe 文件（推荐）

下载 [releases](https://github.com/piratf/windows-folder-remark/releases) 中的 `windows-folder-remark.exe`，直接使用。

### 方式二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/piratf/windows-folder-remark.git
cd windows-folder-remark

# 安装依赖（无外部依赖）
pip install -e .

# 运行
python -m remark.cli --help
```

## 使用方法

### 命令行模式

```bash
# 添加备注
windows-folder-remark.exe "C:\MyFolder" "这是我的文件夹"

# 查看备注
windows-folder-remark.exe --view "C:\MyFolder"

# 删除备注
windows-folder-remark.exe --delete "C:\MyFolder"

# 检查更新
windows-folder-remark.exe --update

# 安装右键菜单
windows-folder-remark.exe --install

# 卸载右键菜单
windows-folder-remark.exe --uninstall
```

### 交互模式

```bash
# 运行后根据提示操作
windows-folder-remark.exe
```

### 右键菜单（推荐）

安装右键菜单后，可以直接在文件资源管理器中右键文件夹添加备注：

```bash
# 安装右键菜单
windows-folder-remark.exe --install
```

- **Windows 10**：右键文件夹可直接看到「添加文件夹备注」
- **Windows 11**：右键文件夹 → 点击「显示更多选项」→ 添加文件夹备注

### 自动更新

程序会在退出时自动检查更新（每 24 小时一次），如有新版本会提示是否立即更新。

也可以手动检查更新：

```bash
windows-folder-remark.exe --update
```

## 编码检测

当使用 `--view` 查看备注时，如果检测到 `desktop.ini` 文件不是标准的 UTF-16 编码，工具会提醒你：

```
警告: desktop.ini 文件编码为 utf-8，不是标准的 UTF-16。
这可能导致中文等特殊字符显示异常。
是否修复编码为 UTF-16？[Y/n]:
```

选择 `Y` 可自动修复编码。

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check .
ruff format .

# 类型检查
mypy remark/

# 本地打包 exe
python -m scripts.build
```

## 原理说明

该工具通过以下步骤实现文件夹备注：

1. 在文件夹中创建/修改 `Desktop.ini` 文件
2. 写入 `[.ShellClassInfo]` 段落和 `InfoTip` 属性
3. 使用 UTF-16 编码保存文件
4. 将 `Desktop.ini` 设置为隐藏和系统属性
5. 将文件夹设置为只读属性（使 Windows 读取 `Desktop.ini`）

参考：[Microsoft 官方文档](https://learn.microsoft.com/en-us/windows/win32/shell/how-to-customize-folders-with-desktop-ini)

## 注意事项

- 修改后可能需要几分钟才能在资源管理器中显示
- 某些文件管理器可能不支持显示文件夹备注
- 工具会修改文件夹的系统属性

## 许可证

MIT License
