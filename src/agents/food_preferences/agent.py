"""Reject incompatible recipes independently of model instructions."""

import re

from src.domain.dietary import conflicting_terms
from src.domain.foods import food_terms
from src.errors import MealPlannerError
from src.localization import source_text
from src.models.coordinator import RequestedMeal
from src.models.household import exclusion_labels


class PreferenceConflict(MealPlannerError):
    """The generated recipe conflicts with household preferences."""


NON_VEGETARIAN = {
    "saumon",
    "salmon",
    "poulet",
    "chicken",
    "bœuf",
    "beef",
    "porc",
    "pork",
    "jambon",
    "ham",
    "lardons",
    "bacon",
    "thon",
    "tuna",
    "crevettes",
    "shrimp",
    "agneau",
    "lamb",
    "gélatine",
    "gelatin",
    "poisson",
    "fish",
}


def preference_conflicts(
    meals: list[RequestedMeal],
    settings: dict,
    meal_offset: int = 0,
) -> list[dict]:
    """Return actionable feedback with global meal positions for recipe repair."""
    conflicts = []
    for meal_index, meal in enumerate(meals, meal_offset):
        recipe = meal.recipe
        if recipe is None:
            continue
        excluded = exclusion_labels(settings, meal_index)
        texts = [recipe.title, recipe.subtitle, *recipe.steps]
        for ingredient in recipe.ingredients:
            texts.extend(food_terms(ingredient.name))
        foods = sorted(
            {term for text in texts for term in conflicting_terms(text, excluded)}
        )
        vegetarian = settings.get("vegetarian", False) and (
            not recipe.vegetarian
            or any(
                re.search(rf"\b{re.escape(name)}\b", ingredient.name.casefold())
                for ingredient in recipe.ingredients
                for name in NON_VEGETARIAN
            )
        )
        if foods or vegetarian:
            conflicts.append(
                {
                    "meal_index": meal_index,
                    "title": meal.title,
                    "excluded_foods_found": foods,
                    "requires_vegetarian": vegetarian,
                }
            )
    return conflicts


def check_preferences(
    meals: list[RequestedMeal],
    settings: dict,
    meal_offset: int = 0,
) -> None:
    conflicts = preference_conflicts(meals, settings, meal_offset)
    if not conflicts:
        return
    if conflicts[0]["requires_vegetarian"]:
        raise PreferenceConflict(
            source_text("text.the_proposed_recipe_does_not_respect_the_vegetarian_diet")
        )
    raise PreferenceConflict(
        source_text(
            "text.the_proposed_recipe_contains_an_excluded_household_food_specify"
        )
    )
