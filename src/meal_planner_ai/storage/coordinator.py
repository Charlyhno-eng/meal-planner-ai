"""Validated local coordinator records, saved with an atomic replacement."""

import os
import tempfile
from pathlib import Path

from meal_planner_ai.models.coordinator import CoordinatorData


def load_coordinator(path: Path) -> CoordinatorData:
    if not path.exists():
        return CoordinatorData()
    return CoordinatorData.model_validate_json(path.read_text(encoding="utf-8"))


def save_coordinator(path: Path, data: CoordinatorData) -> None:
    validated = CoordinatorData.model_validate(data.model_dump())
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
