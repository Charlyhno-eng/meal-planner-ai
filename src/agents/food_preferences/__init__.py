"""Deterministic checks of household exclusions and vegetarian settings."""

from src.agents.food_preferences.agent import (
    PreferenceConflict,
    check_preferences,
)

__all__ = ["PreferenceConflict", "check_preferences"]
