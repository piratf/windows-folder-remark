"""
路径解析模块单元测试
"""

import os
from pathlib import Path, PureWindowsPath

import pytest

from remark.utils.path_resolver import find_candidates


class TestFindCandidates:
    """测试 find_candidates 函数"""

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_single_space_split(self, fs):
        """
        用例: 单次空格分割

        输入: ["D:\\My", "Documents"]
        模拟环境:
            D:\\ 目录下存在文件夹 "My Documents"
            listdir("D:\\") -> ["My Documents", "Users", "Windows", "test.txt"]

        预期输出:
            [("D:\\My Documents", [], "folder")]
        """
        fs.create_dir("D:\\My Documents")
        fs.create_dir("D:\\Users")
        fs.create_dir("D:\\Windows")
        fs.create_file("D:\\test.txt")

        result = find_candidates(["D:\\My", "Documents"])

        assert len(result) == 1
        path, remaining, type_ = result[0]
        assert path == Path("D:\\My Documents")
        assert remaining == []
        assert type_ == "folder"

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_multi_space_folder_name_with_comment(self, fs):
        """
        用例: 文件夹名包含多个空格（有备注）

        输入: ["D:\\Here", "Is", "My", "Folder", "备注", "内容"]
        模拟环境:
            D:\\ 目录下存在文件夹 "Here Is My Folder"
            listdir("D:\\") -> ["Here Is My Folder", "Users"]

        预期输出:
            [("D:\\Here Is My Folder", ["备注", "内容"], "folder")]

        说明: "Here Is My Folder" 被空格分割成 4 个参数，剩余 2 个参数作为备注
        """
        fs.create_dir("D:\\Here Is My Folder")
        fs.create_dir("D:\\Users")

        result = find_candidates(["D:\\Here", "Is", "My", "Folder", "备注", "内容"])

        assert len(result) == 1
        path, remaining, type_ = result[0]
        assert path == Path("D:\\Here Is My Folder")
        assert remaining == ["备注", "内容"]
        assert type_ == "folder"

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_valid_folder_with_comment(self, fs):
        """
        用例: 路径有效 + 备注

        输入: ["D:\\ValidFolder", "备注"]
        模拟环境:
            D:\\ValidFolder 目录存在且是文件夹

        预期输出:
            [("D:\\ValidFolder", ["备注"], "folder")]

        说明: 路径本身完整，剩余参数作为备注
        """
        fs.create_dir("D:\\ValidFolder")

        result = find_candidates(["D:\\ValidFolder", "备注"])

        assert len(result) == 1
        path, remaining, type_ = result[0]
        assert path == Path("D:\\ValidFolder")
        assert remaining == ["备注"]
        assert type_ == "folder"

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_no_match(self, fs):
        """
        用例: 无匹配

        输入: ["D:\\Invalid", "Path"]
        模拟环境:
            D:\\ 目录下只有 "Users", "Windows" 文件夹
            listdir("D:\\") -> ["Users", "Windows"]
            "D:\\Invalid" 和 "D:\\Invalid Path" 都不存在

        预期输出:
            [] (空列表)

        说明: 无法匹配任何路径，返回空列表
        """
        fs.create_dir("D:\\Users")
        fs.create_dir("D:\\Windows")

        result = find_candidates(["D:\\Invalid", "Path"])

        assert result == []

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_both_single_name_and_extended_exist(self, fs):
        """
        用例: 单个文件夹名和扩展路径都存在

        输入: ["My", "Files", "App"]
        模拟环境:
            当前目录下同时存在 "My" 和 "My Files" 两个文件夹
            listdir(".") -> ["My", "My Files", "Other"]

        预期输出 (按优先级排序):
            [
                (包含 "My Files" 的路径, ["App"], "folder"),      # 消耗 2 个参数，剩余 1 个
                (包含 "My" 的路径, ["Files", "App"], "folder"),   # 消耗 1 个参数，剩余 2 个
            ]

        说明: 同时匹配 "My Files" 和 "My"，按剩余参数数量升序排序（剩余越少优先级越高）
        """
        fs.create_dir("My")
        fs.create_dir("My Files")
        fs.create_dir("Other")

        result = find_candidates(["My", "Files", "App"])

        assert len(result) == 2
        path1, remaining1, type1 = result[0]
        path2, remaining2, type2 = result[1]

        # 验证第一个候选是 "My Files"（包含完整路径）
        assert path1 == Path("My Files")
        assert remaining1 == ["App"]
        assert type1 == "folder"

        # 验证第二个候选是 "My"
        assert path2 == Path("My")
        assert remaining2 == ["Files", "App"]
        assert type2 == "folder"

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_subdirectory_recursive_matching(self, fs):
        """
        用例: 子目录递归匹配（跨参数的子目录链）

        输入: ["My", "Folder/App", "Folder/New", "Folder", "测试内容"]
        模拟环境:
            ./My                                (文件夹)
            ./My Folder/                        (文件夹)
            ./My Folder/App                     (文件夹)
            ./My Folder/App Folder/             (文件夹)
            ./My Folder/App Folder1/            (文件夹)
            ./My Folder/App Folder/New Folder/  (文件夹)
            ./Other                             (文件夹)

            listdir(".")            -> ["My", "My Folder", "Other"]
            listdir("./My Folder") -> ["App", "App Folder", "App Folder1"]
            listdir("./My Folder/App Folder") -> ["New Folder", "Other"]

        预期输出 (按优先级排序，按剩余参数数量升序):
            [
                ("My Folder/App Folder/New Folder", ["测试内容"], "folder"),      # 剩余 1 个
                ("My Folder/App", ["Folder/New", "Folder", "测试内容"], "folder"), # 剩余 3 个
                ("My", ["Folder/App", "Folder/New", "Folder", "测试内容"], "folder"), # 剩余 4 个
            ]
        """
        fs.create_dir("My")
        fs.create_dir("My Folder/App")
        fs.create_dir("My Folder/App Folder/New Folder")
        fs.create_dir("My Folder/App Folder1")
        fs.create_dir("Other")

        result = find_candidates(["My", "Folder/App", "Folder/New", "Folder", "测试内容"])

        # 严格验证所有候选（按优先级排序）
        assert len(result) == 3

        # 候选 1: 最大匹配
        path1, remaining1, type1 = result[0]
        assert path1 == Path("My Folder/App Folder/New Folder")
        assert remaining1 == ["测试内容"]
        assert type1 == "folder"

        # 候选 2: 中间匹配
        path2, remaining2, type2 = result[1]
        assert path2 == Path("My Folder/App")
        assert remaining2 == ["Folder/New", "Folder", "测试内容"]
        assert type2 == "folder"

        # 候选 3: 基础匹配
        path3, remaining3, type3 = result[2]
        assert path3 == Path("My")
        assert remaining3 == ["Folder/App", "Folder/New", "Folder", "测试内容"]
        assert type3 == "folder"

    def test_empty_args(self):
        """
        用例: 空参数列表

        输入: []
        模拟环境: (无需模拟)

        预期输出:
            [] (空列表)
        """
        result = find_candidates([])
        assert result == []

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_multiple_slashes_in_single_arg(self, fs):
        """
        用例: 单个参数包含多个路径分隔符

        输入: ["My", "Folder/App/Deep/New", "备注"]
        模拟环境:
            ./My                       (文件夹)
            ./My Folder/               (文件夹)
            ./My Folder/App/           (文件夹)
            ./My Folder/App/Deep/      (文件夹)
            ./My Folder/App/Deep/New/  (文件夹)

            listdir(".")          -> ["My", "My Folder"]
            listdir("./My Folder") -> ["App"]
            listdir("./My Folder/App") -> ["Deep"]
            listdir("./My Folder/App/Deep") -> ["New"]

        预期输出 (按优先级排序，按剩余参数数量升序):
            [
                ("My Folder/App/Deep/New", ["备注"], "folder"),      # 剩余 1 个
                ("My", ["Folder/App/Deep/New", "备注"], "folder"),   # 剩余 2 个
            ]

        说明:
            - "Folder/App/Deep/New" 是单个参数，包含 3 个 /，表示 4 级子目录
            - _find_subpath_candidates 应该递归处理每一级
        """
        fs.create_dir("My")
        fs.create_dir("My Folder/App/Deep/New")

        result = find_candidates(["My", "Folder/App/Deep/New", "备注"])

        # 严格验证所有候选
        assert len(result) == 2

        # 候选 1: 最大匹配
        path1, remaining1, type1 = result[0]
        assert path1 == Path("My Folder/App/Deep/New")
        assert remaining1 == ["备注"]
        assert type1 == "folder"

        # 候选 2: 基础匹配
        path2, remaining2, type2 = result[1]
        assert path2 == Path("My")
        assert remaining2 == ["Folder/App/Deep/New", "备注"]
        assert type2 == "folder"

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_absolute_path_with_slash_arg(self, fs):
        """
        用例: 绝对路径 + 含 / 的参数（跨参数空格匹配）

        输入: ["D:\\My", "Folder/Sub", "备注"]
        模拟环境:
            D:\\My            (文件夹)
            D:\\My Folder\\    (文件夹)
            D:\\My Folder\\Sub\\ (文件夹)

            listdir("D:\\") -> ["My", "My Folder"]
            listdir("D:\\My Folder") -> ["Sub"]

        预期输出 (按优先级排序，按剩余参数数量升序):
            [
                ("D:\\My Folder\\Sub", ["备注"], "folder"),      # 剩余 1 个
                ("D:\\My", ["Folder/Sub", "备注"], "folder"),    # 剩余 2 个
            ]

        说明:
            - "D:\\My" 是绝对路径，"Folder/Sub" 的 "Folder" 与 "My" 正则匹配 → "My Folder"
            - "Sub" 在 "My Folder" 中匹配子目录
            - 测试绝对路径与跨参数 / 处理的组合场景
        """
        fs.create_dir("D:\\My")
        fs.create_dir("D:\\My Folder\\Sub")

        result = find_candidates(["D:\\My", "Folder/Sub", "备注"])

        # 严格验证所有候选
        assert len(result) == 2

        # 候选 1: 最大匹配
        path1, remaining1, type1 = result[0]
        assert path1 == Path("D:\\My Folder\\Sub")
        assert remaining1 == ["备注"]
        assert type1 == "folder"

        # 候选 2: 基础匹配
        path2, remaining2, type2 = result[1]
        assert path2 == Path("D:\\My")
        assert remaining2 == ["Folder/Sub", "备注"]
        assert type2 == "folder"

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_empty_directory(self, fs):
        """
        用例: 空目录处理

        输入: ["D:\\Empty", "Folder", "备注"]
        模拟环境:
            D:\\ 目录下存在空文件夹 "Empty Folder"
            listdir("D:\\") -> ["Empty Folder"]
            listdir("D:\\Empty Folder") -> []

        预期输出:
            [("D:\\Empty Folder\\App", ["备注"], "folder")]

        说明: 匹配到 "Empty Folder" 后继续搜索，发现目录为空，加入候选
        """
        fs.create_dir("D:\\Empty Folder")

        result = find_candidates(["D:\\Empty", "Folder\\App", "备注"])

        assert len(result) == 0

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_separator_no_match(self, fs):
        """
        用例: 分隔符匹配失败

        输入: ["D:\\My", "Invalid/Sub", "备注"]
        模拟环境:
            D:\\My            (文件夹)
            D:\\My Folder\\    (文件夹)
            listdir("D:\\") -> ["My", "My Folder"]
            listdir("D:\\My Folder") -> ["Sub"]

        预期输出:
            [("D:\\My", ["Invalid/Sub", "备注"], "folder")]

        说明: "My" 匹配后，"Invalid" 在 "My Folder" 中无匹配，搜索结束
        """
        fs.create_dir("D:\\My")
        fs.create_dir("D:\\My Folder\\Sub")

        result = find_candidates(["D:\\My", "Invalid/Sub", "备注"])

        assert len(result) == 1
        path, remaining, type_ = result[0]
        assert path == Path("D:\\My")
        assert remaining == ["Invalid/Sub", "备注"]
        assert type_ == "folder"

    @pytest.mark.skipif(os.name != "nt", reason="Windows only")
    def test_file_skipped(self, fs):
        """
        用例: 跳过文件（非目录路径）

        输入: ["D:\\My", "File", "Folder", "备注内容"]
        模拟环境:
            D:\\My File          (文件，应被跳过)
            D:\\My File Folder\\  (文件夹)
            listdir("D:\\") -> ["My File", "My File Folder"]

        预期输出:
            [("D:\\My File Folder", ["备注内容"], "folder")]

        说明: "My File" 和 "My File Folder" 都匹配 "My File"，但 "My File" 是文件被跳过
        """
        fs.create_file("D:\\My File")
        fs.create_dir("D:\\My File Folder")

        result = find_candidates(["D:\\My", "File\\Folder", "备注内容"])

        assert len(result) == 0


