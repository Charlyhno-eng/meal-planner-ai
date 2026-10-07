"""Shared GLM JSON transport. Never expose provider bodies or credentials."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from meal_planner_ai.errors import MealPlannerError

GLM_URL = "https://api.z.ai/api/paas/v4/chat/completions"
GLM_MODEL = "glm-5.3-flash"


class CoordinatorUnavailable(MealPlannerError):
    """A safe provider failure that may be displayed in the desktop."""


def complete_json(system: str, data: dict, api_key: str) -> str:
    if not api_key:
        raise CoordinatorUnavailable(
            "Enregistrez votre clé API GLM dans les paramètres."
        )
    payload = {
        "model": GLM_MODEL,
        "stream": False,
        "response_format": {"type": "json_object"},
        "reasoning_effort": "low",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
        ],
    }
    request = Request(
        GLM_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            result = json.load(response)
    except HTTPError as exc:
        if exc.code in (401, 403):
            message = "Clé API GLM refusée. Vérifiez les paramètres."
        else:
            message = "GLM indisponible. Réessayez plus tard."
        raise CoordinatorUnavailable(message) from None
    except (URLError, TimeoutError, OSError):
        raise CoordinatorUnavailable(
            "GLM indisponible. Vérifiez votre connexion."
        ) from None
    try:
        choice = result["choices"][0]
        if choice.get("finish_reason") != "stop":
            raise ValueError("Incomplete model output")
        content = choice["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("Missing JSON content")
        return content
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Invalid GLM response") from exc
