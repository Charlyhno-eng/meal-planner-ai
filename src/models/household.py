"""Validated household profiles and shared ingredient exclusions."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domain.dietary import expand_terms


class HouseholdMember(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(default="", max_length=100)
    intolerances: str = Field(default="", max_length=1000)


class GuestGroup(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(default="", max_length=100)
    meals: list[int] = Field(min_length=1, max_length=28)
    members: list[HouseholdMember] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def valid_meals(self):
        if len(set(self.meals)) != len(self.meals) or any(
            type(index) is not int or not 0 <= index < 1000 for index in self.meals
        ):
            raise ValueError("Choose distinct meal positions")
        return self


class Household(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    people: int = Field(ge=1, le=12)
    members: list[HouseholdMember] = Field(min_length=1, max_length=12)
    guest_groups: list[GuestGroup] = Field(default_factory=list, max_length=28)
    vegetarian: bool = False
    dislikes: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def matching_size(self):
        if len(self.members) != self.people:
            raise ValueError("Household size differs from member count")
        return self


def meal_guests(settings: dict, meal_index: int) -> list[dict]:
    """Resolve attendees from the same global meal positions used by the UI."""
    return [
        member
        for group in settings.get("guest_groups", [])
        if meal_index in group["meals"]
        for member in group["members"]
    ]


def exclusion_labels(settings: dict, meal_index: int | None = None) -> list[str]:
    """Household exclusions always apply; guests apply only at their chosen meals."""
    members = list(settings.get("members", []))
    if meal_index is not None:
        members.extend(meal_guests(settings, meal_index))
    values = [settings.get("dislikes", "")]
    values.extend(member.get("intolerances", "") for member in members)
    return list(
        dict.fromkeys(
            word.strip()
            for value in values
            for word in value.split(",")
            if word.strip()
        )
    )


def excluded_terms(settings: dict, meal_index: int | None = None) -> list[str]:
    return expand_terms(exclusion_labels(settings, meal_index))
