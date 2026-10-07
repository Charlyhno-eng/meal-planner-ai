"""Validated recipe output; ingredient quantities cover all recipe servings."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from meal_planner_ai.domain.foods import canonical_food


class RecipeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Ingredient(RecipeModel):
    name: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0, le=100000, allow_inf_nan=False, strict=True)
    unit: Literal["g", "ml", "pièce"]
    category: Literal["Épicerie", "Fruits & légumes", "Produits frais"]


class Recipe(RecipeModel):
    title: str = Field(min_length=1, max_length=100)
    servings: int = Field(ge=1, le=32, strict=True)
    subtitle: str = Field(min_length=1, max_length=300)
    minutes: int = Field(ge=1, le=1440, strict=True)
    vegetarian: bool = Field(strict=True)
    ingredients: list[Ingredient] = Field(min_length=1, max_length=100)
    steps: list[str] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def validate_content(self):
        if any(not step.strip() or len(step) > 2000 for step in self.steps):
            raise ValueError("Empty or oversized recipe step")
        keys = []
        for ingredient in self.ingredients:
            ingredient.name = canonical_food(ingredient.name)
            keys.append((ingredient.name.casefold(), ingredient.unit))
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate recipe ingredient")
        return self


class RecipeBatch(RecipeModel):
    recipes: list[Recipe] = Field(min_length=1, max_length=50)
