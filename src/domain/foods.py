"""Stable ingredient identities and French/English matching."""

FOOD_NAMES = {
    "Avocat": "Avocado",
    "Biscuits à la cuillère": "Ladyfingers",
    "Bouillon de légumes": "Vegetable stock",
    "Cacao": "Cocoa",
    "Café": "Coffee",
    "Champignons": "Mushrooms",
    "Citron": "Lemon",
    "Concombre": "Cucumber",
    "Courgettes": "Courgettes",
    "Curry": "Curry",
    "Feta végétarienne": "Vegetarian feta",
    "Lait de coco": "Coconut milk",
    "Lentilles corail": "Red lentils",
    "Mascarpone": "Mascarpone",
    "Pain": "Bread",
    "Parmesan végétarien": "Vegetarian parmesan",
    "Pesto": "Pesto",
    "Pois chiches": "Chickpeas",
    "Pommes de terre": "Potatoes",
    "Pâtes": "Pasta",
    "Quinoa": "Quinoa",
    "Riz": "Rice",
    "Salade": "Lettuce",
    "Saumon": "Salmon",
    "Sucre": "Sugar",
    "Tomates cerises": "Cherry tomatoes",
    "Œufs": "Eggs",
}


def canonical_food(text: str) -> str:
    return next(
        (
            source
            for source, english in FOOD_NAMES.items()
            if text.casefold() in (source.casefold(), english.casefold())
        ),
        text,
    )


def food_terms(text: str) -> tuple[str, str]:
    canonical = canonical_food(text)
    return canonical, FOOD_NAMES.get(canonical, canonical)
