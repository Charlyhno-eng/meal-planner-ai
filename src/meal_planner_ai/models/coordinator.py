"""Strict commands and service records for the coordinator."""

import re
from datetime import date
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from meal_planner_ai.models.recipes import Recipe


class CommandModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Period(CommandModel):
    start: date
    end: date

    @field_validator("start", "end", mode="before")
    @classmethod
    def iso_date(cls, value):
        if type(value) is date:
            return value
        if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return date.fromisoformat(value)
        raise ValueError("Use an ISO calendar date")

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start:
            raise ValueError("Period end precedes start")
        return self


PeriodRequest = Literal["current", "this_week", "next_week"] | Period
Name = Annotated[str, Field(min_length=1, max_length=100)]
Quantity = Annotated[float, Field(gt=0, le=100000, allow_inf_nan=False, strict=True)]
Unit = Literal["g", "ml", "pièce"]
Category = Literal["Épicerie", "Fruits & légumes", "Produits frais"]


class MealRequest(CommandModel):
    service: Literal["meal_request"]
    title: Name
    servings: int = Field(ge=1, le=32, strict=True)
    period: PeriodRequest = "current"


class GroceryAdd(CommandModel):
    service: Literal["grocery_add"]
    name: Name
    amount: Quantity
    unit: Unit
    category: Category
    period: PeriodRequest = "current"

    @model_validator(mode="after")
    def whole_pieces(self):
        if self.unit == "pièce" and not self.amount.is_integer():
            raise ValueError("Pieces require a whole quantity")
        return self


class PantrySet(CommandModel):
    service: Literal["pantry_set"]
    name: Name
    amount: float = Field(ge=0, le=100000, allow_inf_nan=False, strict=True)
    unit: Unit
    category: Category

    @model_validator(mode="after")
    def whole_pieces(self):
        if self.unit == "pièce" and not self.amount.is_integer():
            raise ValueError("Pieces require a whole quantity")
        return self


Action = Annotated[MealRequest | GroceryAdd | PantrySet, Field(discriminator="service")]


class CoordinatorProposal(CommandModel):
    actions: list[Action] = Field(default_factory=list, max_length=50)
    clarification: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def actions_or_question(self):
        if bool(self.actions) == bool(self.clarification):
            raise ValueError("Provide actions or a clarification, never both")
        return self


class RequestedMeal(CommandModel):
    id: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
    title: Name
    servings: int = Field(ge=1, le=32, strict=True)
    period: Period
    recipe: Recipe | None = None
    guests: int = Field(default=0, ge=0, le=12, strict=True)

    @model_validator(mode="after")
    def matching_recipe(self):
        if self.recipe and (
            self.recipe.servings != self.servings
            or self.recipe.title.casefold() != self.title.casefold()
        ):
            raise ValueError("Recipe differs from the requested meal")
        return self


class ShoppingItem(CommandModel):
    id: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
    name: Name
    amount: Quantity
    unit: Unit
    category: Category
    period: Period

    @model_validator(mode="after")
    def whole_pieces(self):
        if self.unit == "pièce" and not self.amount.is_integer():
            raise ValueError("Pieces require a whole quantity")
        return self


class CoordinatorData(CommandModel):
    version: Literal[1] = 1
    meals: list[RequestedMeal] = Field(default_factory=list, max_length=1000)
    groceries: list[ShoppingItem] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [item.id for item in [*self.meals, *self.groceries]]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate record id")
        return self
