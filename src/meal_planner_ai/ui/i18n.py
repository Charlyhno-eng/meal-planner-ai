"""English translations of UI text and supported ingredient vocabulary."""

import json
from pathlib import Path

ENGLISH = json.loads(Path(__file__).with_name("translations.json").read_text("utf-8"))


def translate(text: str, language: str) -> str:
    return ENGLISH.get(text, text) if language == "en" else text


FOOD_NAMES = {
    "Quinoa",
    "Pois chiches",
    "Courgettes",
    "Citron",
    "Pâtes",
    "Tomates cerises",
    "Pesto",
    "Parmesan végétarien",
    "Lentilles corail",
    "Lait de coco",
    "Riz",
    "Curry",
    "Pain",
    "Avocat",
    "Œufs",
    "Salade",
    "Saumon",
    "Pommes de terre",
    "Champignons",
    "Bouillon de légumes",
    "Concombre",
    "Feta végétarienne",
}


def canonical_food(text: str) -> str:
    # Display translations never become ingredient identity keys.
    return next(
        (
            source
            for source in FOOD_NAMES
            if text.casefold() in (source.casefold(), ENGLISH[source].casefold())
        ),
        text,
    )


def translate_food(text: str, language: str) -> str:
    """Translate known ingredients while preserving custom food names."""
    return translate(text, language) if text in FOOD_NAMES else text
