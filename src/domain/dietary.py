"""French/English exclusion matching shared by planning and verification."""

import re
import unicodedata

from src.domain.foods import FOOD_NAMES

INTOLERANCE_SOURCES = {
    "gluten": (
        "blé",
        "wheat",
        "orge",
        "barley",
        "seigle",
        "rye",
        "farine",
        "flour",
        "pain",
        "bread",
        "pâtes",
        "pasta",
        "semoule",
        "couscous",
        "biscuit",
        "biscuits à la cuillère",
        "ladyfingers",
    ),
    "lactose": (
        "lait",
        "milk",
        "crème",
        "cream",
        "beurre",
        "butter",
        "fromage",
        "cheese",
        "yaourt",
        "yogurt",
        "mascarpone",
        "feta",
        "parmesan",
    ),
}


def normalize(text: str) -> str:
    text = text.casefold().replace("œ", "oe").replace("æ", "ae")
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )


def expand_terms(values: list[str]) -> list[str]:
    terms = {normalize(value.strip()) for value in values if value.strip()}
    aliases = [(source, english) for source, english in FOOD_NAMES.items()] + [
        ("oeuf", "oeufs", "egg", "eggs"),
        ("champignon", "champignons", "mushroom", "mushrooms"),
    ]
    for group in aliases:
        normalized = {normalize(word) for word in group}
        if terms & normalized:
            terms.update(normalized)
    for label, sources in INTOLERANCE_SOURCES.items():
        if label in terms:
            terms.update(normalize(source) for source in sources)
    return sorted(terms)


def _matching_terms(text: str, excluded: list[str]) -> list[str]:
    """Match whole food names, allowing explicit 'sans/without' and '-free' labels.

    Qualifiers apply within a phrase, never across comma/and/et-separated foods.
    An egg-free title cannot excuse eggs in the actual ingredient list or steps.
    """
    conflicts = set()
    for phrase in re.split(r"[.;,\n]|\b(?:and|et)\b", normalize(text)):
        safe_sources = set()
        for label, sources in INTOLERANCE_SOURCES.items():
            if label in excluded and re.search(
                rf"\b(?:sans|without|no) {label}\b|\b{label}[- ]free\b", phrase
            ):
                safe_sources.update(normalize(source) for source in (label, *sources))
        for term in excluded:
            term = normalize(term)
            if term in safe_sources:
                continue
            pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
            for match in re.finditer(pattern, phrase):
                before, after = phrase[: match.start()], phrase[match.end() :]
                if re.search(r"\b(?:sans|without|no|free of)\s*$", before):
                    continue
                if re.match(r"[- ]free\b", after):
                    continue
                conflicts.add(term)
    return sorted(conflicts)


def conflicting_terms(text: str, exclusions: list[str]) -> list[str]:
    """Check each explicit exclusion separately to preserve its meaning.

    Gluten-free pasta satisfies a gluten exclusion, but still conflicts when
    pasta itself is disliked. A free-from qualifier cannot erase that preference.
    """
    return sorted(
        {
            term
            for label in exclusions
            for term in _matching_terms(text, expand_terms([label]))
        }
    )