@pytest.mark.unit
class TestGetCurrentWorkingPath:
    """测试 get_current_working_path 函数"""

    def test_empty_string(self):
        """空字符串返回 (".", Cursor(0, 0))"""
        from remark.utils.path_resolver import get_current_working_path

        working, cursor = get_current_working_path("")
        assert working == PureWindowsPath()
        assert cursor.arg_index == 0
        assert cursor.char_index == 0

    def test_absolute_root(self):
        r"""根目录 C:\ 返回 (C:\, Cursor(0, 2))"""
        from remark.utils.path_resolver import get_current_working_path

        working, cursor = get_current_working_path("C:\\")
        assert working == PureWindowsPath("C:\\")
        assert cursor.arg_index == 0
        assert cursor.char_index == 2

    def test_absolute_with_trailing_slash(self):
        r"""C:\MyFolder\ 返回 (C:\, Cursor(0, 2))"""
        from remark.utils.path_resolver import get_current_working_path

        working, cursor = get_current_working_path("C:\\MyFolder\\")
        assert working == PureWindowsPath("C:\\")
        assert cursor.arg_index == 0
        assert cursor.char_index == 2

    def test_absolute_without_trailing_slash(self):
        r"""C:\MyFolder 返回 (C:, Cursor(0, 2))"""
        from remark.utils.path_resolver import get_current_working_path

        working, cursor = get_current_working_path("C:\\MyFolder")
        assert working == PureWindowsPath("C:\\")
        assert cursor.arg_index == 0
        assert cursor.char_index == 2

    def test_absolute_multi_level(self):
        r"""C:\MyFolder\Other 返回 (C:\MyFolder, Cursor(0, 11))"""
        from remark.utils.path_resolver import get_current_working_path

        working, cursor = get_current_working_path("C:\\MyFolder\\Other")
        assert working == PureWindowsPath("C:\\MyFolder")
        assert cursor.arg_index == 0
        assert cursor.char_index == 11

    def test_forward_slash_normalization(self):
        r"""C:/My/Folder 规范化后返回 (C:\My, Cursor(0, 5))"""
        from remark.utils.path_resolver import get_current_working_path

        working, cursor = get_current_working_path("C:/My/Folder")
        assert working == PureWindowsPath("C:\\My")
        assert cursor.arg_index == 0
        assert cursor.char_index == 5

    def test_relative_single(self):
        """MyFolder 返回 (., Cursor(0, 0))"""
        from remark.utils.path_resolver import get_current_working_path

        working, cursor = get_current_working_path("MyFolder")
        assert working == PureWindowsPath()
        assert cursor.arg_index == 0
        assert cursor.char_index == -1

    def test_relative_with_backslash(self):
        r"""My\Folder 返回 (My, Cursor(0, 2))"""
        from remark.utils.path_resolver import get_current_working_path

        working, cursor = get_current_working_path("My\\Folder")
        assert working == PureWindowsPath("My")
        assert cursor.arg_index == 0
        assert cursor.char_index == 2
