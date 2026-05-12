"""
主 GUI 窗口
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from remark.core.folder_handler import FolderCommentHandler
from remark.utils import registry
from remark.utils.constants import MAX_COMMENT_LENGTH
from remark.utils.platform import check_platform
from remark.utils.updater import (
    check_updates_manual,
    create_update_script,
    download_update,
    get_executable_path,
    trigger_update,
)


def get_version():
    try:
        from importlib.metadata import version
        return version("windows-folder-remark")
    except Exception:
        return "unknown"


FONT = ("Microsoft YaHei UI", 11)
FONT_BOLD = ("Microsoft YaHei UI", 11, "bold")
FONT_SMALL = ("Microsoft YaHei UI", 9)


class MainWindow:
    def __init__(self):
        self.handler = FolderCommentHandler()
        self.root = tk.Tk()
        self.root.title("Windows 文件夹备注")
        self.root.resizable(True, True)
        self.root.minsize(600, 460)

        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            style.theme_use("clam")

        style.configure("Title.TLabel", font=FONT_BOLD, foreground="#1a1a1a")
        style.configure("Hint.TLabel", font=FONT_SMALL, foreground="#888888")
        style.configure("Status.TLabel", font=FONT_SMALL, foreground="#666666",
                        background="#f0f0f0", padding=(8, 4))

        self._build_ui()
        self._center_window()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        # main container
        main = ttk.Frame(self.root, padding="18 14 18 12")
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1)

        row = 0

        # ── 文件夹 ──
        ttk.Label(main, text="文件夹", style="Title.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1

        path_frame = ttk.Frame(main)
        path_frame.grid(row=row, column=0, sticky=tk.EW, pady=(0, 6))
        path_frame.columnconfigure(0, weight=1)
        self.folder_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.folder_var, font=FONT)
        self.path_entry.grid(row=0, column=0, sticky=tk.EW)
        self.path_entry.bind("<KeyRelease>", lambda e: self._on_path_changed())
        ttk.Button(path_frame, text="浏览…", command=self._browse_folder,
                   width=8).grid(row=0, column=1, padx=(6, 0))
        row += 1

        # ── 当前备注 ──
        ttk.Label(main, text="当前备注", style="Title.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=(8, 4))
        row += 1
        self.current_var = tk.StringVar(value="")
        cur_entry = ttk.Entry(main, textvariable=self.current_var,
                              font=FONT, state="readonly")
        cur_entry.grid(row=row, column=0, sticky=tk.EW, pady=(0, 6))
        row += 1

        # ── 新备注 ──
        ttk.Label(main, text="新备注", style="Title.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=(8, 4))
        row += 1
        self.remark_var = tk.StringVar()
        self.remark_entry = ttk.Entry(main, textvariable=self.remark_var, font=FONT)
        self.remark_entry.grid(row=row, column=0, sticky=tk.EW, pady=(0, 6))
        self.remark_entry.bind("<Return>", lambda e: self._set_remark())
        row += 1

        ttk.Label(main, text=f"备注最长 {MAX_COMMENT_LENGTH} 个字符", style="Hint.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=(0, 8))
        row += 1

        # ── 操作按钮 ──
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 10))
        ttk.Button(btn_frame, text="设置备注", command=self._set_remark,
                   width=13).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="查看备注", command=self._view_remark,
                   width=13).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="删除备注", command=self._delete_remark,
                   width=13).pack(side=tk.LEFT)
        row += 1

        # ── 工具 ──
        ttk.Label(main, text="工具", style="Title.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=(8, 4))
        row += 1

        tool_frame = ttk.Frame(main)
        tool_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        self.install_btn = ttk.Button(tool_frame, text="安装右键菜单",
                                      command=self._install_menu)
        self.install_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.uninstall_btn = ttk.Button(tool_frame, text="卸载右键菜单",
                                        command=self._uninstall_menu)
        self.uninstall_btn.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(tool_frame, text="检查更新",
                   command=self._check_update).pack(side=tk.LEFT)
        row += 1

        # ── 状态栏 ──
        status_frame = tk.Frame(main, bg="#f0f0f0", height=26)
        status_frame.grid(row=row, column=0, sticky=tk.EW, pady=(12, 0))
        status_frame.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(status_frame, textvariable=self.status_var,
                 font=FONT_SMALL, fg="#555555", bg="#f0f0f0",
                 anchor=tk.W, padx=8, pady=2).grid(row=0, column=0, sticky=tk.EW)
        tk.Label(status_frame, text=f"v{get_version()}",
                 font=FONT_SMALL, fg="#aaaaaa", bg="#f0f0f0",
                 anchor=tk.E, padx=8, pady=2).grid(row=0, column=1, sticky=tk.E)

        self._refresh_menu_button_state()

    # ── actions ──────────────────────────────────────────────────

    def _get_path(self):
        return self.folder_var.get().strip().strip('"')

    def _browse_folder(self):
        d = filedialog.askdirectory(title="选择文件夹")
        if d:
            self.folder_var.set(d)
            self._on_path_changed()

    def _on_path_changed(self):
        path = self._get_path()
        if not path or not os.path.isdir(path):
            self.current_var.set("")
            return
        remark = self.handler.get_comment(path)
        self.current_var.set(remark or "（无备注）")

    def _validate_folder(self):
        path = self._get_path()
        if not path:
            messagebox.showwarning("提示", "请先选择一个文件夹", parent=self.root)
            return None
        if not os.path.exists(path):
            messagebox.showwarning("提示", "路径不存在", parent=self.root)
            return None
        if not os.path.isdir(path):
            messagebox.showwarning("提示", "这不是一个文件夹", parent=self.root)
            return None
        return path

    def _set_remark(self):
        path = self._validate_folder()
        if not path:
            return
        remark = self.remark_var.get().strip()
        if not remark:
            messagebox.showwarning("提示", "备注不能为空", parent=self.root)
            return
        if len(remark) > MAX_COMMENT_LENGTH:
            remark = remark[:MAX_COMMENT_LENGTH]

        self.status_var.set("正在设置备注…")
        self.root.update_idletasks()
        if self.handler.set_comment(path, remark):
            self.current_var.set(remark)
            self.remark_var.set("")
            self.status_var.set("备注设置成功")
        else:
            self.status_var.set("设置失败")

    def _view_remark(self):
        path = self._validate_folder()
        if not path:
            return
        remark = self.handler.get_comment(path)
        if remark:
            self.current_var.set(remark)
            messagebox.showinfo("文件夹备注", f"文件夹：{path}\n\n备注：{remark}", parent=self.root)
        else:
            self.current_var.set("（无备注）")
            messagebox.showinfo("文件夹备注", "该文件夹没有备注", parent=self.root)

    def _delete_remark(self):
        path = self._validate_folder()
        if not path:
            return
        if not messagebox.askyesno("确认", "确定要删除该文件夹的备注吗？", parent=self.root):
            return
        if self.handler.delete_comment(path):
            self.current_var.set("（无备注）")
            self.status_var.set("备注已删除")
        else:
            self.status_var.set("删除失败")

    def _install_menu(self):
        self.status_var.set("正在安装右键菜单…")
        self.root.update_idletasks()
        if registry.install_context_menu():
            self.status_var.set("右键菜单已安装")
            messagebox.showinfo(
                "安装成功",
                "右键菜单已安装。\n\n"
                "Win10：右键文件夹即可看到「添加文件夹备注」\n"
                "Win11：右键文件夹 → 显示更多选项 → 添加文件夹备注",
                parent=self.root,
            )
        else:
            self.status_var.set("安装失败")
            messagebox.showerror("错误", "右键菜单安装失败", parent=self.root)
        self._refresh_menu_button_state()

    def _uninstall_menu(self):
        self.status_var.set("正在卸载右键菜单…")
        self.root.update_idletasks()
        if registry.uninstall_context_menu():
            self.status_var.set("右键菜单已卸载")
            messagebox.showinfo("卸载成功", "右键菜单已卸载", parent=self.root)
        else:
            self.status_var.set("卸载失败")
            messagebox.showerror("错误", "右键菜单卸载失败", parent=self.root)
        self._refresh_menu_button_state()

    def _refresh_menu_button_state(self):
        installed = registry.is_context_menu_installed()
        if installed:
            self.install_btn.configure(state="disabled")
            self.uninstall_btn.configure(state="normal")
        else:
            self.install_btn.configure(state="normal")
            self.uninstall_btn.configure(state="disabled")

    def _check_update(self):
        self.status_var.set("正在检查更新…")
        self.root.update_idletasks()

        def _run():
            try:
                info = check_updates_manual(get_version())
            except Exception:
                info = None
            self.root.after(0, lambda: self._on_update_result(info))

        threading.Thread(target=_run, daemon=True).start()

    def _on_update_result(self, info):
        if info is None:
            self.status_var.set("已是最新版本")
            messagebox.showinfo("检查更新", "已是最新版本", parent=self.root)
            return

        tag = info.get("tag_name", "")
        body = info.get("body", "")[:300]
        url = info.get("html_url", "")

        want = messagebox.askyesno(
            "发现新版本",
            f"新版本：{tag}\n\n更新内容：\n{body}\n\n是否下载并更新？",
            parent=self.root,
        )
        if not want:
            return

        self.status_var.set("正在下载更新…")
        self.root.update_idletasks()

        def _download():
            try:
                import tempfile

                new_exe = os.path.join(
                    tempfile.gettempdir(), f"windows-folder-remark-{tag}.exe"
                )
                download_update(info["download_url"], new_exe)
                old_exe = get_executable_path()
                script_path = create_update_script(old_exe, new_exe)
                trigger_update(script_path)
                self.root.after(0, lambda: self.root.destroy())
            except Exception as e:
                self.root.after(0, lambda: self._on_download_error(str(e), url))

        threading.Thread(target=_download, daemon=True).start()

    def _on_download_error(self, error, url):
        messagebox.showerror(
            "更新失败",
            f"下载失败：{error}\n\n请手动下载：{url}",
            parent=self.root,
        )
        self.status_var.set("更新失败")

    def _on_close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def run_main_window():
    root = tk.Tk()
    root.withdraw()
    if not check_platform():
        root.destroy()
        sys.exit(1)
    root.destroy()
    app = MainWindow()
    app.run()
