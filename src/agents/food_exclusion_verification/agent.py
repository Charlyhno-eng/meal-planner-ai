"""Check household food exclusions independently of LLM instructions."""

from collections.abc import Iterable

from src.agents.food_preferences import PreferenceConflict
from src.domain.dietary import conflicting_terms
from src.domain.foods import food_terms
from src.models.coordinator import GroceryAdd, RequestedMeal, ShoppingItem
from src.models.household import exclusion_labels
from src.models.recipes import Ingredient


class FoodExclusionConflict(PreferenceConflict):
    """A recipe or grocery item contains a food the household avoids."""


def check_food_exclusions(
    meals: Iterable[RequestedMeal],
    groceries: Iterable[Ingredient | ShoppingItem | GroceryAdd],
    settings: dict,
    meal_offset: int = 0,
) -> None:
    """Reject conflicts, including recipe ingredients already covered by stock.

    Use the shared French/English vocabulary and gluten/lactose source mapping.
    Personal and household-wide food exclusions are both checked.
    """

    def verify(texts, excluded):
        if any(conflicting_terms(text, excluded) for text in texts):
            raise FoodExclusionConflict(
                "Les recettes ou la liste de courses contiennent "
                "un aliment que le foyer souhaite éviter. "
                "Précisez une variante et réessayez."
            )

    for index, meal in enumerate(meals, meal_offset):
        if meal.recipe is None:
            continue
        recipe = meal.recipe
        texts = [recipe.title, recipe.subtitle, *recipe.steps]
        for ingredient in recipe.ingredients:
            texts.extend(food_terms(ingredient.name))
        verify(texts, exclusion_labels(settings, index))
    # Merged groceries serve several meals. Guest restrictions are checked on the
    # originating recipes, never globally against ingredients for other meals.
    verify(
        [text for item in groceries for text in food_terms(item.name)],
        exclusion_labels(settings),
    )
