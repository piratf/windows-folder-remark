"""集成测试专用 fixtures"""

import codecs

import pytest


@pytest.fixture
def utf16_encoded_file(tmp_path):
    """创建 UTF-16 编码的测试文件"""
    file_path = tmp_path / "utf16_test.ini"
    content = "[.ShellClassInfo]\r\nInfoTip=UTF-16 测试\r\n"

    with codecs.open(str(file_path), "w", encoding="utf-16") as f:
        f.write(content)

    return str(file_path)


@pytest.fixture
def utf8_encoded_file(tmp_path):
    """创建 UTF-8 编码的测试文件"""
    file_path = tmp_path / "utf8_test.ini"
    content = "[.ShellClassInfo]\r\nInfoTip=UTF-8 测试\r\n"

    with open(str(file_path), "w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path)
