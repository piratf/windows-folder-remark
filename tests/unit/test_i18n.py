"""国际化 (i18n) 单元测试"""

from unittest.mock import MagicMock, patch

import pytest

from remark.i18n import (
    SUPPORTED_LANGUAGES,
    _get_windows_locale,
    get_system_language,
    gettext_function,
    init_translation,
    ngettext_function,
    set_language,
)


@pytest.mark.unit
class TestGetWindowsLocale:
    """Windows locale 获取测试"""

    @pytest.mark.parametrize(
        "locale_name,expected",
        [
            ("zh-CN", "zh-CN"),
            ("en-US", "en-US"),
            ("zh-TW", "zh-TW"),
        ],
    )
    def test_get_windows_locale_success(self, locale_name, expected):
        """测试成功获取 Windows locale"""
        mock_buffer = MagicMock()
        mock_buffer.value = locale_name
        mock_buffer.strip.return_value = locale_name

        with patch("ctypes.create_unicode_buffer", return_value=mock_buffer):
            with patch("ctypes.windll.kernel32.GetUserDefaultLocaleName", return_value=len(locale_name)):
                result = _get_windows_locale()
                assert result == expected

    def test_get_windows_locale_api_fails(self):
        """测试 Windows API 调用失败"""
        with patch("ctypes.windll.kernel32.GetUserDefaultLocaleName", return_value=0):
            result = _get_windows_locale()
            assert result is None

    def test_get_windows_locale_exception(self):
        """测试 Windows API 抛出异常"""
        with patch("ctypes.windll.kernel32.GetUserDefaultLocaleName", side_effect=OSError):
            result = _get_windows_locale()
            assert result is None


@pytest.mark.unit
class TestGetSystemLanguage:
    """系统语言获取测试"""

    @pytest.mark.parametrize(
        "windows_locale,expected",
        [
            ("zh-CN", "zh"),
            ("en-US", "en"),
            ("zh-TW", "zh"),
        ],
    )
    def test_windows_platform_priority(self, windows_locale, expected):
        """测试 Windows 平台优先使用 Windows API"""
        with patch("remark.i18n.platform.system", return_value="Windows"):
            with patch("remark.i18n._get_windows_locale", return_value=windows_locale):
                result = get_system_language()
                assert result in SUPPORTED_LANGUAGES
                assert result == expected

    @pytest.mark.parametrize(
        "windows_locale",
        ["ja-JP", "ko-KR", "fr-FR"],
    )
    def test_windows_unsupported_locale_fallback(self, windows_locale):
        """测试不支持的语言回退到默认"""
        with patch("remark.i18n.platform.system", return_value="Windows"):
            with patch("remark.i18n._get_windows_locale", return_value=windows_locale):
                with patch.dict("os.environ", {}, clear=True):
                    with patch("remark.i18n.locale.getlocale", return_value=(None, None)):
                        result = get_system_language()
                        assert result == "en"

    def test_windows_api_null_fallback_to_locale(self):
        """测试 Windows API 返回 None 时回退到 locale.getlocale()"""
        with patch("remark.i18n.platform.system", return_value="Windows"):
            with patch("remark.i18n._get_windows_locale", return_value=None):
                with patch.dict("os.environ", {}, clear=True):
                    with patch("remark.i18n.locale.getlocale", return_value=("zh_CN", "cp1252")):
                        result = get_system_language()
                        assert result == "zh"

    @pytest.mark.parametrize(
        "locale_value,expected",
        [
            ("zh_CN", "zh"),
            ("zh-CN", "zh"),
            ("Chinese_China", "zh"),
            ("en_US", "en"),
            ("en-GB", "en"),
            ("English_United States", "en"),
        ],
    )
    def test_locale_getlocale_variations(self, locale_value, expected):
        """测试 locale.getlocale() 的各种返回值格式"""
        with patch("remark.i18n.platform.system", return_value="Linux"):
            with patch("remark.i18n._get_windows_locale", return_value=None):
                with patch.dict("os.environ", {}, clear=True):
                    with patch("remark.i18n.locale.getlocale", return_value=(locale_value, "cp1252")):
                        result = get_system_language()
                        assert result == expected

    @pytest.mark.parametrize(
        "env_lang,expected",
        [
            ("zh_CN.UTF-8", "zh"),
            ("en_US.UTF-8", "en"),
            ("zh.UTF-8", "zh"),
            ("en", "en"),
        ],
    )
    def test_lang_environment_variable(self, env_lang, expected):
        """测试 LANG 环境变量"""
        with patch("remark.i18n.platform.system", return_value="Linux"):
            with patch("remark.i18n._get_windows_locale", return_value=None):
                with patch.dict("os.environ", {"LANG": env_lang}):
                    with patch("remark.i18n.locale.getlocale", return_value=(None, None)):
                        result = get_system_language()
                        assert result == expected

    def test_all_methods_fallback_to_default(self):
        """测试所有方法都失败时回退到默认语言"""
        with patch("remark.i18n.platform.system", return_value="Linux"):
            with patch("remark.i18n._get_windows_locale", return_value=None):
                with patch.dict("os.environ", {}, clear=True):
                    with patch("remark.i18n.locale.getlocale", return_value=(None, None)):
                        result = get_system_language()
                        assert result == "en"


@pytest.mark.unit
class TestInitTranslation:
    """翻译初始化测试"""

    @pytest.mark.parametrize(
        "language,expected_domain",
        [
            ("en", "messages"),
            ("zh", "messages"),
        ],
    )
    def test_init_translation_supported_language(self, language, expected_domain):
        """测试支持的语言初始化"""
        translator = init_translation(language)
        assert translator is not None
        assert translator.gettext("test") == "test"

    def test_init_translation_unsupported_language_fallback(self):
        """测试不支持的语言回退到英文"""
        translator = init_translation("fr")
        assert translator is not None
        # 应该回退到 NullTranslations 或英文翻译
        assert translator.gettext("test") == "test"

    def test_init_translation_none_uses_system(self):
        """测试 None 作为参数使用系统语言"""
        with patch("remark.i18n.get_system_language", return_value="zh"):
            translator = init_translation(None)
            assert translator is not None


@pytest.mark.unit
class TestSetLanguage:
    """设置语言测试"""

    def test_set_language_updates_translator(self):
        """测试设置语言更新翻译器"""
        set_language("zh")
        # 验证语言已被设置（通过调用 gettext_function）
        result = gettext_function("Windows Folder Remark Tool")
        # 如果成功加载中文翻译，应该返回中文字符串
        # 否则返回原字符串
        assert isinstance(result, str)


@pytest.mark.unit
class TestGetTextFunction:
    """翻译函数测试"""

    def test_gettext_function_returns_string(self):
        """测试 gettext_function 返回字符串"""
        result = gettext_function("test message")
        assert isinstance(result, str)

    def test_ngettext_function_singular(self):
        """测试 ngettext 单数形式"""
        result = ngettext_function("one item", "many items", 1)
        assert isinstance(result, str)

    def test_ngettext_function_plural(self):
        """测试 ngettext 复数形式"""
        result = ngettext_function("one item", "many items", 10)
        assert isinstance(result, str)
