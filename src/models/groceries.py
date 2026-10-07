"""Requirements computed from recipes, separate from explicit purchases."""

import math

from pydantic import Field, model_validator

from src.models.recipes import Ingredient


class GroceryRequirement(Ingredient):
    required: float = Field(gt=0, le=10000000, allow_inf_nan=False)
    available: float = Field(ge=0, le=10000000, allow_inf_nan=False)
    # amount is the purchase quantity; zero means already covered by pantry.
    amount: float = Field(ge=0, le=10000000, allow_inf_nan=False)

    @model_validator(mode="after")
    def balanced(self):
        shortage = max(0, self.required - self.available)
        expected = math.ceil(shortage) if self.unit == "pièce" else shortage
        if not math.isclose(self.amount, expected):
            raise ValueError("Purchase quantity does not cover recipe requirements")
        return self
