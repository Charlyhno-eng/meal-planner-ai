"""Shared language module for desktop labels and deterministic agent messages."""

from src.localization.catalogs import (
    CATALOGS,
    DEFAULT_LANGUAGE,
    ENGLISH,
    SUPPORTED_LANGUAGES,
    source_text,
    translate,
)

__all__ = [
    "CATALOGS",
    "DEFAULT_LANGUAGE",
    "ENGLISH",
    "SUPPORTED_LANGUAGES",
    "source_text",
    "system_language",
    "translate",
]


def system_language() -> str:
    # Keep the domain vocabulary and message catalogs usable without Qt imports.
    from src.localization.system import system_language as detect

    return detect()
