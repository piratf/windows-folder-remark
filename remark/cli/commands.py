"""
命令行接口
"""

import argparse
import os
import sys
import tempfile
import threading
import urllib.error

from remark.core.folder_handler import FolderCommentHandler
from remark.gui import remark_dialog
from remark.i18n import _ as _, set_language
from remark.utils import registry
from remark.utils.path_resolver import find_candidates
from remark.utils.platform import check_platform
from remark.utils.updater import (
    check_updates_auto,
    check_updates_manual,
    create_update_script,
    download_update,
    get_executable_path,
    should_check_update,
    trigger_update,
)


def get_version():
    """动态获取版本号"""
    try:
        from importlib.metadata import version

        return version("windows-folder-remark")
    except Exception:
        return "unknown"


class CLI:
    """命令行接口"""

    def __init__(self):
        self.handler = FolderCommentHandler()
        self.pending_update = None
        self._update_check_done = threading.Event()
        # 先检查缓存，只有在需要检查时才启动后台线程
        if should_check_update():
            self._start_update_checker()
        else:
            self._update_check_done.set()  # 不需要检查，直接标记完成

    def _validate_folder(self, path: str) -> bool:
        """验证路径是否为文件夹"""
        if not os.path.exists(path):
            print(_("Path does not exist: {path}").format(path=path))
            return False
        if not self.handler.supports(path):
            print(_("Path is not a folder: {path}").format(path=path))
            return False
        return True

    def _start_update_checker(self):
        """后台线程检查更新，不阻塞主流程"""
        thread = threading.Thread(target=self._run_update_check, daemon=True)
        thread.start()

    def _run_update_check(self):
        """实际执行更新检查"""
        try:
            self.pending_update = check_updates_auto(get_version())
        finally:
            self._update_check_done.set()

    def check_update_now(self) -> bool:
        """强制检查更新（用于 --update 命令，绕过缓存）

        Returns:
            True 如果有新版本，False 否则
        """
        print(_("Current version: {version}").format(version=get_version()))
        print(_("Checking for updates..."))

        update = check_updates_manual(get_version())

        if update:
            print(_("\nNew version found: {tag_name}").format(tag_name=update["tag_name"]))
            print(_("Update notes: {notes}").format(notes=update["body"][:300]))
            print(_("Full changelog: {url}").format(url=update["html_url"]))
            response = input(_("\nUpdate now? [Y/n]: ")).lower()
            if response in ("", "y", "yes"):
                self._perform_update(update)
            return True
        else:
            print(_("Already at the latest version"))
            return False

    def _wait_for_update_check(self, timeout: float = 2.0) -> None:
        """等待后台检测完成

        Args:
            timeout: 超时时间（秒）
        """
        self._update_check_done.wait(timeout=timeout)

    def _prompt_update(self) -> None:
        """提示用户有新版本可用"""
        update = self.pending_update
        if update is None:
            return
        print(
            _("\nNew version available: {tag_name} (Current version: {version})").format(
                tag_name=update["tag_name"], version=get_version()
            )
        )
        print(_("Update notes: {notes}").format(notes=update["body"][:200]))
        print(_("Full changelog: {url}").format(url=update["html_url"]))
        response = input(_("Update now? [Y/n]: ")).lower()
        if response in ("", "y", "yes"):
            self._perform_update(update)

    def _perform_update(self, update: dict) -> None:
        """执行更新流程"""
        try:
            print(_("Downloading new version..."))
            # 下载到临时目录
            new_exe = os.path.join(
                tempfile.gettempdir(), f"windows-folder-remark-{update['tag_name']}.exe"
            )
            download_update(update["download_url"], new_exe)

            print(_("Download complete, preparing update..."))
            old_exe = get_executable_path()
            script_path = create_update_script(old_exe, new_exe)

            print(_("Update program has started, the application will exit..."))
            print(_("Please wait a few moments, the update will complete automatically."))
            trigger_update(script_path)
            sys.exit(0)
        except urllib.error.URLError as e:
            err_msg = str(e)
            if "closed connection" in err_msg.lower() or "connection reset" in err_msg.lower():
                print(_("Download failed: Connection reset by server"))
                print(_("Please try again later, or visit the following link to download manually:"))
                print(f"  {update['html_url']}")
            elif "timeout" in err_msg.lower():
                print(_("Download failed: Request timeout"))
                print(_("Please check your network connection, or visit the following link to download manually:"))
                print(f"  {update['html_url']}")
            elif "no route to host" in err_msg.lower() or "hostname" in err_msg.lower():
                print(_("Download failed: Unable to connect to server"))
                print(_("Please check your network connection, or visit the following link to download manually:"))
                print(f"  {update['html_url']}")
            else:
                print(_("Download failed, please check your network or download manually"))
                print(f"  {update['html_url']}")
        except Exception as e:
            print(_("Update failed: {error}").format(error=e))
            print(_("Manual download: {url}").format(url=update["html_url"]))

    def add_comment(self, path, comment):
        """添加备注"""
        if self._validate_folder(path):
            return self.handler.set_comment(path, comment)
        return False

    def delete_comment(self, path):
        """删除备注"""
        if self._validate_folder(path):
            return self.handler.delete_comment(path)
        return False

    def install_menu(self) -> bool:
        """安装右键菜单"""
        if registry.install_context_menu():
            print(_("Right-click menu installed successfully"))
            print("")
            print(_("Usage Instructions:"))
            print(_("  Windows 10: Right-click folder to see 'Add Folder Remark'"))
            print(_("  Windows 11: Right-click folder → Click 'Show more options' → Add Folder Remark"))
            return True
        else:
            print(_("Right-click menu installation failed"))
            return False

    def uninstall_menu(self) -> bool:
        """卸载右键菜单"""
        if registry.uninstall_context_menu():
            print(_("Right-click menu uninstalled"))
            return True
        else:
            print(_("Right-click menu uninstallation failed"))
            return False

    def gui_mode(self, folder_path: str) -> bool:
        """GUI 模式（右键菜单调用）"""
        if not self._validate_folder(folder_path):
            return False

        # 显示对话框
        comment = remark_dialog.show_remark_dialog(folder_path)
        if comment:
            result = self.add_comment(folder_path, comment)
            return result is not False
        return False

    def view_comment(self, path: str) -> None:
        """查看备注"""
        if self._validate_folder(path):
            # 检查 desktop.ini 编码
            from remark.storage.desktop_ini import DesktopIniHandler

            if DesktopIniHandler.exists(path):
                desktop_ini_path = DesktopIniHandler.get_path(path)
                detected_encoding, is_utf16 = DesktopIniHandler.detect_encoding(desktop_ini_path)
                if not is_utf16:
                    print(
                        _(
                            "Warning: desktop.ini file encoding is {encoding}, not standard UTF-16."
                        ).format(encoding=detected_encoding or _("unknown"))
                    )
                    print(_("This may cause Chinese and other special characters to display abnormally."))

                    # 询问是否修复
                    while True:
                        response = input(_("Fix encoding to UTF-16? [Y/n]: ")).strip().lower()
                        if response in ("", "y", "yes"):
                            if DesktopIniHandler.fix_encoding(desktop_ini_path, detected_encoding):
                                print(_("Fixed to UTF-16 encoding"))
                            else:
                                print(_("Failed to fix encoding"))
                            break
                        elif response in ("n", "no"):
                            print(_("Skip encoding fix"))
                            break
                        else:
                            print(_("Please enter Y or n"))
                    print()  # 空行分隔

            comment = self.handler.get_comment(path)
            if comment:
                print(_("Current remark: {remark}").format(remark=comment))
            else:
                print(_("This folder has no remark"))

    def interactive_mode(self) -> None:
        """交互模式"""
        version = get_version()
        print(_("Windows Folder Remark Tool v{version}").format(version=version))
        print(_("Tip: Press Ctrl + C to exit") + os.linesep)

        input_path_msg = _("Enter folder path (or drag here): ")
        input_comment_msg = _("Enter remark:")

        while True:
            try:
                path = input(input_path_msg).replace('"', "").strip()

                if not os.path.exists(path):
                    print(_("Path does not exist, please re-enter"))
                    continue

                if not os.path.isdir(path):
                    print(_("This is a 'file', currently only supports adding remarks to 'folders'"))
                    continue

                comment = input(input_comment_msg)
                while not comment:
                    print(_("Remark cannot be empty"))
                    comment = input(input_comment_msg)

                self.add_comment(path, comment)

            except KeyboardInterrupt:
                print(_(" ❤ Thank you for using"))
                break
            print(os.linesep + _("Continue processing or press Ctrl + C to exit") + os.linesep)

    def show_help(self) -> None:
        """显示帮助信息"""
        print(_("Windows Folder Remark Tool"))
        print(_("Usage:"))
        print(_("  Interactive mode: python remark.py"))
        print(_("  Command line mode: python remark.py [options] [arguments]"))
        print(_("Options:"))
        print(_("  --install          Install right-click menu"))
        print(_("  --uninstall        Uninstall right-click menu"))
        print(_("  --update           Check for updates"))
        print(_("  --gui <path>        GUI mode (called from right-click menu)"))
        print(_("  --delete <path>     Delete remark"))
        print(_("  --view <path>        View remark"))
        print(_("  --help, -h         Show help information"))
        print(_("Examples:"))
        print(_(' [Add remark] python remark.py "C:\\\\MyFolder" "My Folder"'))
        print(_(' [Delete remark] python remark.py --delete "C:\\\\MyFolder"'))
        print(_(' [View current remark] python remark.py --view "C:\\\\MyFolder"'))
        print(_(" [Install right-click menu] python remark.py --install"))
        print(_(" [Check for updates] python remark.py --update"))

    def _select_from_multiple_candidates(
        self, candidates: list, show_remaining: bool = False
    ) -> tuple[str, list[str]] | None:
        """
        从多个候选路径中选择

        Args:
            candidates: 候选路径列表，每个元素为 (path, remaining, type)
            show_remaining: 是否显示剩余参数（备注内容）

        Returns:
            (path_str, remaining) 或 None 如果用户取消
        """

        # 转换 candidates 中的 Path 对象为字符串
        str_candidates: list[tuple[str, list[str], str]] = []
        for path, remaining, path_type in candidates:
            str_candidates.append((str(path), remaining, path_type))

        print("检测到多个可能的路径，请选择:")
        for i, (p, r, t) in enumerate(str_candidates, 1):
            type_mark = " [文件]" if t == "file" else ""
            print(f"\n[{i}] {p}{type_mark}")
            if show_remaining and r:
                print(f"    剩余备注: {' '.join(r)}")
            elif not show_remaining:
                print("    (将查看现有备注)")
        print("\n[0] 取消")

        while True:
            choice = input(f"\n请选择 [0-{len(str_candidates)}]: ").strip()
            if choice == "0":
                return None
            if choice.isdigit() and 1 <= int(choice) <= len(str_candidates):
                path, remaining, path_type = str_candidates[int(choice) - 1]
                if path_type == "file":
                    print("\n错误: 这是一个文件，工具只能为文件夹设置备注，请重新选择")
                    continue
                return path, remaining
            print("无效选择，请重试")

    def _handle_ambiguous_path(self, args_list: list[str]) -> tuple[str | None, str | None]:
        """
        处理模糊路径，返回 (最终路径, 备注内容)

        Args:
            args_list: 位置参数列表

        Returns:
            (path, comment) 或 (None, None) 如果用户取消
        """

        candidates = find_candidates(args_list)

        if not candidates:
            print(_("Error: Path does not exist or not quoted"))
            print(_("Hint: Use quotes when path contains spaces"))
            print(_('  windows-folder-remark "C:\\\\My Documents" "Remark content"'))
            return None, None

        if len(candidates) == 1:
            path, remaining, path_type = candidates[0]
            print(_("Detected path: {path}").format(path=path))

            if path_type == "file":
                print(_("Error: This is a file, the tool can only set remarks for folders"))
                return None, None

            if remaining:
                comment = " ".join(remaining)
                print(_("Remark content: {remark}").format(remark=comment))
            else:
                print(_("(Will view existing remark)"))

            if input(_("Continue? [Y/n]: ")).lower() in ("", "y", "yes"):
                return str(path), " ".join(remaining) if remaining else None

            return None, None

        result = self._select_from_multiple_candidates(candidates, show_remaining=True)
        if result:
            path_str, remaining = result
            return path_str, " ".join(remaining) if remaining else None
        return None, None

    def _resolve_path_from_ambiguous_args(self, args_list: list[str]) -> str | None:
        """
        从可能被空格分割的参数列表中解析出有效路径

        适用于 --view, --delete, --gui 等只接收路径的命令。

        Args:
            args_list: 可能包含路径片段的参数列表

        Returns:
            解析出的路径字符串，如果无法解析则返回 None
        """
        candidates = find_candidates(args_list)

        if not candidates:
            return None

        if len(candidates) == 1:
            path, remaining, path_type = candidates[0]
            if path_type == "folder":
                return str(path)
            else:
                print(_("Error: This is a file, the tool can only set remarks for folders"))
                return None

        result = self._select_from_multiple_candidates(candidates, show_remaining=False)
        if result:
            return result[0]
        return None

    def run(self, argv=None) -> None:
        """运行 CLI"""
        if not check_platform():
            sys.exit(1)

        parser = argparse.ArgumentParser(description="Windows 文件夹备注工具", add_help=False)
        parser.add_argument("args", nargs="*", help="位置参数（路径和备注）")
        parser.add_argument("--install", action="store_true", help="安装右键菜单")
        parser.add_argument("--uninstall", action="store_true", help="卸载右键菜单")
        parser.add_argument("--update", action="store_true", help="检查更新")
        parser.add_argument("--gui", metavar="PATH", help="GUI 模式（右键菜单调用）")
        parser.add_argument("--delete", metavar="PATH", help="删除备注")
        parser.add_argument("--view", metavar="PATH", help="查看备注")
        parser.add_argument("--help", "-h", action="store_true", help="显示帮助信息")
        parser.add_argument("--lang", "-L", metavar="LANG", help="设置语言 (en, zh_CN)", dest="lang")

        args = parser.parse_args(argv)

        # 设置语言
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
                print("错误: 路径不存在或未使用引号")
        elif args.delete:
            path = self._resolve_path_from_ambiguous_args([args.delete, *args.args])
            if path:
                self.delete_comment(path)
            else:
                print("错误: 路径不存在或未使用引号")
        elif args.view:
            path = self._resolve_path_from_ambiguous_args([args.view, *args.args])
            if path:
                self.view_comment(path)
            else:
                print("错误: 路径不存在或未使用引号")
        elif args.args:
            # 处理位置参数
            path, comment = self._handle_ambiguous_path(args.args)
            if path:
                if comment:
                    self.add_comment(path, comment)
                else:
                    self.view_comment(path)
            else:
                # 用户取消或解析失败，显示帮助
                self.show_help()
        else:
            # 无参数，进入交互模式
            self.interactive_mode()


def main() -> None:
    """主入口"""
    cli = CLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print(_("\nOperation cancelled"))
        sys.exit(0)
    except Exception as e:
        print(_("An error occurred: {error}").format(error=str(e)))
        sys.exit(1)
    finally:
        # 等待后台检测完成（最多等待 2 秒）
        cli._wait_for_update_check(timeout=2.0)
        # 退出前检查更新
        if cli.pending_update:
            cli._prompt_update()


if __name__ == "__main__":
    main()
