"""Load the French and English text catalogs without importing UI services."""

import json
from pathlib import Path

SUPPORTED_LANGUAGES = ("fr", "en")
DEFAULT_LANGUAGE = "en"
CATALOGS: dict[str, dict[str, str]] = {
    language: json.loads(
        Path(__file__).with_name(f"{language}.json").read_text(encoding="utf-8")
    )
    for language in SUPPORTED_LANGUAGES
}

CANONICAL_KEYS: dict[str, str] = json.loads(
    Path(__file__).with_name("vocabulary.json").read_text(encoding="utf-8")
)

# Canonical ingredient/unit/category values and older persisted recipe examples
# use French identities. Resolve those values through the same catalogs at display.
ENGLISH = {french: CATALOGS["en"][key] for key, french in CATALOGS["fr"].items()}
ENGLISH.update({value: CATALOGS["en"][key] for value, key in CANONICAL_KEYS.items()})


def source_text(key: str) -> str:
    """Resolve a message's source text for language-neutral error/progress APIs."""
    return CATALOGS["fr"][key]


def translate(key_or_text: str, language: str, **values) -> str:
    """Resolve a stable ID, preserving user text and canonical data values.

    Formatting is explicit: arbitrary user/AI text containing braces is never
    interpreted as a template unless the caller supplies template values.
    """
    language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    catalog = CATALOGS[language]
    text = catalog.get(CANONICAL_KEYS.get(key_or_text, key_or_text))
    if text is None:
        text = (
            ENGLISH.get(key_or_text, key_or_text) if language == "en" else key_or_text
        )
    return text.format(**values) if values else text
