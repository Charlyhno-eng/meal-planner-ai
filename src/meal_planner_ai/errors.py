"""Errors whose messages may be shown to users without exposing model data."""


class MealPlannerError(RuntimeError):
    """A safe, actionable failure in the agent workflow."""
