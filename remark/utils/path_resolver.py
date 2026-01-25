"""
路径解析模块

处理未加引号的含空格路径，智能重建完整路径。
"""

import posixpath
import re
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PureWindowsPath


class NextResult(Enum):
    """Cursor.next() 的返回类型枚举"""

    SEPARATOR = "separator"  # 找到路径分隔符
    END_OF_ARG = "end_of_arg"  # 找到参数末尾


@dataclass
class Cursor:
    """
    路径解析游标，跟踪当前解析位置

    注意：Cursor 在 posix 格式分隔符 (/) 上工作，因为 normalized_args 使用 posix 格式

    Attributes:
        arg_index: 当前指向第几个参数（从 0 开始）
        char_index: 当前指向参数中第几个字符（路径归一化后的参数为准，从 0 开始）
    """

    arg_index: int
    char_index: int

    def jump_to_end_of_arg(self, normalized_args: list[str]) -> None:
        """
        跳转到当前参数的结束位置

        :param normalized_args: 归一化后的参数列表
        """
        self.char_index = len(normalized_args[self.arg_index])

    def jump_to_last_separator(self, normalized_args: list[str]) -> None:
        """
        跳转到当前参数的最后一个系统分隔符位置
        如果找不到，则留在当前位置 (后面没有分隔符)

        :param normalized_args: 归一化后的参数列表
        """
        norm_path = normalized_args[self.arg_index]
        last_sep = norm_path.rfind(posixpath.sep)
        if last_sep >= 0:
            self.char_index = last_sep
        else:
            self.char_index = -1

    def next(self, normalized_args: list[str]) -> tuple["Cursor", NextResult] | None:
        """
        从当前位置向后查找，找到下一个路径分隔符或参数末尾

        搜索从 char_index + 1 开始（跳过当前位置），找到下一个分隔符或参数末尾。
        找到分隔符时，end cursor 停在分隔符上（与 jump_to_last_separator 保持一致）。

        :param normalized_args: 归一化后的参数列表
        :return: (新 cursor, NextResult) 或 None（如果无法继续）
        """
        new_cursor = Cursor(self.arg_index, self.char_index)

        while new_cursor.arg_index < len(normalized_args):
            current_arg = normalized_args[new_cursor.arg_index]
            arg_len = len(current_arg)

            # 如果当前位置已在参数末尾，跳到下一个参数开头
            if new_cursor.char_index >= arg_len:
                new_cursor.arg_index += 1
                new_cursor.char_index = 0
                continue

            # 从 char_index + 1 开始查找分隔符（跳过当前位置）
            search_start = new_cursor.char_index + 1
            sep_pos = current_arg.find(posixpath.sep, search_start)

            if sep_pos >= 0:
                # 找到分隔符，新 cursor 停在分隔符上
                new_cursor.char_index = sep_pos
                return new_cursor, NextResult.SEPARATOR

            # 没有找到分隔符，跳到当前参数末尾
            new_cursor.char_index = arg_len
            return new_cursor, NextResult.END_OF_ARG

        # 已经到达最后一个参数的末尾，无法继续
        return None


def get_between(begin: Cursor, end: Cursor, normalized_args: list[str]) -> list[str]:
    """
    获取两个 cursor 之间的内容，可能跨多个参数

    :param begin: 起始 cursor（不包含）
    :param end: 结束 cursor（不包含）
    :param normalized_args: 归一化后的参数列表
    :return: 字符串片段列表
    """
    if begin.arg_index == end.arg_index:
        # 同一个参数内，从 begin.char_index + 1 开始（不包含 begin 位置）
        arg = normalized_args[begin.arg_index]
        return [arg[begin.char_index + 1 : end.char_index]]

    # 跨多个参数
    result = []

    # 第一个参数的部分，从 begin.char_index + 1 开始（不包含 begin 位置）
    first_arg = normalized_args[begin.arg_index]
    result.append(first_arg[begin.char_index + 1 :])

    # 中间的完整参数
    for i in range(begin.arg_index + 1, end.arg_index):
        result.append(normalized_args[i])

    # 最后一个参数的部分
    if end.arg_index < len(normalized_args):
        last_arg = normalized_args[end.arg_index]
        result.append(last_arg[: end.char_index])

    return result


