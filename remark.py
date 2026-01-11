# -*- coding: utf-8 -*
# Filename: comment.py

__author__ = 'Piratf'

# Modified By CraikLee 2024-01-26

import sys
import os
import subprocess

# 获取系统编码，确保备注不会出现乱码
defEncoding = sys.getfilesystemencoding()


# 将代码中的字符转换为系统编码
def sys_encode(content):
    try:
        return content.encode(defEncoding).decode(defEncoding)
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        print(sys_encode(u"编码转换错误: ") + str(e))
        return content


def run_command(command):
    try:
        result = subprocess.call(command, shell=True)
        if result != 0:
            print(sys_encode(u"命令执行失败，错误码: ") + str(result))
        return result == 0
    except Exception as e:
        print(sys_encode(u"命令执行异常: ") + str(e))
        return False


def re_enter_message(message):
    print(sys_encode(u" * " + message))
    print(sys_encode(u" * 继续处理或按 ctrl + c 退出程序") + os.linesep)


def get_setting_file_path(dir_path):
    return os.path.join(dir_path, 'desktop.ini')


def update_folder_comment(dir_path, comment):
    content = sys_encode(u'[.ShellClassInfo]' + os.linesep + 'InfoTip=')
    # 开始设置备注信息
    setting_file_path = get_setting_file_path(dir_path)
    try:
        with open(setting_file_path, 'w', encoding=defEncoding) as f:
            f.write(content)
            f.write(sys_encode(comment + os.linesep))
    except IOError as e:
        print(sys_encode(u"文件写入失败: ") + str(e))
        return False

    # 添加保护
    if not run_command('attrib \"' + setting_file_path + '\" +s +h'):
        print(sys_encode(u"设置文件属性失败"))
        return False
    if not run_command('attrib \"' + dir_path + '\" +s '):
        print(sys_encode(u"设置文件夹属性失败"))
        return False

    print(sys_encode(u"备注添加成功~"))
    print(sys_encode(u"备注可能过一会才会显示，不要着急"))
    return True


def add_comment(dir_path=None, comment=None):
    input_path_msg = sys_encode(u"请输入文件夹路径(或拖动文件夹到这里): ")
    input_comment_msg = sys_encode(u"请输入文件夹备注:")

    # 输入文件夹路径
    if dir_path is None:
        dir_path_temp = input(input_path_msg)
        #print(dir_path_temp)
        #dir_path = "r"+dir_path
        dir_path = dir_path_temp.replace('\"', '').strip()
	
    # 判断路径是否存在文件夹
    while not os.path.isdir(dir_path):
        #print(dir_path)        
        re_enter_message(u"你输入的不是一个文件夹路径")
        dir_path_temp = input(input_path_msg)
        dir_path = dir_path_temp.replace('\"', '').strip()

    setting_file_path = get_setting_file_path(dir_path)

    # 判断设置文件是否已经存在
    if os.path.exists(setting_file_path):
        # 去除保护属性
        run_command('attrib \"' + setting_file_path + '\" -s -h')

    # 输入文件夹的备注
    if comment is None:
        comment = input(input_comment_msg)

    while not comment:
        re_enter_message(u"备注不要为空哦")
        comment = input(input_comment_msg)

    if not update_folder_comment(dir_path, comment):
        print(sys_encode(u"备注添加失败"))


if __name__ == '__main__':
    if len(sys.argv) == 3:
        add_comment(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        while True:
            try:
                add_comment()
            except KeyboardInterrupt:
                print(sys_encode(u" ❤ 感谢使用"))
                break
            re_enter_message("成功完成一次备注")
    else:
        print('Usage .1: %s [folder path] [content]' % sys.argv[0])
        print('Usage .2: %s' % sys.argv[0])
