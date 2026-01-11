# -*- coding: utf-8 -*-

"""
命令行接口
"""

import os
import sys
import argparse
from remark.core.file_handler import FileCommentHandler
from remark.core.folder_handler import FolderCommentHandler
from remark.utils.encoding import sys_encode
from remark.utils.platform import check_platform


class CLI:
    """命令行接口"""
    
    def __init__(self):
        self.file_handler = FileCommentHandler()
        self.folder_handler = FolderCommentHandler()
    
    def _get_handler(self, path):
        """根据路径类型获取处理器"""
        if self.file_handler.supports(path):
            return self.file_handler
        elif self.folder_handler.supports(path):
            return self.folder_handler
        return None
    
    def add_comment(self, path, comment):
        """添加备注"""
        if not os.path.exists(path):
            print(sys_encode(u"路径不存在: ") + path)
            return False
        
        handler = self._get_handler(path)
        if handler:
            return handler.set_comment(path, comment)
        else:
            print(sys_encode(u"不支持的路径类型"))
            return False
    
    def delete_comment(self, path):
        """删除备注"""
        if not os.path.exists(path):
            print(sys_encode(u"路径不存在: ") + path)
            return False
        
        handler = self._get_handler(path)
        if handler:
            return handler.delete_comment(path)
        else:
            print(sys_encode(u"不支持的路径类型"))
            return False
    
    def view_comment(self, path):
        """查看备注"""
        if not os.path.exists(path):
            print(sys_encode(u"路径不存在: ") + path)
            return
        
        handler = self._get_handler(path)
        if handler:
            comment = handler.get_comment(path)
            if comment:
                print(sys_encode(u"当前备注: ") + comment)
            else:
                print(sys_encode(u"该对象没有备注"))
        else:
            print(sys_encode(u"不支持的路径类型"))
    
    def interactive_mode(self):
        """交互模式"""
        print(sys_encode(u"Windows 文件/文件夹备注工具"))
        print(sys_encode(u"提示: 按 Ctrl + C 退出程序") + os.linesep)
        
        input_path_msg = sys_encode(u"请输入文件或文件夹路径(或拖动到这里): ")
        input_comment_msg = sys_encode(u"请输入备注:")
        
        while True:
            try:
                path = input(input_path_msg).replace('\"', '').strip()
                
                if not os.path.exists(path):
                    print(sys_encode(u"路径不存在，请重新输入"))
                    continue
                
                comment = input(input_comment_msg)
                while not comment:
                    print(sys_encode(u"备注不要为空哦"))
                    comment = input(input_comment_msg)
                
                self.add_comment(path, comment)
                
            except KeyboardInterrupt:
                print(sys_encode(u" ❤ 感谢使用"))
                break
            print(os.linesep + sys_encode(u"继续处理或按 Ctrl + C 退出程序") + os.linesep)
    
    def show_help(self):
        """显示帮助信息"""
        print(sys_encode(u"Windows 文件/文件夹备注工具"))
        print(sys_encode(u"使用方法:"))
        print(sys_encode(u"  交互模式: python remark.py"))
        print(sys_encode(u"  命令行模式: python remark.py [选项] [参数]"))
        print(sys_encode(u"选项:"))
        print(sys_encode(u"  --delete <路径>    删除备注"))
        print(sys_encode(u"  --view <路径>      查看备注"))
        print(sys_encode(u"  --help, -h         显示帮助信息"))
        print(sys_encode(u"示例:"))
        print(sys_encode(u" [添加备注] python remark.py \"C:\\\\MyFolder\" \"这是我的文件夹\""))
        print(sys_encode(u" [添加备注] python remark.py \"C:\\\\MyFile.txt\" \"这是我的文件\""))
        print(sys_encode(u" [删除备注] python remark.py --delete \"C:\\\\MyFolder\""))
        print(sys_encode(u" [查看当前备注] python remark.py --view \"C:\\\\MyFolder\""))
    
    def run(self, argv=None):
        """运行 CLI"""
        if not check_platform():
            sys.exit(1)
        
        parser = argparse.ArgumentParser(
            description=sys_encode(u"Windows 文件/文件夹备注工具"),
            add_help=False
        )
        parser.add_argument('path', nargs='?', help=sys_encode(u"文件或文件夹路径"))
        parser.add_argument('comment', nargs='?', help=sys_encode(u"备注内容"))
        parser.add_argument('--delete', metavar='PATH', help=sys_encode(u"删除备注"))
        parser.add_argument('--view', metavar='PATH', help=sys_encode(u"查看备注"))
        parser.add_argument('--help', '-h', action='store_true', help=sys_encode(u"显示帮助信息"))
        
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
    cli = CLI()
    cli.run()


if __name__ == '__main__':
    main()