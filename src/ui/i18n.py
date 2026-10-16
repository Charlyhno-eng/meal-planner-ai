"""English translations of UI text and supported ingredient vocabulary."""

import json
from pathlib import Path

from PySide6.QtCore import QLocale

from src.domain.foods import FOOD_NAMES, canonical_food

__all__ = [
    "ENGLISH",
    "FOOD_NAMES",
    "canonical_food",
    "system_language",
    "translate",
    "translate_food",
]

ENGLISH = json.loads(Path(__file__).with_name("translations.json").read_text("utf-8"))


def system_language() -> str:
    """Use the first supported OS UI language, falling back to English."""
    for tag in QLocale.system().uiLanguages():
        language = tag.replace("_", "-").split("-", 1)[0].lower()
        if language in ("fr", "en"):
            return language
    return "en"


def translate(text: str, language: str) -> str:
    return ENGLISH.get(text, text) if language == "en" else text


def translate_food(text: str, language: str) -> str:
    """Translate known ingredients while preserving custom food names."""
    return translate(text, language) if text in FOOD_NAMES else text
