"""UI adapter for the shared language module and canonical food vocabulary."""

from src.domain.foods import FOOD_NAMES, canonical_food
from src.localization import ENGLISH, system_language, translate

__all__ = [
    "ENGLISH",
    "FOOD_NAMES",
    "canonical_food",
    "system_language",
    "translate",
    "translate_food",
]


def translate_food(text: str, language: str) -> str:
    """Translate known ingredients while preserving custom food names."""
    return translate(text, language) if text in FOOD_NAMES else text
