"""
命令行接口
"""

import argparse
import os
import sys
import tempfile
import threading

import requests

from remark.core.folder_handler import FolderCommentHandler
from remark.gui import remark_dialog
from remark.utils import registry
from remark.utils.path_resolver import find_candidates
from remark.utils.platform import check_platform
from remark.utils.updater import (
    check_for_updates,
    create_update_script,
    download_update,
    get_executable_path,
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
        self._check_update_in_background()

    def _validate_folder(self, path):
        """验证路径是否为文件夹"""
        if not os.path.exists(path):
            print("路径不存在:", path)
            return False
        if not self.handler.supports(path):
            print("路径不是文件夹:", path)
            return False
        return True

    def _check_update_in_background(self):
        """后台线程检查更新，不阻塞主流程"""
        thread = threading.Thread(target=self._do_check_update, daemon=True)
        thread.start()

    def _do_check_update(self):
        """实际执行更新检查"""
        try:
            self.pending_update = check_for_updates(get_version())
        finally:
            self._update_check_done.set()

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
        print(f"\n发现新版本: {update['tag_name']} (当前版本: {get_version()})")
        print(f"更新说明: {update['body'][:200]}...")
        print(f"完整更新日志: {update['html_url']}")
        response = input("是否立即更新? [Y/n]: ").lower()
        if response in ("", "y", "yes"):
            self._perform_update(update)

    def _perform_update(self, update: dict) -> None:
        """执行更新流程"""
        try:
            print("正在下载新版本...")
            # 下载到临时目录
            new_exe = os.path.join(
                tempfile.gettempdir(), f"windows-folder-remark-{update['tag_name']}.exe"
            )
            download_update(update["download_url"], new_exe)

            print("下载完成，准备更新...")
            old_exe = get_executable_path()
            script_path = create_update_script(old_exe, new_exe)

            print("更新程序已启动，程序即将退出...")
            print("请等待几秒钟，更新将自动完成。")
            trigger_update(script_path)
            sys.exit(0)
        except requests.RequestException:
            print("下载失败，请检查网络连接或手动下载更新")
        except Exception as e:
            print(f"更新失败: {e}")

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
            print("右键菜单安装成功")
            print("")
            print("使用说明:")
            print("  Windows 10: 右键文件夹可直接看到「添加文件夹备注」")
            print("  Windows 11: 右键文件夹 → 点击「显示更多选项」→ 添加文件夹备注")
            return True
        else:
            print("右键菜单安装失败")
            return False

    def uninstall_menu(self) -> bool:
        """卸载右键菜单"""
        if registry.uninstall_context_menu():
            print("右键菜单已卸载")
            return True
        else:
            print("右键菜单卸载失败")
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

    def view_comment(self, path):
        """查看备注"""
        if self._validate_folder(path):
            # 检查 desktop.ini 编码
            from remark.storage.desktop_ini import DesktopIniHandler

            if DesktopIniHandler.exists(path):
                desktop_ini_path = DesktopIniHandler.get_path(path)
                detected_encoding, is_utf16 = DesktopIniHandler.detect_encoding(desktop_ini_path)
                if not is_utf16:
                    print(
                        f"警告: desktop.ini 文件编码为 {detected_encoding or '未知'}，不是标准的 UTF-16。"
                    )
                    print("这可能导致中文等特殊字符显示异常。")

                    # 询问是否修复
                    while True:
                        response = input("是否修复编码为 UTF-16？[Y/n]: ").strip().lower()
                        if response in ("", "y", "yes"):
                            if DesktopIniHandler.fix_encoding(desktop_ini_path, detected_encoding):
                                print("✓ 已修复为 UTF-16 编码")
                            else:
                                print("✗ 修复失败")
                            break
                        elif response in ("n", "no"):
                            print("跳过编码修复")
                            break
                        else:
                            print("请输入 Y 或 n")
                    print()  # 空行分隔

            comment = self.handler.get_comment(path)
            if comment:
                print("当前备注:", comment)
            else:
                print("该文件夹没有备注")

    def interactive_mode(self):
        """交互模式"""
        version = get_version()
        print("Windows 文件夹备注工具 v" + version)
        print("提示: 按 Ctrl + C 退出程序" + os.linesep)

        input_path_msg = "请输入文件夹路径(或拖动到这里): "
        input_comment_msg = "请输入备注:"

        while True:
            try:
                path = input(input_path_msg).replace('"', "").strip()

                if not os.path.exists(path):
                    print("路径不存在，请重新输入")
                    continue

                if not os.path.isdir(path):
                    print('这是一个"文件"，当前仅支持为"文件夹"添加备注')
                    continue

                comment = input(input_comment_msg)
                while not comment:
                    print("备注不要为空哦")
                    comment = input(input_comment_msg)

                self.add_comment(path, comment)

            except KeyboardInterrupt:
                print(" ❤ 感谢使用")
                break
            print(os.linesep + "继续处理或按 Ctrl + C 退出程序" + os.linesep)

    def show_help(self):
        """显示帮助信息"""
        print("Windows 文件夹备注工具")
        print("使用方法:")
        print("  交互模式: python remark.py")
        print("  命令行模式: python remark.py [选项] [参数]")
        print("选项:")
        print("  --install          安装右键菜单")
        print("  --uninstall        卸载右键菜单")
        print("  --gui <路径>       GUI 模式（右键菜单调用）")
        print("  --delete <路径>    删除备注")
        print("  --view <路径>      查看备注")
        print("  --help, -h         显示帮助信息")
        print("示例:")
        print(' [添加备注] python remark.py "C:\\\\MyFolder" "这是我的文件夹"')
        print(' [删除备注] python remark.py --delete "C:\\\\MyFolder"')
        print(' [查看当前备注] python remark.py --view "C:\\\\MyFolder"')
        print(" [安装右键菜单] python remark.py --install")

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
            print("错误: 路径不存在或未使用引号")
            print("提示: 路径包含空格时请使用引号")
            print('  windows-folder-remark "C:\\\\My Documents" "备注内容"')
            return None, None

        if len(candidates) == 1:
            path, remaining, path_type = candidates[0]
            print(f"检测到路径: {path}")

            if path_type == "file":
                print("错误: 这是一个文件，工具只能为文件夹设置备注")
                return None, None

            if remaining:
                comment = " ".join(remaining)
                print(f"备注内容: {comment}")
            else:
                print("(将查看现有备注)")

            if input("是否继续? [Y/n]: ").lower() in ("", "y", "yes"):
                return str(path), " ".join(remaining) if remaining else None

            return None, None

        # 多个候选，让用户选择
        print("检测到多个可能的路径，请选择:")
        for i, (p, r, t) in enumerate(candidates, 1):
            type_mark = " [文件]" if t == "file" else ""
            print(f"\n[{i}] 路径: {p}{type_mark}")
            if r:
                print(f"    剩余备注: {' '.join(r)}")
            else:
                print("    (将查看现有备注)")
        print("\n[0] 取消")

        while True:
            choice = input(f"\n请选择 [0-{len(candidates)}]: ").strip()
            if choice == "0":
                return None, None
            if choice.isdigit() and 1 <= int(choice) <= len(candidates):
                path, remaining, path_type = candidates[int(choice) - 1]
                if path_type == "file":
                    print("\n错误: 这是一个文件，工具只能为文件夹设置备注，请重新选择")
                    continue
                return str(path), " ".join(remaining) if remaining else None
            print("无效选择，请重试")

    def run(self, argv=None):
        """运行 CLI"""
        if not check_platform():
            sys.exit(1)

        parser = argparse.ArgumentParser(description="Windows 文件夹备注工具", add_help=False)
        parser.add_argument("args", nargs="*", help="位置参数（路径和备注）")
        parser.add_argument("--install", action="store_true", help="安装右键菜单")
        parser.add_argument("--uninstall", action="store_true", help="卸载右键菜单")
        parser.add_argument("--gui", metavar="PATH", help="GUI 模式（右键菜单调用）")
        parser.add_argument("--delete", metavar="PATH", help="删除备注")
        parser.add_argument("--view", metavar="PATH", help="查看备注")
        parser.add_argument("--help", "-h", action="store_true", help="显示帮助信息")

        args = parser.parse_args(argv)

        if args.help:
            self.show_help()
        elif args.install:
            self.install_menu()
        elif args.uninstall:
            self.uninstall_menu()
        elif args.gui:
            self.gui_mode(args.gui)
        elif args.delete:
            self.delete_comment(args.delete)
        elif args.view:
            self.view_comment(args.view)
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


def main():
    """主入口"""
    cli = CLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print("发生错误:", str(e))
        sys.exit(1)
    finally:
        # 等待后台检测完成（最多等待 2 秒）
        cli._wait_for_update_check(timeout=2.0)
        # 退出前检查更新
        if cli.pending_update:
            cli._prompt_update()


if __name__ == "__main__":
    main()
