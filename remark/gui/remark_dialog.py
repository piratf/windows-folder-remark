"""
备注输入对话框

使用 tkinter 实现的简单 GUI 对话框，用于右键菜单集成。
"""

import tkinter as tk
from tkinter import messagebox, ttk

from remark.core.folder_handler import FolderCommentHandler


def show_remark_dialog(folder_path: str) -> str | None:
    """
    显示备注输入对话框

    界面:
    - 标题: "添加文件夹备注"
    - 文件夹路径显示 (只读)
    - 当前备注显示 (如果有)
    - 备注输入框
    - 确定/取消按钮

    Args:
        folder_path: 文件夹完整路径

    Returns:
        用户输入的备注内容（非空字符串），用户点击取消返回 None
    """
    root = tk.Tk()
    root.title("添加文件夹备注")

    # 设置窗口大小和居中
    window_width = 500
    window_height = 250
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # 禁止调整窗口大小
    root.resizable(False, False)

    # 使用 ttk 样式
    style = ttk.Style()
    style.theme_use("clam")

    # 结果存储
    result: dict[str, str | None] = {"comment": None}

    # =============================================================================
    # 界面元素
    # =============================================================================

    # 主框架
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 文件夹路径标签
    path_label = ttk.Label(main_frame, text="文件夹路径:")
    path_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

    path_entry = ttk.Entry(main_frame, width=60)
    path_entry.insert(0, folder_path)
    path_entry.configure(state="readonly")
    path_entry.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 15))

    # 当前备注显示（如果存在）
    handler = FolderCommentHandler()
    current_comment = handler.get_comment(folder_path)

    if current_comment:
        current_label = ttk.Label(main_frame, text="当前备注:")
        current_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))

        current_value = ttk.Entry(main_frame, width=60)
        current_value.insert(0, current_comment)
        current_value.configure(state="readonly")
        current_value.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0, 15))

        next_row = 4
    else:
        next_row = 2

    # 备注输入标签
    comment_label = ttk.Label(main_frame, text="备注内容:")
    comment_label.grid(row=next_row, column=0, sticky=tk.W, pady=(0, 5))

    # 备注输入框
    comment_entry = ttk.Entry(main_frame, width=60)
    if current_comment:
        comment_entry.insert(0, current_comment)
    comment_entry.grid(row=next_row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 20))

    # 按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=next_row + 2, column=0, columnspan=2, sticky=tk.EW)

    # 确定按钮
    def on_ok():
        comment = comment_entry.get().strip()
        if not comment:
            messagebox.showwarning("警告", "备注不能为空")
            return
        result["comment"] = comment
        root.destroy()

    def on_cancel():
        result["comment"] = None
        root.destroy()

    ok_button = ttk.Button(button_frame, text="确定", command=on_ok, width=10)
    ok_button.pack(side=tk.RIGHT, padx=(5, 0))

    # 取消按钮
    cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel, width=10)
    cancel_button.pack(side=tk.RIGHT)

    # =============================================================================
    # 键盘快捷键
    # =============================================================================

    root.bind("<Return>", lambda e: on_ok())
    root.bind("<Escape>", lambda e: on_cancel())

    # =============================================================================
    # 焦点设置
    # =============================================================================

    comment_entry.focus_set()
    if current_comment:
        # 如果有现有备注，全选文本方便修改
        comment_entry.select_range(0, tk.END)

    # =============================================================================
    # 运行
    # =============================================================================

    root.wait_window()
    return result["comment"]
