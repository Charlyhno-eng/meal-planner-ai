"""Deterministic verification of recipes and groceries against food exclusions."""

from src.agents.food_exclusion_verification.agent import (
    FoodExclusionConflict,
    check_food_exclusions,
)

__all__ = ["FoodExclusionConflict", "check_food_exclusions"]
