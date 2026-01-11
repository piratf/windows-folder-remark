# -*- coding: utf-8 -*-

"""
文件夹备注处理器 - 使用 desktop.ini
"""

import os
import subprocess
from remark.core.base import CommentHandler
from remark.utils.encoding import sys_encode
from remark.utils.constants import MAX_COMMENT_LENGTH


def run_command(command):
    """执行系统命令"""
    try:
        result = subprocess.call(command, shell=True)
        if result != 0:
            print(sys_encode(u"命令执行失败，错误码: ") + str(result))
        return result == 0
    except Exception as e:
        print(sys_encode(u"命令执行异常: ") + str(e))
        return False


class FolderCommentHandler(CommentHandler):
    """文件夹备注处理器"""
    
    def _get_desktop_ini_path(self, folder_path):
        """获取 desktop.ini 路径"""
        return os.path.join(folder_path, 'desktop.ini')
    
    def set_comment(self, folder_path, comment):
        """设置文件夹备注"""
        if not os.path.isdir(folder_path):
            print(sys_encode(u"路径不是文件夹: ") + folder_path)
            return False
        
        if len(comment) > MAX_COMMENT_LENGTH:
            print(sys_encode(u"备注长度超过限制，最大长度为 ") + str(MAX_COMMENT_LENGTH) + sys_encode(u" 个字符"))
            comment = comment[:MAX_COMMENT_LENGTH]
        
        desktop_ini = self._get_desktop_ini_path(folder_path)
        
        try:
            if os.path.exists(desktop_ini):
                run_command('attrib \"' + desktop_ini + '\" -s -h')
            
            content = sys_encode(u'[.ShellClassInfo]' + os.linesep + 'InfoTip=')
            with open(desktop_ini, 'w', encoding=sys.getfilesystemencoding()) as f:
                f.write(content)
                f.write(sys_encode(comment + os.linesep))
            
            if not run_command('attrib \"' + desktop_ini + '\" +s +h'):
                print(sys_encode(u"设置文件属性失败"))
                return False
            if not run_command('attrib \"' + folder_path + '\" +s '):
                print(sys_encode(u"设置文件夹属性失败"))
                return False
            
            print(sys_encode(u"备注添加成功"))
            return True
        except IOError as e:
            print(sys_encode(u"文件写入失败: ") + str(e))
            return False
    
    def get_comment(self, folder_path):
        """获取文件夹备注"""
        desktop_ini = self._get_desktop_ini_path(folder_path)
        
        if not os.path.exists(desktop_ini):
            return None
        
        try:
            with open(desktop_ini, 'r', encoding=sys.getfilesystemencoding()) as f:
                content = f.read()
                if 'InfoTip=' in content:
                    start = content.index('InfoTip=') + 8
                    end = content.find(os.linesep, start)
                    if end == -1:
                        end = len(content)
                    return content[start:end].strip()
        except IOError:
            pass
        return None
    
    def delete_comment(self, folder_path):
        """删除文件夹备注"""
        desktop_ini = self._get_desktop_ini_path(folder_path)
        
        if not os.path.exists(desktop_ini):
            print(sys_encode(u"该文件夹没有备注"))
            return True
        
        if not run_command('attrib \"' + desktop_ini + '\" -s -h'):
            print(sys_encode(u"去除文件属性失败"))
            return False
        
        try:
            os.remove(desktop_ini)
            print(sys_encode(u"备注删除成功"))
            return True
        except OSError as e:
            print(sys_encode(u"删除文件失败: ") + str(e))
            return False
    
    def supports(self, path):
        """检查是否支持该路径"""
        return os.path.isdir(path)