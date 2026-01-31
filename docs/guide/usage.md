# 使用方法

## 命令行模式

```bash
# 添加备注
windows-folder-remark.exe "C:\MyFolder" "我的文件夹"

# 查看备注
windows-folder-remark.exe --view "C:\MyFolder"

# 删除备注
windows-folder-remark.exe --delete "C:\MyFolder"
```

## 交互模式

```bash
windows-folder-remark.exe
```

## 语言切换

```bash
# 使用中文
windows-folder-remark.exe --lang zh

# 使用英文
windows-folder-remark.exe --lang en
```

## 自动更新

程序会在退出时自动检查更新（每 24 小时一次）。

手动检查更新：

```bash
windows-folder-remark.exe --update
```
