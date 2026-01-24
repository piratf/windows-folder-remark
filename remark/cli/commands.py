"""
命令行接口
"""

import argparse
import os
import sys

from remark.core.folder_handler import FolderCommentHandler
from remark.utils.platform import check_platform


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

    def _validate_folder(self, path):
        """验证路径是否为文件夹"""
        if not os.path.exists(path):
            print("路径不存在:", path)
            return False
        if not self.handler.supports(path):
            print("路径不是文件夹:", path)
            return False
        return True

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

    def view_comment(self, path):
        """查看备注"""
        if self._validate_folder(path):
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
        print("  --delete <路径>    删除备注")
        print("  --view <路径>      查看备注")
        print("  --help, -h         显示帮助信息")
        print("示例:")
        print(' [添加备注] python remark.py "C:\\\\MyFolder" "这是我的文件夹"')
        print(' [删除备注] python remark.py --delete "C:\\\\MyFolder"')
        print(' [查看当前备注] python remark.py --view "C:\\\\MyFolder"')

    def run(self, argv=None):
        """运行 CLI"""
        if not check_platform():
            sys.exit(1)

        parser = argparse.ArgumentParser(description="Windows 文件夹备注工具", add_help=False)
        parser.add_argument("path", nargs="?", help="文件夹路径")
        parser.add_argument("comment", nargs="?", help="备注内容")
        parser.add_argument("--delete", metavar="PATH", help="删除备注")
        parser.add_argument("--view", metavar="PATH", help="查看备注")
        parser.add_argument("--help", "-h", action="store_true", help="显示帮助信息")

        args = parser.parse_args(argv)

        if args.help:
            self.show_help()
        elif args.delete:
            self.delete_comment(args.delete)
        elif args.view:
            self.view_comment(args.view)
        elif args.path and args.comment:
            self.add_comment(args.path, args.comment)
        elif not args.path and not args.comment:
            self.interactive_mode()
        else:
            self.show_help()


def main():
    """主入口"""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print("发生错误:", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
