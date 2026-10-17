"""Stable ingredient identities and French/English matching."""

from src.localization.catalogs import CANONICAL_KEYS, CATALOGS

FOOD_NAMES = {
    canonical: CATALOGS["en"][key]
    for canonical, key in CANONICAL_KEYS.items()
    if key.startswith("food.")
}


def canonical_food(text: str) -> str:
    return next(
        (
            source
            for source, english in FOOD_NAMES.items()
            if text.casefold()
            in (
                source.casefold(),
                english.casefold(),
                CATALOGS["fr"][CANONICAL_KEYS[source]].casefold(),
            )
        ),
        text,
    )


def food_terms(text: str) -> tuple[str, str]:
    canonical = canonical_food(text)
    return canonical, FOOD_NAMES.get(canonical, canonical)