def build_pattern(parts: list[str]) -> re.Pattern:
    r"""
    将多个字符串片段构建为宽容搜索的正则表达式

    由于终端用空格分割参数，用户输入的 "My Folder" 会被分割成 ["My", "Folder"]。
    此函数构建一个宽容的正则表达式来匹配可能的文件名。

    宽容规则：
    - 片段之间允许任意空白字符（用 \s+ 连接）
    - 转义所有正则表达式特殊字符，用户输入不含正则表达式
    - 使用 re.IGNORECASE 忽略大小写（Windows 文件系统不区分大小写）

    :param parts: 字符串片段列表
    :return: 编译后的正则表达式模式
    """
    if not parts:
        return re.compile(r"")

    # 转义每个片段中的正则表达式特殊字符
    escaped_parts = [re.escape(part) for part in parts]

    # 用 \s+ 连接片段，允许片段之间有任意空白
    pattern = r"\s+".join(escaped_parts)

    # 首尾精确匹配
    pattern = r"^" + pattern + r"$"

    # 忽略大小写匹配
    return re.compile(pattern, re.IGNORECASE)


def get_current_working_path(
    first_arg: str, cursor: Cursor | None = None, normalized_args: list[str] | None = None
) -> tuple[PureWindowsPath, Cursor]:
    """
    从第一个参数中提取工作目录和剩余内容

    规则：
    - 使用 PureWindowsPath 规范化路径并获取父目录
    - 空字符串 → (".", "")

    :param first_arg: 一个路径
    :param cursor: 游标，如果为 None 则初始化为 (0, 0)
    :param normalized_args: 归一化后的参数列表，如果为 None 则使用 first_arg 初始化
    :return: (工作目录, Cursor)
    """
    # 如果 cursor 为 None，初始化为 (0, 0)
    if cursor is None:
        cursor = Cursor(0, 0)

    # 如果 normalized_args 为 None，归一化 first_arg
    if normalized_args is None:
        normalized_args = [PureWindowsPath(first_arg).as_posix()]

    # 空字符串处理
    if not first_arg:
        return PureWindowsPath(), cursor

    # 使用 pathlib 获取父目录
    path_obj = PureWindowsPath(first_arg)
    parent = path_obj.parent

    # 跳转到最后一个分隔符位置，因为 parent 可能是 "." 等特殊情况，根据最后一个分隔符判断是安全的
    cursor.jump_to_last_separator(normalized_args)
    return parent if parent else PureWindowsPath(), cursor


def get_inner_items_list(current_working_path: Path) -> list[Path]:
    """
    获取指定路径下的所有文件和文件夹列表

    :param current_working_path: 当前工作目录路径
    :return: 文件和文件夹名称列表，如果路径不存在或不是目录则返回空列表
    """
    return list(current_working_path.iterdir())


