"""Aggregate ingredient needs; stock is shared once across the whole plan."""

import math
from collections import defaultdict

from meal_planner_ai.domain.foods import canonical_food
from meal_planner_ai.models.groceries import GroceryRequirement
from meal_planner_ai.models.recipes import Ingredient


def calculate_groceries(
    ingredients: list[Ingredient], pantry: list[dict]
) -> list[GroceryRequirement]:
    needed = defaultdict(float)
    stock = defaultdict(float)
    foods = {}
    for ingredient in ingredients:
        ingredient = Ingredient.model_validate(ingredient.model_dump())
        name = canonical_food(ingredient.name)
        key = (name.casefold(), ingredient.unit)
        needed[key] += ingredient.amount
        foods.setdefault(key, (name, ingredient.category))
    for item in pantry:
        key = (canonical_food(item["name"]).casefold(), item["unit"])
        amount = item["amount"]
        if (
            not isinstance(amount, (int, float))
            or not math.isfinite(amount)
            or amount < 0
        ):
            raise ValueError("Invalid pantry quantity")
        stock[key] += amount
    result = []
    for key, required in needed.items():
        available = min(required, stock[key])
        missing = max(0, required - available)
        result.append(
            GroceryRequirement(
                name=foods[key][0],
                category=foods[key][1],
                unit=key[1],
                required=required,
                available=available,
                amount=math.ceil(missing) if key[1] == "pièce" else missing,
            )
        )
    return result
