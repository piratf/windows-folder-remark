"""
命令行接口 — 所有输出通过 GUI (messagebox)，兼容 console=False 打包
"""

import argparse
import os
import sys
import tempfile
import tkinter as tk
import urllib.error
from tkinter import messagebox, ttk

from remark.core.folder_handler import FolderCommentHandler
from remark.gui import remark_dialog
from remark.i18n import _ as _, set_language
from remark.utils import registry
from remark.utils.path_resolver import find_candidates
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


class CLI:
    def __init__(self):
        self.handler = FolderCommentHandler()

    def _validate_folder(self, path: str) -> bool:
        if not os.path.exists(path):
            messagebox.showwarning(_("Warning"), _("Path does not exist: {path}").format(path=path))
            return False
        if not self.handler.supports(path):
            messagebox.showwarning(_("Warning"), _("Path is not a folder: {path}").format(path=path))
            return False
        return True

    # ── actions ──────────────────────────────────────────────

    def add_comment(self, path, comment):
        if self._validate_folder(path):
            if self.handler.set_comment(path, comment):
                messagebox.showinfo(_("Success"), _("Remark has been set"))
                return True
        return False

    def delete_comment(self, path):
        if self._validate_folder(path):
            if self.handler.delete_comment(path):
                messagebox.showinfo(_("Success"), _("Remark deleted"))
                return True
        return False

    def install_menu(self):
        if registry.install_context_menu():
            messagebox.showinfo(
                _("Success"),
                _("Right-click menu installed.\n")
                + _("Win10: Right-click folder → 'Add Folder Remark'.\n")
                + _("Win11: Right-click → Show more options → Add Folder Remark."),
            )
        else:
            messagebox.showerror(_("Error"), _("Right-click menu installation failed"))

    def uninstall_menu(self):
        if registry.uninstall_context_menu():
            messagebox.showinfo(_("Success"), _("Right-click menu uninstalled"))
        else:
            messagebox.showerror(_("Error"), _("Right-click menu uninstallation failed"))

    def gui_mode(self, folder_path: str):
        if not self._validate_folder(folder_path):
            return
        comment = remark_dialog.show_remark_dialog(folder_path)
        if comment:
            self.handler.set_comment(folder_path, comment)

    def view_comment(self, path: str):
        if not self._validate_folder(path):
            return
        remark = self.handler.get_comment(path)
        if remark:
            messagebox.showinfo(_("Folder Remark"), f"{path}\n\n{remark}")
        else:
            messagebox.showinfo(_("Folder Remark"), _("This folder has no remark"))

    def check_update_now(self):
        version_str = get_version()
        info = check_updates_manual(version_str)

        if info is None:
            messagebox.showinfo(_("Update"), _("Already at the latest version"))
            return

        tag = info.get("tag_name", "")
        body = info.get("body", "")[:300]
        url = info.get("html_url", "")

        want = messagebox.askyesno(
            _("Update Available"),
            _("Current version: {cur}\nNew version: {tag}").format(cur=version_str, tag=tag)
            + "\n\n"
            + _("Update notes: {notes}").format(notes=body)
            + "\n\n"
            + _("Download and update now?"),
        )
        if not want:
            return

        try:
            new_exe = os.path.join(tempfile.gettempdir(), f"windows-folder-remark-{tag}.exe")
            download_update(info["download_url"], new_exe)
            old_exe = get_executable_path()
            script_path = create_update_script(old_exe, new_exe)
            trigger_update(script_path)
            sys.exit(0)
        except urllib.error.URLError as e:
            err_msg = str(e)
            if "closed connection" in err_msg.lower() or "connection reset" in err_msg.lower():
                messagebox.showerror(_("Update Failed"), _("Download failed: Connection reset by server"))
            elif "timeout" in err_msg.lower():
                messagebox.showerror(_("Update Failed"), _("Download failed: Request timeout"))
            else:
                messagebox.showerror(_("Update Failed"), _("Download failed: {error}").format(error=err_msg))
        except Exception as e:
            messagebox.showerror(_("Update Failed"), _("Update failed: {error}\nManual download: {url}").format(error=e, url=url))

    # ── help ─────────────────────────────────────────────────

    def show_help(self):
        msg = (
            _("Windows Folder Remark Tool")
            + "\n\n"
            + _("Usage:")
            + "\n"
            + _('  remark "C:\\Folder" "Remark"    - Add remark')
            + "\n"
            + _("  remark --gui      <path>    - GUI dialog (right-click)")
            + "\n"
            + _("  remark --delete   <path>    - Delete remark")
            + "\n"
            + _("  remark --view     <path>    - View remark")
            + "\n"
            + _("  remark --install            - Install context menu")
            + "\n"
            + _("  remark --uninstall          - Uninstall context menu")
            + "\n"
            + _("  remark --update             - Check for updates")
            + "\n"
            + _("  remark                      - Open main window")
        )
        messagebox.showinfo(_("Help"), msg)

    # ── ambiguous path resolution ───────────────────────────

    def _select_from_multiple_candidates(self, candidates: list) -> tuple[str, list] | None:
        str_candidates = [(str(p), r, t) for p, r, t in candidates]

        dialog = tk.Toplevel(self._root)
        dialog.title(_("Select Path"))
        dialog.resizable(False, False)
        dialog.transient(self._root)
        dialog.grab_set()

        lines = [_("Multiple possible paths detected. Please select:")]
        for i, (p, r, t) in enumerate(str_candidates, 1):
            tag = _("[File]") if t == "file" else ""
            lines.append(f"\n[{i}] {p} {tag}")
        lines.append(f"\n[0] {_('Cancel')}")

        result = {"choice": None}

        frame = ttk.Frame(dialog, padding="16")
        frame.pack(fill=tk.BOTH, expand=True)

        msg_label = tk.Label(frame, text="\n".join(lines), justify=tk.LEFT, font=("Consolas", 10))
        msg_label.pack(pady=(0, 10))

        entry_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=entry_var, width=10)
        entry.pack()
        entry.focus_set()

        def on_ok():
            c = entry_var.get().strip()
            if c == "0":
                dialog.destroy()
                return
            if c.isdigit() and 1 <= int(c) <= len(str_candidates):
                result["choice"] = int(c) - 1
                dialog.destroy()
                return
            messagebox.showwarning(_("Warning"), _("Invalid choice"), parent=dialog)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))
        ttk.Button(btn_frame, text=_("OK"), command=on_ok, width=10).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frame, text=_("Cancel"), command=dialog.destroy, width=10).pack(side=tk.LEFT)

        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"+{(sw - 400) // 2}+{(sh - 300) // 2}")
        dialog.wait_window()

        if result["choice"] is not None:
            p, r, _ = str_candidates[result["choice"]]
            return p, r
        return None

    def _handle_ambiguous_path(self, args_list: list[str]) -> tuple[str | None, str | None]:
        candidates = find_candidates(args_list)
        if not candidates:
            messagebox.showerror(
                _("Error"),
                _("Path does not exist or not quoted.")
                + "\n"
                + _('Hint: Use quotes when path contains spaces.\n  remark "C:\\My Documents" "Remark"'),
            )
            return None, None

        if len(candidates) == 1:
            path, remaining, path_type = candidates[0]
            if path_type == "file":
                messagebox.showerror(_("Error"), _("This is a file, the tool can only set remarks for folders"))
                return None, None
            comment = " ".join(remaining) if remaining else None
            return str(path), comment

        result = self._select_from_multiple_candidates(candidates)
        if result:
            p, r = result
            return p, " ".join(r) if r else None
        return None, None

    def _resolve_path_from_ambiguous_args(self, args_list: list[str]) -> str | None:
        candidates = find_candidates(args_list)
        if not candidates:
            return None

        if len(candidates) == 1:
            path, remaining, path_type = candidates[0]
            if path_type == "folder":
                return str(path)
            else:
                messagebox.showerror(_("Error"), _("This is a file, the tool can only set remarks for folders"))
                return None

        result = self._select_from_multiple_candidates(candidates)
        if result:
            return result[0]
        return None

    # ── router ──────────────────────────────────────────────

    def run(self, argv=None):
        parser = argparse.ArgumentParser(description="Windows Folder Remark", add_help=False)
        parser.add_argument("args", nargs="*", help="Positional arguments (path and remark)")
        parser.add_argument("--install", action="store_true", help="Install context menu")
        parser.add_argument("--uninstall", action="store_true", help="Uninstall context menu")
        parser.add_argument("--update", action="store_true", help="Check for updates")
        parser.add_argument("--gui", metavar="PATH", help="GUI mode (right-click menu)")
        parser.add_argument("--delete", metavar="PATH", help="Delete remark")
        parser.add_argument("--view", metavar="PATH", help="View remark")
        parser.add_argument("--help", "-h", action="store_true", help="Show help")
        parser.add_argument("--lang", "-L", metavar="LANG", dest="lang", help="Set language (en, zh)")

        args = parser.parse_args(argv)

        # Hidden root window for messagebox dialogs
        self._root = tk.Tk()
        self._root.withdraw()

        if not check_platform():
            self._root.destroy()
            sys.exit(1)

        if args.lang:
            set_language(args.lang)

        if args.help:
            self.show_help()
        elif args.install:
            self.install_menu()
        elif args.uninstall:
            self.uninstall_menu()
        elif args.update:
            self.check_update_now()
            sys.exit(0)
        elif args.gui:
            path = self._resolve_path_from_ambiguous_args([args.gui, *args.args])
            if path:
                self.gui_mode(path)
            else:
                messagebox.showerror(
                    _("Error"),
                    _("Path does not exist.")
                    + "\n"
                    + _('Hint: Use quotes for paths with spaces.\n  remark --gui "C:\\My Documents"'),
                )
        elif args.delete:
            path = self._resolve_path_from_ambiguous_args([args.delete, *args.args])
            if path:
                self.delete_comment(path)
            else:
                messagebox.showerror(
                    _("Error"),
                    _("Path does not exist.")
                    + "\n"
                    + _('Hint: Use quotes for paths with spaces.\n  remark --delete "C:\\My Documents"'),
                )
        elif args.view:
            path = self._resolve_path_from_ambiguous_args([args.view, *args.args])
            if path:
                self.view_comment(path)
            else:
                messagebox.showerror(
                    _("Error"),
                    _("Path does not exist.")
                    + "\n"
                    + _('Hint: Use quotes for paths with spaces.\n  remark --view "C:\\My Documents"'),
                )
        elif args.args:
            path, comment = self._handle_ambiguous_path(args.args)
            if path:
                if comment:
                    self.add_comment(path, comment)
                else:
                    self.view_comment(path)
        else:
            # 无参数 → 启动主 GUI 窗口
            self._root.destroy()
            from remark.gui.main_window import run_main_window
            run_main_window()
            return

        self._root.destroy()


def main():
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    cli = CLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        try:
            messagebox.showerror(_("Error"), _("An error occurred: {error}").format(error=str(e)))
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
