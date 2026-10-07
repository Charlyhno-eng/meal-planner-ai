"""Read and atomically write the application's local language preference."""

import json
import os
import tempfile
import tomllib
from pathlib import Path

LANGUAGES = {"fr", "en"}


def load_language(path: Path) -> str:
    if not path.exists():
        save_language(path, "fr")
        return "fr"
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    language = config.get("application", {}).get("language", "fr")
    if language not in LANGUAGES:
        raise ValueError("Unsupported application language")
    return language


def save_language(path: Path, language: str) -> None:
    if language not in LANGUAGES:
        raise ValueError("Unsupported application language")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(f'[application]\nlanguage = "{language}"\n')
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


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
