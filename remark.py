# -*- coding: utf-8 -*
# Filename: comment.py

__author__ = 'Piratf'

import sys
import os

# 获取系统编码，确保备注不会出现乱码
defEncoding = sys.getfilesystemencoding()

# 将代码中的字符转换为系统编码
def sysEncode(content):
    return content.encode(defEncoding).decode(defEncoding)

def runCommand(command):
    # 我使用 cxfreeze 打包成 exe 程序，如果用 popen 运行时会出现没有 subprocess 模块的 bug，所以用 system 运行系统命令
    # 如果有更好的办法请联系我，感谢
    os.system(command)

def re_enterMessage(message):
    print (sysEncode(u" * " + message))
    print (sysEncode(u" * 重新输入或按 ctrl + c 退出程序") + os.linesep)

def getSettingFilePath(fpath):
    return fpath + os.sep + 'desktop.ini'

def addCommentToFolder(fpath, comment):
    content = sysEncode(u'[.ShellClassInfo]' + os.linesep + 'InfoTip=')
    # 开始设置备注信息
    settingFilePath = getSettingFilePath(fpath)
    with open(settingFilePath, 'w') as f:
        f.write(content)
        f.write(sysEncode(comment + os.linesep))

    # 添加保护
    runCommand('attrib \"' + settingFilePath + '\" +s +h')
    runCommand('attrib \"' + fpath + '\" +s ')

    print (sysEncode(u"备注添加成功~"))
    print (sysEncode(u"备注可能过一会才会显示，不要着急"))

def addComment(fpath = None, comment = None):
    inputPathMsg = sysEncode(u"请输入文件夹路径(或拖动文件夹到这里): ")
    inputCommentMsg = sysEncode(u"请输入文件夹备注:")
    
    # 输入文件夹路径
    if (fpath == None):
        fpath = input(inputPathMsg)
    
    # 判断路径是否存在文件夹
    while not os.path.isdir(fpath):
        re_enterMessage(u"你输入的不是一个文件夹路径")
        fpath = input(inputPathMsg)

    settingFilePath = getSettingFilePath(fpath)

    # 判断设置文件是否已经存在
    if (os.path.exists(settingFilePath)):
        # 去除保护属性
        runCommand('attrib \"' + settingFilePath + '\" -s -h')

    # 输入文件夹的备注
    if (comment == None):
        comment = input(inputCommentMsg)

    while not comment:
        re_enterMessage(u"备注不要为空哦")
        comment = input(inputCommentMsg)

    addCommentToFolder(fpath, comment)
    

if __name__ == '__main__':
    if len(sys.argv) == 3:
        addComment(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        addComment()
    else:
        print ('Usage .1: %s FolderPath "remark content"' % sys.argv[0])
        print ('Usage .2: %s' % sys.argv[0])
