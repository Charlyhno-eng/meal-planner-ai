"""Validated proposals returned by the local planning model."""

from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlanningSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: date
    days: int = Field(ge=1, le=14)
    count: int = Field(ge=1, le=28)
    people: int = Field(ge=1, le=12)
    vegetarian: bool
    dislikes: str = Field(max_length=1000)

    @model_validator(mode="after")
    def check_period(self):
        try:
            self.start + timedelta(days=self.days - 1)
        except OverflowError as exc:
            raise ValueError("Planning period exceeds supported dates") from exc
        return self


class PantryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    amount: float = Field(ge=0, le=100000, allow_inf_nan=False)
    unit: Literal["g", "ml", "pièce"]
    category: Literal["Épicerie", "Fruits & légumes", "Produits frais"]


class GuestMeal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meal: int = Field(ge=0, le=27)
    count: int = Field(ge=1, le=20)


class PlanningProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    settings: PlanningSettings
    recipe_ids: list[int] = Field(min_length=1, max_length=28)
    pantry_updates: list[PantryUpdate] = Field(max_length=100)
    guests: list[GuestMeal] = Field(max_length=28)

    @model_validator(mode="after")
    def check_meals(self):
        if len(self.recipe_ids) != self.settings.count:
            raise ValueError("Recipe count differs from meal count")
        if any(guest.meal >= self.settings.count for guest in self.guests):
            raise ValueError("Guest meal is outside the meal list")
        if len({guest.meal for guest in self.guests}) != len(self.guests):
            raise ValueError("Duplicate guest meal")
        return self


def validate_recipes(proposal: PlanningProposal, recipes: list[dict], english: dict):
    """Reject unknown recipes and exclusions independently of the LLM."""
    excluded = [
        word.strip().casefold()
        for word in proposal.settings.dislikes.split(",")
        if word.strip()
    ]
    for recipe_id in proposal.recipe_ids:
        if not 0 <= recipe_id < len(recipes):
            raise ValueError("Unknown recipe")
        recipe = recipes[recipe_id]
        if proposal.settings.vegetarian and not recipe["vegetarian"]:
            raise ValueError("Recipe is not vegetarian")
        if any(
            word in name.casefold() or word in english.get(name, name).casefold()
            for name, *_ in recipe["ingredients"]
            for word in excluded
        ):
            raise ValueError("Recipe contains an excluded ingredient")
