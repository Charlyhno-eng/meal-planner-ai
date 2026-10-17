"""Resolve the supported application language from OS UI preferences."""

from PySide6.QtCore import QLocale

from src.localization.catalogs import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


def system_language() -> str:
    for tag in QLocale.system().uiLanguages():
        language = tag.replace("_", "-").split("-", 1)[0].lower()
        if language in SUPPORTED_LANGUAGES:
            return language
    return DEFAULT_LANGUAGE
