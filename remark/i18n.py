"""
Internationalization (i18n) module for Windows Folder Remark tool.

This module provides translation support using gettext.
"""
from __future__ import annotations

import gettext
import locale
import os
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


def get_system_language() -> str:
    """
    获取系统语言设置.

    Returns:
        语言代码（如 'en', 'zh_CN'），如果不支持则返回默认的 'en'
    """
    # 尝试从环境变量获取
    lang = os.environ.get("LANG", "")
    if lang:
        # 提取语言代码（如 zh_CN.UTF-8 -> zh_CN）
        lang_code = lang.split(".")[0].split("_")[0]
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code
        # 处理完整语言代码（如 zh_CN）
        if "_" in lang:
            full_lang = lang.split(".")[0]
            if full_lang in SUPPORTED_LANGUAGES:
                return full_lang

    # 尝试从 locale 获取
    try:
        loc = locale.getlocale()[0]
        if loc:
            # locale 格式可能是 'zh_CN' 或 'zh-CN'
            normalized = loc.replace("-", "_")
            if normalized in SUPPORTED_LANGUAGES:
                return normalized
            # 尝试只取语言部分
            lang_code = normalized.split("_")[0]
            if lang_code in SUPPORTED_LANGUAGES:
                return lang_code
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
