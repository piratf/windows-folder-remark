"""
Minimal entry point for right-click context menu.

Imports NOTHING from remark/ to keep the exe small and fast.
All desktop.ini logic is inlined (~60 lines).
"""

import codecs
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

DESKTOP_INI_ENCODING = "utf-16"
SECTION = "[.ShellClassInfo]"
KEY = "InfoTip"


def _ini_path(folder):
    return os.path.join(folder, "desktop.ini")


def read_remark(folder_path: str) -> str | None:
    p = _ini_path(folder_path)
    if not os.path.exists(p):
        return None
    for enc in ["utf-16", "utf-16-le", "utf-8-sig", "utf-8", "gbk", "mbcs"]:
        try:
            with codecs.open(p, "r", encoding=enc) as f:
                content = f.read()
            if SECTION not in content:
                continue
            if KEY in content:
                start = content.index(KEY + "=") + len(KEY + "=")
                end = len(content)
                for term in ["\r\n", "\n", "\r"]:
                    pos = content.find(term, start)
                    if pos != -1 and pos < end:
                        end = pos
                        break
                return content[start:end].strip() or None
            return None
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            break
    return None


def write_remark(folder_path: str, remark: str) -> bool:
    p = _ini_path(folder_path)
    try:
        if os.path.exists(p):
            _clear_attrs(p)
            try:
                with codecs.open(p, "r", encoding=DESKTOP_INI_ENCODING) as f:
                    content = f.read()
                lines = content.splitlines()
                new_lines = []
                found = False
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith(KEY + "=") or stripped.startswith(KEY + " "):
                        new_lines.append(KEY + "=" + remark)
                        found = True
                    else:
                        new_lines.append(line)
                if not found:
                    inserted = False
                    for i, line in enumerate(new_lines):
                        if line.strip().startswith("[.ShellClassInfo]"):
                            new_lines.insert(i + 1, KEY + "=" + remark)
                            inserted = True
                            break
                    if not inserted:
                        new_lines = [SECTION, KEY + "=" + remark]
                new_content = "\r\n".join(new_lines)
            except (UnicodeDecodeError, UnicodeError):
                # can't read, overwrite
                new_content = SECTION + "\r\n" + KEY + "=" + remark + "\r\n"
        else:
            new_content = SECTION + "\r\n" + KEY + "=" + remark + "\r\n"

        with codecs.open(p, "w", encoding=DESKTOP_INI_ENCODING) as f:
            f.write(new_content)
        _set_attrs(p)
        _set_folder_readonly(folder_path)
        return True
    except Exception:
        return False


def delete_remark(folder_path: str) -> bool:
    p = _ini_path(folder_path)
    if not os.path.exists(p):
        return True
    try:
        _clear_attrs(p)
        with codecs.open(p, "r", encoding=DESKTOP_INI_ENCODING) as f:
            content = f.read()
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(KEY + "=") or stripped.startswith(KEY + " "):
                continue
            new_lines.append(line)
        has_content = any(
            l.strip() and not l.strip().startswith("[.ShellClassInfo]") for l in new_lines
        )
        if not has_content:
            os.remove(p)
            return True
        new_content = "\r\n".join(new_lines)
        with codecs.open(p, "w", encoding=DESKTOP_INI_ENCODING) as f:
            f.write(new_content)
        _set_attrs(p)
        return True
    except Exception:
        return False


def _clear_attrs(path):
    subprocess.call('attrib -s -h "' + path + '"', shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _set_attrs(path):
    subprocess.call('attrib +h +s "' + path + '"', shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _set_folder_readonly(path):
    subprocess.call('attrib +r "' + path + '"', shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ── GUI ────────────────────────────────────────────────────────

def show_dialog(folder_path: str):
    current = read_remark(folder_path)

    root = tk.Tk()
    root.title("添加文件夹备注")
    root.resizable(False, False)

    pad = ttk.Frame(root, padding="16 10 16 16")
    pad.pack(fill=tk.BOTH, expand=True)
    pad.columnconfigure(1, weight=1)

    # folder path
    ttk.Label(pad, text="文件夹:", font=("", 9, "bold")).grid(
        row=0, column=0, sticky=tk.W, pady=(0, 2))
    path_entry = ttk.Entry(pad, width=55)
    path_entry.insert(0, folder_path)
    path_entry.configure(state="readonly")
    path_entry.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))

    # current remark
    ttk.Label(pad, text="当前备注:", font=("", 9, "bold")).grid(
        row=2, column=0, sticky=tk.W, pady=(0, 2))
    cur_entry = ttk.Entry(pad, width=55, state="readonly")
    cur_entry.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
    if current:
        cur_entry.configure(state="normal")
        cur_entry.insert(0, current)
        cur_entry.configure(state="readonly")

    # new remark
    ttk.Label(pad, text="新备注:", font=("", 9, "bold")).grid(
        row=4, column=0, sticky=tk.W, pady=(0, 2))
    remark_var = tk.StringVar()
    if current:
        remark_var.set(current)
    remark_entry = ttk.Entry(pad, textvariable=remark_var, width=55)
    remark_entry.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(0, 12))
    remark_entry.focus_set()
    if current:
        remark_entry.select_range(0, tk.END)

    # buttons
    btn_frame = ttk.Frame(pad)
    btn_frame.grid(row=6, column=0, columnspan=2)

    def on_ok():
        r = remark_var.get().strip()
        if not r:
            messagebox.showwarning("提示", "备注不能为空", parent=root)
            return
        if write_remark(folder_path, r):
            root.destroy()
        else:
            messagebox.showerror("错误", "写入失败", parent=root)

    def on_del():
        if not messagebox.askyesno("确认", "确定要删除备注吗？", parent=root):
            return
        if delete_remark(folder_path):
            root.destroy()
        else:
            messagebox.showerror("错误", "删除失败", parent=root)

    ttk.Button(btn_frame, text="确定", command=on_ok, width=12).pack(
        side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_frame, text="删除", command=on_del, width=12).pack(
        side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_frame, text="取消", command=root.destroy, width=12).pack(
        side=tk.LEFT)

    root.bind("<Return>", lambda e: on_ok())
    root.bind("<Escape>", lambda e: root.destroy())

    # center
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    root.mainloop()


# ── entry ──────────────────────────────────────────────────────

def main():
    # get folder path from args
    args = sys.argv[1:]
    path = " ".join(args).strip().strip('"')
    if not path or not os.path.isdir(path):
        # try to show an error
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", "无效的文件夹路径")
        root.destroy()
        sys.exit(1)

    show_dialog(path)


if __name__ == "__main__":
    main()
