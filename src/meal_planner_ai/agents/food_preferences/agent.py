"""Reject incompatible recipes independently of model instructions."""

import re

from meal_planner_ai.domain.foods import food_terms
from meal_planner_ai.errors import MealPlannerError
from meal_planner_ai.models.coordinator import RequestedMeal


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


def check_preferences(meals: list[RequestedMeal], settings: dict) -> None:
    excluded = [
        word.strip().casefold()
        for word in settings["dislikes"].split(",")
        if word.strip()
    ]
    for meal in meals:
        recipe = meal.recipe
        if recipe is None:
            continue
        if settings["vegetarian"] and (
            not recipe.vegetarian
            or any(
                re.search(rf"\b{re.escape(name)}\b", ingredient.name.casefold())
                for ingredient in recipe.ingredients
                for name in NON_VEGETARIAN
            )
        ):
            raise PreferenceConflict(
                "La recette proposée ne respecte pas le régime végétarien. "
                "Précisez une variante et réessayez."
            )
        texts = [recipe.title, recipe.subtitle, *recipe.steps]
        for ingredient in recipe.ingredients:
            texts.extend(food_terms(ingredient.name))
        if any(word in text.casefold() for word in excluded for text in texts):
            raise PreferenceConflict(
                "La recette proposée contient un aliment exclu du foyer. "
                "Précisez une variante et réessayez."
            )
