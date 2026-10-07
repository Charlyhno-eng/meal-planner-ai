"""Atomic JSON persistence for household profiles."""

import os
import tempfile
from pathlib import Path

from meal_planner_ai.models.household import Household


def load_household(path: Path) -> Household | None:
    if not path.exists():
        return None
    return Household.model_validate_json(path.read_text(encoding="utf-8"))


def save_household(path: Path, household: Household) -> None:
    validated = Household.model_validate(household.model_dump())
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(validated.model_dump_json(indent=2))
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
