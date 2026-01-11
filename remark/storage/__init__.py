"""
存储层模块 - 提供统一的存储接口
"""

from .desktop_ini import DesktopIniHandler, EncodingConversionCanceled

__all__ = ["DesktopIniHandler", "EncodingConversionCanceled"]
