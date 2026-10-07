"""Complete, validated output of the desktop agent workflow."""

from pydantic import Field, model_validator

from src.models.coordinator import (
    CommandModel,
    CoordinatorProposal,
    RequestedMeal,
)
from src.models.groceries import GroceryRequirement


class MealExecution(CommandModel):
    commands: CoordinatorProposal
    meals: list[RequestedMeal] = Field(default_factory=list, max_length=50)
    groceries: list[GroceryRequirement] = Field(default_factory=list, max_length=5000)

    @model_validator(mode="after")
    def complete_meals(self):
        requests = [a for a in self.commands.actions if a.service == "meal_request"]
        if len(requests) != len(self.meals):
            raise ValueError("Missing planned meal")
        for request, meal in zip(requests, self.meals, strict=True):
            if (
                meal.recipe is None
                or request.title != meal.title
                or request.servings != meal.servings
                or request.period != meal.period
            ):
                raise ValueError("Planned meal differs from the coordinator command")
        if self.commands.clarification and self.groceries:
            raise ValueError("A clarification cannot change groceries")
        return self
