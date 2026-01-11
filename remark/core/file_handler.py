# -*- coding: utf-8 -*-

"""
文件备注处理器 - 使用 NTFS 替代数据流(ADS)
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


class FileCommentHandler(CommentHandler):
    """文件备注处理器"""
    
    def _get_ads_path(self, file_path):
        """获取 ADS 路径"""
        return file_path + ':comment'
    
    def set_comment(self, file_path, comment):
        """设置文件备注"""
        if not os.path.isfile(file_path):
            print(sys_encode(u"路径不是文件: ") + file_path)
            return False
        
        if len(comment) > MAX_COMMENT_LENGTH:
            print(sys_encode(u"备注长度超过限制，最大长度为 ") + str(MAX_COMMENT_LENGTH) + sys_encode(u" 个字符"))
            comment = comment[:MAX_COMMENT_LENGTH]
        
        try:
            ads_path = self._get_ads_path(file_path)
            with open(ads_path, 'w', encoding='utf-8') as f:
                f.write(comment)
            run_command('attrib \"' + ads_path + '\" +h')
            print(sys_encode(u"备注添加成功"))
            return True
        except Exception as e:
            print(sys_encode(u"设置文件备注失败: ") + str(e))
            return False
    
    def get_comment(self, file_path):
        """获取文件备注"""
        try:
            ads_path = self._get_ads_path(file_path)
            if not os.path.exists(ads_path):
                return None
            with open(ads_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    
    def delete_comment(self, file_path):
        """删除文件备注"""
        try:
            ads_path = self._get_ads_path(file_path)
            if os.path.exists(ads_path):
                os.remove(ads_path)
                print(sys_encode(u"备注删除成功"))
                return True
            else:
                print(sys_encode(u"该文件没有备注"))
                return True
        except Exception as e:
            print(sys_encode(u"删除文件备注失败: ") + str(e))
            return False
    
    def supports(self, path):
        """检查是否支持该路径"""
        return os.path.isfile(path)