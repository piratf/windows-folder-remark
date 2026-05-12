# Windows 文件夹备注工具

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

通过 `Desktop.ini` 为 Windows 文件夹添加备注。纯本地运行，用完即走。

## 特性

- 图形界面操作，无需命令行
- 支持中文等 Unicode 字符（UTF-16 LE 编码）
- 右键菜单集成，资源管理器中直接添加备注
- 无黑框——右键菜单弹出原生对话框
- 自动更新检查

## 安装

下载 [Releases](https://github.com/piratf/windows-folder-remark/releases) 中的两个 exe，放到同一目录：

| 文件 | 用途 |
|------|------|
| `windows-folder-remark.exe` | 主程序，双击打开 |
| `windows-folder-remark-context.exe` | 右键菜单，自动调用 |

## 使用方法

### 主窗口

双击 `windows-folder-remark.exe`，打开图形界面：

- 输入或浏览选择文件夹
- 查看/设置/删除备注
- 安装/卸载右键菜单
- 检查更新

### 右键菜单

在程序中点击「安装右键菜单」后：

- **Win10**：右键文件夹 → 添加文件夹备注
- **Win11**：右键文件夹 → 显示更多选项 → 添加文件夹备注

直接弹出输入框，写入后即时生效。

### 命令行（可选）

```bash
windows-folder-remark.exe --install      # 安装右键菜单
windows-folder-remark.exe --uninstall    # 卸载右键菜单
windows-folder-remark.exe --update       # 检查更新
windows-folder-remark.exe --delete "C:\Folder"  # 删除备注
```

## 原理

1. 在目标文件夹创建/修改 `Desktop.ini`
2. 写入 `[.ShellClassInfo]` + `InfoTip=<备注>`
3. UTF-16 LE 编码保存
4. 设置文件为隐藏+系统属性，文件夹为只读

参考：[Microsoft 官方文档](https://learn.microsoft.com/en-us/windows/win32/shell/how-to-customize-folders-with-desktop-ini)

## 开发

```bash
# 安装依赖
uv sync --dev

# 运行主程序
uv run remark

# 运行右键菜单
uv run python remark/cli/context_entry.py "C:\某个文件夹"

# 打包
uv run python -m scripts.build
uv run pyinstaller remark_context.spec --clean

# 测试
uv run pytest
```

## 注意事项

- 修改后可能需要一两分钟才能在资源管理器中显示
- 网络位置（NAS、映射盘）的文件夹不支持
- 部分第三方文件管理器不显示文件夹备注

## 许可证

MIT License
