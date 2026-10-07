"""Validated household profiles and shared ingredient exclusions."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HouseholdMember(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(default="", max_length=100)
    intolerances: str = Field(default="", max_length=1000)


class Household(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    people: int = Field(ge=1, le=12)
    members: list[HouseholdMember] = Field(min_length=1, max_length=12)
    vegetarian: bool = False
    dislikes: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def matching_size(self):
        if len(self.members) != self.people:
            raise ValueError("Household size differs from member count")
        return self


def excluded_terms(settings: dict) -> list[str]:
    """Combine shared exclusions and every member's comma-separated intolerances."""
    values = [settings.get("dislikes", "")]
    values.extend(member["intolerances"] for member in settings.get("members", []))
    terms = {word.strip().casefold() for value in values for word in value.split(",")}
    terms.discard("")
    # Common intolerance labels also exclude their usual ingredient sources.
    sources = {
        "gluten": (
            "blé",
            "wheat",
            "orge",
            "barley",
            "seigle",
            "rye",
            "farine",
            "flour",
            "pain",
            "bread",
            "pâtes",
            "pasta",
            "semoule",
            "couscous",
            "biscuit",
        ),
        "lactose": (
            "lait",
            "milk",
            "crème",
            "cream",
            "beurre",
            "butter",
            "fromage",
            "cheese",
            "yaourt",
            "yogurt",
            "mascarpone",
            "feta",
            "parmesan",
        ),
    }
    for label, ingredients in sources.items():
        if label in terms:
            terms.update(ingredients)
    return sorted(terms)
