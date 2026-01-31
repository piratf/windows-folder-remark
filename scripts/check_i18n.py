#!/usr/bin/env python
"""检查翻译文件完整性"""

import re
import sys


def check_po_file(path: str) -> bool:
    """检查单个 .po 文件是否有空翻译"""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    found_issue = False
    while i < len(lines):
        line = lines[i]
        # 检查单行 msgid 后跟空 msgstr 的情况
        if re.match(r'^msgid ".+"$', line):
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # 如果下一行是 msgstr "" 且不是多行字符串的开始
                if next_line == 'msgstr ""':
                    # 检查是否真的是单行（再下一行不是以引号开头）
                    if i + 2 >= len(lines) or not lines[i + 2].strip().startswith('"'):
                        print(f"ERROR: {path}:{i + 2}: Empty translation: {line.strip()}")
                        found_issue = True
        i += 1

    return found_issue


if __name__ == "__main__":
    all_ok = True
    for path in sys.argv[1:]:
        if check_po_file(path):
            all_ok = False

    if not all_ok:
        print("\nERROR: Empty translations found! Please add translations.", file=sys.stderr)
        sys.exit(1)

    print("Translation check PASSED")
    sys.exit(0)
