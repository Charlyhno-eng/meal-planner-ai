"""Check household food exclusions independently of LLM instructions."""

from collections.abc import Iterable

from src.agents.food_preferences import PreferenceConflict
from src.domain.foods import food_terms
from src.models.coordinator import GroceryAdd, RequestedMeal, ShoppingItem
from src.models.household import excluded_terms
from src.models.recipes import Ingredient


class IntoleranceConflict(PreferenceConflict):
    """A recipe or grocery item conflicts with a household intolerance."""


def check_intolerances(
    meals: Iterable[RequestedMeal],
    groceries: Iterable[Ingredient | ShoppingItem | GroceryAdd],
    settings: dict,
) -> None:
    """Reject conflicts, including recipe ingredients already covered by stock.

    Use the shared French/English vocabulary and gluten/lactose source mapping.
    Legacy member intolerances and shared food exclusions are both checked.
    """
    excluded = excluded_terms(settings)
    if not excluded:
        return
    texts = []
    for meal in meals:
        if meal.recipe is None:
            continue
        recipe = meal.recipe
        texts.extend([recipe.title, recipe.subtitle, *recipe.steps])
        for ingredient in recipe.ingredients:
            texts.extend(food_terms(ingredient.name))
    for item in groceries:
        texts.extend(food_terms(item.name))
    if any(term in text.casefold() for term in excluded for text in texts):
        raise IntoleranceConflict(
            "Les recettes ou la liste de courses contiennent un aliment incompatible "
            "avec les intolérances du foyer. Précisez une variante et réessayez."
        )