def find_candidates(
    args_list: list[str],
) -> list[tuple[Path, list[str], str]]:
    """
    递归查找所有可能的路径重建候选

    返回所有候选，按优先级排序（消耗更多 args 的优先）

    Args:
        args_list: argparse 解析后的位置参数列表
                   例如: ["C:\\Program", "Files", "App"] 或 ["My", "Folder/App", "备注"]

    Returns:
        List[Tuple[full_path, remaining_args, type]]: 所有候选
        - full_path: 完整路径
        - remaining_args: 剩余参数（作为备注内容）
        - type: "folder" 或 "file"

    """
    if not args_list:
        return []

    # 归一化所有参数
    normalized_args = [PureWindowsPath(arg).as_posix() for arg in args_list]

    # 构建游标
    cursor = Cursor(0, 0)

    # 根据第一个参数，判断当前工作目录
    current_working_path, cursor = get_current_working_path(args_list[0], cursor, normalized_args)

    # 处理剩余内容
    # 接下来是一个经典的 BFS 搜索问题，我们使用队列来保存当前工作目录和游标作为搜索起点（值拷贝）
    # - 如果队列为空，结束搜索
    # 获取当前队头的工作目录对应的文件列表
    #   - 如果为空，则工作目录加入候选，弹出队列
    #   - 否则继续
    # 接下来使用三指针策略，一个新的 next_ 指针沿着当前 cursor 向后找，一个 last_ 保存上一次找到的位置，一个 start_ 保存起始位置，每次
    #   - 找到下一个路径分隔符
    #   - 或者找到下一个参数末尾
    # Cursor 应当提供一个 next 接口，返回新的指针和以上两种类型之一，但是不要修改当前 cursor 的值
    # Cursor 应当提供一个 get_between 接口，返回两个指针之间的全部字符串内容(可能跨多个参数，因此可能有多个字符串)
    # 当前模块应当提供一个把多个字符串组合成一个正则表达式的函数
    # 如果找到的是路径分隔符
    #   - 将当前找到的内容()**放到一个正则表达式**中(抽象为一个函数)，然后在文件列表中搜索匹配
    #       - 如果匹配成功
    #           - 将成功的一个或多个匹配作为新的工作目录，带着新 cursor 值，进行深拷贝并加入候选项
    #       - 如果没有匹配成功
    #           - 结束搜索，返回当前可选项
    #   - 弹出当前工作目录
    # 如果找到的是参数末尾
    #   - 将当前找到的内容**放到一个正则表达式**中，然后在文件列表中搜索匹配
    #   - 如果匹配成功
    #       - 将成功的一个或多个匹配作为新的工作目录，带着新 cursor 值，进行深拷贝并加入候选项
    #   - 如果没有匹配成功
    #       - 当前 cursor 不变，队列也不变，新 Cursor 继续向后找
    #   - 无论匹配是否成功，当前工作目录都不变
    # 如果没有下一个参数，新 Cursor 无法前进
    #   - 弹出队列中的当前工作目录

    candidates: list[tuple[Path, list[str], str]] = []
    # 队列元素: (current_working_path, cursor)
    queue: deque[tuple[Path, Cursor, Cursor]] = deque()
    # working_path, start, last
    queue.append((Path(current_working_path), deepcopy(cursor), deepcopy(cursor)))

    while queue:
        work_path, start_cursor, cur = queue.popleft()
        if not work_path.is_dir():
            continue

        # 尝试从当前 cursor 向后推进
        next_result = cur.next(normalized_args)
        if next_result is None:
            # 无法继续，弹出队列中的当前工作目录（已处理）
            continue

        next_cursor, result_type = next_result

        # 获取当前 cursor 和 next_cursor 之间的内容
        parts = get_between(start_cursor, next_cursor, normalized_args)

        # 构建正则表达式
        pattern = build_pattern(parts)

        # 获取当前工作目录的文件列表
        inner_items = get_inner_items_list(work_path)

        if not inner_items:
            # 工作目录为空，加入候选
            remaining = get_remaining_args(next_cursor, normalized_args)
            candidates.append((work_path, remaining, "folder"))
            continue

        # 在文件列表中搜索匹配
        matches = [item.name for item in inner_items if pattern.search(item.name)]

        if result_type == NextResult.SEPARATOR:
            # 找到分隔符
            if matches:
                # 匹配成功，将匹配项作为新的工作目录加入队列
                # 需要将 cursor 推进到分隔符之后
                for match in matches:
                    queue.append((work_path / match, next_cursor, next_cursor))
            else:
                # 匹配失败，结束搜索，返回当前候选
                break

        elif result_type == NextResult.END_OF_ARG:
            # 找到参数末尾
            if matches:
                # 匹配成功，将匹配项加入候选
                for match in matches:
                    full_path = work_path / match
                    is_folder = full_path.is_dir()
                    entry_type = "folder" if is_folder else "file"
                    remaining = get_remaining_args(next_cursor, normalized_args)
                    candidates.append((full_path, remaining, entry_type))

            # 无论匹配是否成功，当前工作目录不变，继续尝试向前推进
            # 将当前工作目录和 next_cursor 重新加入队列
            queue.append((work_path, start_cursor, next_cursor))

    def _candidate_key(item: tuple[Path, list[str], str]) -> tuple[bool, int]:
        """候选排序键函数：folder 优先，路径越长越优先"""
        return (
            item[2] != "folder",  # folder 优先
            -len(str(item[0])),  # 路径越长越优先
        )

    # 匹配到的路径越长越优先（消耗的参数越多，剩余参数越少）
    candidates.sort(key=_candidate_key)

    return candidates if candidates else []


def get_remaining_args(cursor: Cursor, normalized_args: list[str]) -> list[str]:
    """
    获取 cursor 之后的所有剩余参数，作为备注内容

    :param cursor: 当前游标
    :param normalized_args: 归一化后的参数列表
    :return: 剩余参数拼接的字符串
    """
    remaining = []

    # 当前参数的剩余部分
    if cursor.arg_index < len(normalized_args):
        current_arg = normalized_args[cursor.arg_index]
        if cursor.char_index < len(current_arg):
            remaining.append(current_arg[cursor.char_index :])

    # 后续完整参数
    for i in range(cursor.arg_index + 1, len(normalized_args)):
        remaining.append(normalized_args[i])

    return remaining
