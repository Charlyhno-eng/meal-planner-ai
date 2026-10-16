"""Read and atomically write local provider credentials."""

import json
import os
import tempfile
from pathlib import Path


def load_glm_key(path: Path) -> str:
    if not path.exists():
        return ""
    key = json.loads(path.read_text(encoding="utf-8"))["api_key"]
    if not isinstance(key, str):
        raise ValueError("Invalid GLM API key")
    return key


def save_glm_key(path: Path, key: str) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(
                {"name": "GLM_ai", "model": "glm-5.3-flash", "api_key": key}, stream
            )
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
