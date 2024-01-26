# -*- coding: utf-8 -*
# Filename: comment.py

__author__ = 'Piratf'

# Modified By CraikLee 2024-01-26

import sys
import os

# 获取系统编码，确保备注不会出现乱码
defEncoding = sys.getfilesystemencoding()


# 将代码中的字符转换为系统编码
def sys_encode(content):
    return content.encode(defEncoding).decode(defEncoding)


def run_command(command):
    os.system(command)


def re_enter_message(message):
    print(sys_encode(u" * " + message))
    print(sys_encode(u" * 继续处理或按 ctrl + c 退出程序") + os.linesep)


def get_setting_file_path(dir_path):
    return dir_path + os.sep + 'desktop.ini'


def update_folder_comment(dir_path, comment):
    content = sys_encode(u'[.ShellClassInfo]' + os.linesep + 'InfoTip=')
    # 开始设置备注信息
    setting_file_path = get_setting_file_path(dir_path)
    with open(setting_file_path, 'w') as f:
        f.write(content)
        f.write(sys_encode(comment + os.linesep))

    # 添加保护
    run_command('attrib \"' + setting_file_path + '\" +s +h')
    run_command('attrib \"' + dir_path + '\" +s ')

    print(sys_encode(u"备注添加成功~"))
    print(sys_encode(u"备注可能过一会才会显示，不要着急"))


def add_comment(dir_path=None, comment=None):
    input_path_msg = sys_encode(u"请输入文件夹路径(或拖动文件夹到这里): ")
    input_comment_msg = sys_encode(u"请输入文件夹备注:")

    # 输入文件夹路径
    if dir_path is None:
        dir_path_temp = input(input_path_msg)
        #print(dir_path_temp)
        #dir_path = "r"+dir_path
        dir_path = dir_path_temp.replace('\"', '')
	
    # 判断路径是否存在文件夹
    while not os.path.isdir(dir_path):
        #print(dir_path)        
        re_enter_message(u"你输入的不是一个文件夹路径")
        dir_path_temp = input(input_path_msg)
        dir_path = dir_path_temp.replace('\"', '')

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

    update_folder_comment(dir_path, comment)


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
