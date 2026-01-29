"""
Internationalization (i18n) module for Windows Folder Remark tool.

This module provides translation support using gettext.
"""
from __future__ import annotations

import ctypes
import gettext
import locale
import os
import platform
from pathlib import Path
from typing import Final

# 项目根目录
PROJECT_ROOT: Final = Path(__file__).parent.parent

# 翻译文件目录
LOCALE_DIR: Final = PROJECT_ROOT / "locale"

# 翻译域
DOMAIN: Final = "messages"

# 支持的语言列表
SUPPORTED_LANGUAGES: Final = ("en", "zh")


def _get_windows_locale() -> str | None:
    """
    在 Windows 上使用 Windows API 获取用户默认区域设置名称.

    Returns:
        区域设置名称（如 'zh-CN', 'en-US'），如果获取失败则返回 None
    """
    try:
        # GetUserDefaultLocaleName 返回 locale 名称（如 'zh-CN', 'en-US'）
        # 缓冲区大小为 LOCALE_NAME_MAX_LENGTH (85)
        buffer_size: int = 85
        buffer: ctypes.Array[ctypes.c_wchar] = ctypes.create_unicode_buffer(buffer_size)

        # kernel32.dll 中的 GetUserDefaultLocaleName 函数
        # 原型: int GetUserDefaultLocaleName(LPWSTR lpLocaleName, int cchLocaleName)
        kernel32 = ctypes.windll.kernel32
        kernel32.GetUserDefaultLocaleName.restype = ctypes.c_int
        kernel32.GetUserDefaultLocaleName.argtypes = [
            ctypes.POINTER(ctypes.c_wchar),
            ctypes.c_int,
        ]

        result: int = kernel32.GetUserDefaultLocaleName(buffer, buffer_size)

        if result > 0:
            return buffer.value.strip()
    except (AttributeError, OSError, ValueError):
        pass

    return None


def get_system_language() -> str:
    """
    获取系统语言设置.

    在 Windows 上优先使用 GetUserDefaultLocaleName API，
    在其他平台上使用环境变量和 locale.getlocale()。

    Returns:
        语言代码（如 'en', 'zh'），如果不支持则返回默认的 'en'
    """
    # Windows 平台优先使用 Windows API
    if platform.system() == "Windows":
        windows_locale = _get_windows_locale()
        if windows_locale:
            # Windows locale 格式为 'zh-CN', 'en-US' 等
            # 提取语言部分（zh-CN -> zh）
            lang_code = windows_locale.split("-")[0]
            if lang_code in SUPPORTED_LANGUAGES:
                return lang_code

    # 尝试从环境变量获取
    lang = os.environ.get("LANG", "")
    if lang:
        # 提取语言代码（如 zh_CN.UTF-8 -> zh）
        lang_code = lang.split(".")[0].split("_")[0]
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code
        # 处理完整语言代码（如 zh_CN -> zh）
        if "_" in lang:
            full_lang = lang.split(".")[0]
            if full_lang in SUPPORTED_LANGUAGES:
                return full_lang

    # 尝试从 locale 获取
    try:
        loc = locale.getlocale()[0]
        if loc:
            # locale 格式可能是 'zh_CN', 'zh-CN', 'Chinese_China' 等
            normalized = loc.replace("-", "_")
            if normalized in SUPPORTED_LANGUAGES:
                return normalized
            # 尝试只取语言部分
            lang_code = normalized.split("_")[0]
            if lang_code in SUPPORTED_LANGUAGES:
                return lang_code
            # 处理 Windows 特殊格式（如 'Chinese_China' -> 'zh'）
            if normalized.startswith("Chinese"):
                return "zh"
    except (ValueError, AttributeError):
        pass

    # 默认返回英文
    return "en"


def init_translation(language: str | None = None) -> gettext.GNUTranslations:
    """
    初始化翻译.

    Args:
        language: 语言代码，如果为 None 则使用系统语言

    Returns:
        翻译函数
    """
    if language is None:
        language = get_system_language()

    # 确保语言受支持
    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    # 尝试加载翻译
    try:
        translator = gettext.translation(
            domain=DOMAIN,
            localedir=str(LOCALE_DIR),
            languages=[language],
            fallback=True,
        )
        return translator
    except Exception:
        # 如果加载失败，使用空翻译（返回原字符串）
        return gettext.NullTranslations()


# 全局翻译函数
_translator: gettext.GNUTranslations | gettext.NullTranslations | None = None


def get_translator() -> gettext.GNUTranslations | gettext.NullTranslations:
    """
    获取当前翻译器.

    Returns:
        翻译器实例
    """
    global _translator
    if _translator is None:
        _translator = init_translation()
    return _translator


def set_language(language: str) -> None:
    """
    设置当前语言.

    Args:
        language: 语言代码（如 'en', 'zh_CN'）
    """
    global _translator
    _translator = init_translation(language)


def gettext_function(message: str) -> str:
    """
    翻译函数（用于在代码中标记可翻译字符串）.

    Args:
        message: 要翻译的字符串

    Returns:
        翻译后的字符串
    """
    return get_translator().gettext(message)


def ngettext_function(singular: str, plural: str, n: int) -> str:
    """
    复数形式翻译函数.

    Args:
        singular: 单数形式
        plural: 复数形式
        n: 数量

    Returns:
        翻译后的字符串
    """
    return get_translator().ngettext(singular, plural, n)


# 默认导出的翻译函数
_ = gettext_function
