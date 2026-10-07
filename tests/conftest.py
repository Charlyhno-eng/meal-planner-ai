"""A display-independent Qt application shared by desktop checks."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuickControls2 import QQuickStyle


@pytest.fixture(scope="session")
def qt_app():
    app = QGuiApplication.instance() or QGuiApplication([])
    QQuickStyle.setStyle("Basic")
    return app


@pytest.fixture
def sample_session(monkeypatch):
    """Inject examples explicitly; the application itself always starts empty."""
    import json
    from pathlib import Path

    from sample_data import PANTRY, RECIPES

    from src.ui.demo import DemoState
    from src.ui.i18n import ENGLISH

    translations = json.loads(
        Path(__file__).with_name("sample_translations.json").read_text("utf-8")
    )
    for source, target in translations.items():
        monkeypatch.setitem(ENGLISH, source, target)
    monkeypatch.setattr(DemoState, "recipe_catalogue", RECIPES)
    original = DemoState.__init__

    def initialize(self, *args, **kwargs):
        original(self, *args, **kwargs)
        self._pantry = [item.copy() for item in PANTRY]
        self._next_id = 7
        self._make_plan()

    monkeypatch.setattr(DemoState, "__init__", initialize)


@pytest.fixture
def fake_recipes(monkeypatch):
    """Generate deterministic test recipes, without making a provider request."""
    import json

    def respond(system, payload, api_key):
        return json.dumps(
            {
                "recipes": [
                    {
                        "title": meal["title"],
                        "servings": meal["servings"],
                        "subtitle": "Recette de test",
                        "minutes": 30,
                        "vegetarian": True,
                        "ingredients": [
                            {
                                "name": "Mascarpone",
                                "amount": 50 * meal["servings"],
                                "unit": "g",
                                "category": "Produits frais",
                            },
                            {
                                "name": "Sucre",
                                "amount": 10 * meal["servings"],
                                "unit": "g",
                                "category": "Épicerie",
                            },
                        ],
                        "steps": ["Mélanger les ingrédients et réserver au frais."],
                    }
                    for meal in payload["meals"]
                ]
            }
        )

    monkeypatch.setattr("src.agents.meal_planning.agent.complete_json", respond)
    return respond
