"""Offline boundaries, proposal validation, and the home-page planning flow."""

import json
from contextlib import contextmanager
from pathlib import Path
from urllib.error import URLError

import pytest
from pydantic import ValidationError
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from sample_data import RECIPES
from test_bootstrap import visual_child

from meal_planner_ai.models.coordinator import CoordinatorProposal
from meal_planner_ai.models.planning import PlanningProposal
from meal_planner_ai.ui import app
from meal_planner_ai.ui.demo import DemoState
from meal_planner_ai.ui.i18n import ENGLISH
from meal_planner_ai.ui.speech import MODEL_FILES, LocalParakeet
from meal_planner_ai.workflow.planning import ask_local_model, build_planning_workflow


def proposal(**changes):
    data = {
        "settings": {
            "start": "2026-10-07",
            "days": 2,
            "count": 2,
            "people": 3,
            "vegetarian": True,
            "dislikes": "mushrooms",
        },
        "recipe_ids": [0, 2],
        "pantry_updates": [
            {"name": "Rice", "amount": 1000, "unit": "g", "category": "Épicerie"}
        ],
        "guests": [{"meal": 1, "count": 2}],
    }
    data.update(changes)
    return PlanningProposal.model_validate(data)


def test_workflow_validates_llm_and_apply_updates_quantities_atomically(qt_app):
    demo = DemoState()
    before = demo.planning_context()
    graph = build_planning_workflow(
        RECIPES, ENGLISH, reason=lambda state: {"proposal": proposal()}
    )
    result = graph.invoke({"request": "test", "context": before})["proposal"]
    assert demo.planning_context() == before  # Reasoning never mutates session state.
    demo.apply_proposal(result)
    assert len(demo.meals) == 2
    assert demo.meals[1]["servings"] == 5
    rice = next(item for item in demo.pantry if item["name"] == "Riz")
    assert rice["amount"] == 1000
    quinoa = next(item for item in demo.groceries if item["name"] == "Quinoa")
    assert quinoa["quantity"] == "240 g"
    rice = next(item for item in demo.groceries if item["name"] == "Riz")
    assert rice["quantity"] == "350 g"
    assert rice["available"] is True
    assert demo._guests == {1: 2}


@pytest.mark.parametrize("ids", [[0, 99], [0, -1], [0, 4], [0, 5]])
def test_incompatible_proposals_cannot_modify_plan(qt_app, ids):
    demo = DemoState()
    before = demo.planning_context(), demo.meals
    invalid = proposal(recipe_ids=ids)
    graph = build_planning_workflow(
        RECIPES, ENGLISH, reason=lambda state: {"proposal": invalid}
    )
    with pytest.raises(ValueError):
        graph.invoke({"request": "test", "context": demo.planning_context()})
    with pytest.raises(ValueError):
        demo.apply_proposal(invalid)
    assert (demo.planning_context(), demo.meals) == before


def test_invalid_period_guest_and_duplicate_pantry(qt_app):
    with pytest.raises(ValidationError):
        proposal(recipe_ids=[0])
    with pytest.raises(ValidationError):
        proposal(guests=[{"meal": 2, "count": 1}])
    with pytest.raises(ValidationError):
        proposal(guests=[{"meal": 1, "count": 1}, {"meal": 1, "count": 2}])
    data = proposal().model_dump(mode="json")
    data["settings"]["days"] = 1
    data["settings"]["count"] = 3
    data["recipe_ids"] = [0, 1, 2]
    flexible = PlanningProposal.model_validate(data)
    assert flexible.settings.count == 3
    data["settings"]["start"] = "9999-12-31"
    data["settings"]["days"] = 2
    with pytest.raises(ValidationError):
        PlanningProposal.model_validate(data)
    demo = DemoState()
    before = demo.planning_context()
    update = proposal().pantry_updates[0].model_dump()
    with pytest.raises(ValueError):
        demo.apply_proposal(proposal(pantry_updates=[update, update]))
    assert demo.planning_context() == before


def test_ollama_uses_loopback_structured_output_without_pulling_models(monkeypatch):
    calls = []

    @contextmanager
    def respond(request, timeout):
        import io

        calls.append((request.full_url, json.loads(request.data), timeout))
        yield io.StringIO(
            json.dumps({"message": {"content": proposal().model_dump_json()}})
        )

    monkeypatch.setattr("meal_planner_ai.workflow.planning.urlopen", respond)
    monkeypatch.setenv("MEAL_PLANNER_OLLAMA_MODEL", "installed-model")
    result = ask_local_model({"request": "two meals", "context": {}})
    assert result["proposal"] == proposal()
    url, payload, timeout = calls[0]
    assert url == "http://127.0.0.1:11434/api/chat"
    assert payload["model"] == "installed-model"
    assert payload["format"] == PlanningProposal.model_json_schema()
    assert payload["stream"] is False
    assert timeout == 120

    def unavailable(*args, **kwargs):
        raise URLError("offline")

    monkeypatch.setattr("meal_planner_ai.workflow.planning.urlopen", unavailable)
    with pytest.raises(RuntimeError, match="Ollama indisponible"):
        ask_local_model({"request": "test", "context": {}})


def test_missing_local_parakeet_never_attempts_loading(tmp_path, monkeypatch):
    speech = LocalParakeet(tmp_path / "missing")
    with pytest.raises(RuntimeError, match="paramètres"):
        speech.transcribe(b"\x00\x00" * 1600, 16000)
    assert not speech.path.exists()


def test_model_download_installs_complete_export_and_cleans_failed_transfer(
    tmp_path, monkeypatch
):
    import io

    from meal_planner_ai.ui.speech import MODEL_URL

    speech = LocalParakeet(tmp_path / "model")
    calls = []
    fail = True

    @contextmanager
    def respond(url, timeout):
        calls.append(url)
        assert timeout == 60
        if fail and url.endswith("encoder-model.onnx.data"):
            raise URLError("offline")
        response = io.BytesIO(b"model data")
        response.headers = {"Content-Length": "10"}
        yield response

    monkeypatch.setattr("meal_planner_ai.ui.speech.urlopen", respond)
    with pytest.raises(URLError):
        speech.download()
    assert not speech.is_installed()
    assert list(speech.path.iterdir()) == []
    assert list(tmp_path.iterdir()) == [speech.path]
    fail = False
    speech.download()
    assert speech.is_installed()
    assert calls[-len(MODEL_FILES) :] == [f"{MODEL_URL}/{n}" for n in MODEL_FILES]
    assert all((speech.path / n).read_bytes() == b"model data" for n in MODEL_FILES)

    # Truncated responses must not replace an existing installation.
    @contextmanager
    def truncated(url, timeout):
        response = io.BytesIO(b"short")
        response.headers = {"Content-Length": "10"}
        yield response

    monkeypatch.setattr("meal_planner_ai.ui.speech.urlopen", truncated)
    with pytest.raises(RuntimeError, match="Incomplete"):
        speech.download()
    assert all((speech.path / n).read_bytes() == b"model data" for n in MODEL_FILES)


def test_parakeet_uses_local_only_loader_and_pcm(tmp_path, monkeypatch):
    import numpy as np
    import onnx_asr

    for name in MODEL_FILES:
        (tmp_path / name).write_text("placeholder")
    calls = []

    class Model:
        def recognize(self, samples, sample_rate):
            assert samples.dtype == np.float32
            assert samples.tolist() == [0.0, 0.5, -0.5]
            assert sample_rate == 16000
            return " Deux repas. "

    def load(model, path, providers):
        calls.append((model, path, providers))
        return Model()

    monkeypatch.setattr(onnx_asr, "load_model", load)
    speech = LocalParakeet(tmp_path)
    pcm = np.array([0, 16384, -16384], dtype="<i2").tobytes()
    assert speech.transcribe(pcm, 16000) == "Deux repas."
    assert speech.transcribe(pcm, 16000) == "Deux repas."
    assert calls == [("nemo-conformer-tdt", tmp_path, ["CPUExecutionProvider"])]


def wait_for_job(assistant):
    for _ in range(100):
        QTest.qWait(10)
        if not assistant.busy:
            return
    pytest.fail("Background job did not finish")


def test_home_dictation_and_automatic_application(qt_app, monkeypatch, fake_recipes):
    demo = DemoState()
    assistant = demo.assistant
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(str(e) for e in errors))
    engine.setInitialProperties({"demo": demo})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    assert len(engine.rootObjects()) == 1, warnings
    window = engine.rootObjects()[0]
    window.setWidth(960)
    window.setHeight(700)
    before = demo.settings
    demo.setGlmApiKey("test-key")
    try:
        assert window.property("currentPage") == 5
        request = visual_child(window.contentItem(), "planningRequest")
        pantry = visual_child(window.contentItem(), "pantryRequest")
        groceries = visual_child(window.contentItem(), "groceryRequest")
        pantry.setProperty("text", "500 g de riz")
        groceries.setProperty("text", "Trois pommes")
        request.setProperty("text", "Deux repas")
        assistant.transcribed.emit("pour trois personnes")
        assert request.property("text") == "Deux repas pour trois personnes"

        monkeypatch.setattr(
            "meal_planner_ai.providers.glm.urlopen",
            lambda *args, **kwargs: (_ for _ in ()).throw(URLError("offline")),
        )
        assistant.plan(request.property("text"))
        wait_for_job(assistant)
        assert "GLM" in assistant.error
        assert demo.settings == before
        assert request.property("text") == "Deux repas pour trois personnes"

        monkeypatch.setattr(
            "meal_planner_ai.workflow.coordinator.interpret_request",
            lambda state, key: {
                "proposal": CoordinatorProposal(
                    actions=[
                        {"service": "meal_request", "title": "Tiramisu", "servings": 6}
                    ]
                )
            },
        )
        assistant.plan(request.property("text"))
        wait_for_job(assistant)
        assert not assistant.error
        assert not assistant.proposal
        assert demo.meals[-1]["servings"] == 6
        assert demo.meals[-1]["title"] == "Tiramisu"
        assert request.property("text") == ""
        assert pantry.property("text") == "500 g de riz"
        assert groceries.property("text") == "Trois pommes"
        assert assistant.completedActions
        assert demo.settings == before
        request.setProperty("text", "Une autre demande")
        assert not assistant.completedActions
        assistant.plan(request.property("text"))
        wait_for_job(assistant)
        demo.setLanguage("en")
        QTest.qWait(10)
        assert window.property("currentPage") == 5
        assert demo.settings == before
        assert len(demo.meals) == 9
        assert not assistant.proposal
        assert "Request saved" in assistant.reply
        window.setProperty("currentPage", 5)
        QTest.qWait(10)
        button = visual_child(window.contentItem(), "dictationButton")
        monkeypatch.setattr(
            assistant.speech, "path", Path("/tmp/no-such-parakeet-model")
        )
        button.clicked.emit()
        assert "missing" in assistant.error
        assert not assistant.recording
        assert window.property("currentPage") == 4
        QTest.qWait(10)
        download = visual_child(window.contentItem(), "downloadParakeetButton")
        assert download.isEnabled()
        # The UI starts an explicit worker; errors remain visible and allow retry.
        calls = []

        def fail_download():
            calls.append(True)
            raise OSError("offline")

        monkeypatch.setattr(assistant.speech, "download", fail_download)
        position = download.mapToScene(QPoint(20, 20))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position.toPoint())
        wait_for_job(assistant)
        assert calls == [True]
        assert "Download failed" in assistant.modelError
        assert download.isEnabled()

        monkeypatch.setattr(assistant.speech, "download", lambda: calls.append(True))
        monkeypatch.setattr(assistant.speech, "is_installed", lambda: len(calls) == 2)
        assistant.downloadModel()
        wait_for_job(assistant)
        assert assistant.modelInstalled
        assert not assistant.modelError
        assert not download.isEnabled()
        assert not warnings, "\n".join(warnings)
    finally:
        assistant.shutdown()
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def test_microphone_capture_stop_cancel_and_duration_limit(qt_app, monkeypatch):
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Signal
    from PySide6.QtMultimedia import QAudio, QAudioFormat

    import meal_planner_ai.ui.assistant as bridge

    demo = DemoState()
    assistant = demo.assistant
    captured = []
    texts = []
    assistant.transcribed.connect(texts.append)
    monkeypatch.setattr(assistant.speech, "check_available", lambda: None)

    def transcribe(pcm, rate):
        captured.append((len(pcm), rate))
        return "Planifie trois repas"

    monkeypatch.setattr(assistant.speech, "transcribe", transcribe)

    class Device:
        def isNull(self):
            return False

        def isFormatSupported(self, audio_format):
            assert audio_format.sampleRate() == 16000
            assert audio_format.channelCount() == 1
            assert audio_format.sampleFormat() == QAudioFormat.Int16
            return True

    class Source(QObject):
        stateChanged = Signal(object)
        data = b"\x00\x00" * 16000

        def __init__(self, device, audio_format, parent):
            super().__init__(parent)
            self.buffer = QBuffer(self)
            self.buffer.setData(QByteArray(self.data))
            self.buffer.open(QIODevice.ReadOnly)

        def start(self):
            return self.buffer

        def stop(self):
            self.buffer.close()

        def error(self):
            return QAudio.NoError

    class Application:
        def checkPermission(self, permission):
            return Qt.PermissionStatus.Granted

    class Gui:
        @staticmethod
        def instance():
            return Application()

    monkeypatch.setattr(bridge, "QGuiApplication", Gui)
    monkeypatch.setattr("PySide6.QtMultimedia.QMediaDevices.defaultAudioInput", Device)
    monkeypatch.setattr("PySide6.QtMultimedia.QAudioSource", Source)
    try:
        assistant.startDictation()
        assert assistant.recording
        assistant.stopDictation()
        wait_for_job(assistant)
        assert captured == [(32000, 16000)]
        assert texts == ["Planifie trois repas"]
        assert not assistant.recording
        assistant.startDictation()
        assistant.cancelDictation()
        assert not assistant.recording
        assert not assistant._pcm
        assert captured == [(32000, 16000)]
        Source.data = b"\x00\x00" * (16000 * 21)
        assistant.startDictation()
        assistant._read_audio()
        assert assistant.recording
        assert assistant._timer.interval() == 300000
        assistant.stopDictation()
        wait_for_job(assistant)
        assert captured[-1] == (672000, 16000)
        Source.data = b"\x00\x00" * (16000 * 301)
        assistant.startDictation()
        assistant._read_audio()
        wait_for_job(assistant)
        assert captured[-1] == (bridge.MAX_DICTATION_BYTES, 16000)
        assert not assistant.recording
        Source.data = b"\x00\x00"
        assistant.startDictation()
        assistant.stopDictation()
        assert "court" in assistant.error
        assert len(captured) == 3
    finally:
        assistant.shutdown()


pytestmark = pytest.mark.usefixtures("sample_session")


def test_proposal_review_has_no_assigned_dates_and_keeps_recipe_order(qt_app):
    demo = DemoState()
    demo.assistant._proposal = proposal(recipe_ids=[2, 0])
    assert demo.assistant.proposal["titles"] == [
        "Repas 1 · Curry de lentilles",
        "Repas 2 · Bowl aux légumes rôtis",
    ]
    demo.setLanguage("en")
    assert demo.assistant.proposal["titles"] == [
        "Meal 1 · Lentil curry",
        "Meal 2 · Roasted vegetable bowl",
    ]
    demo.apply_proposal(demo.assistant._proposal)
    assert [meal["art"] for meal in demo.meals] == [2, 0]
    assert demo.meals[1]["servings"] == 5


@pytest.mark.parametrize("missing", ["onnx_asr", "onnxruntime", "numpy"])
def test_missing_speech_dependencies_explain_standard_setup(
    tmp_path, monkeypatch, missing
):
    for name in MODEL_FILES:
        (tmp_path / name).write_text("placeholder")
    monkeypatch.setattr(
        "meal_planner_ai.ui.speech.find_spec",
        lambda module: None if module == missing else object(),
    )
    with pytest.raises(RuntimeError, match="uv sync --locked") as error:
        LocalParakeet(tmp_path).check_available()
    assert "--extra" not in str(error.value)


def test_home_progress_panel_requires_content(qt_app):
    demo = DemoState()
    engine = QQmlApplicationEngine()
    engine.setInitialProperties({"demo": demo})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    window = engine.rootObjects()[0]
    try:
        panel = visual_child(window.contentItem(), "assistantProgressPanel")
        assert not panel.property("visible")
        demo.assistant._busy = True
        demo.assistant.changed.emit()
        assert not panel.property("visible")
        demo.assistant._status = "Préparation de votre demande et du contexte du foyer…"
        demo.assistant.changed.emit()
        assert panel.property("visible")
        demo.assistant._busy = False
        demo.assistant._status = ""
        demo.assistant._steps = ["Terminé : les changements ont été enregistrés."]
        demo.assistant.changed.emit()
        assert panel.property("visible")
        demo.assistant.discard()
        assert not panel.property("visible")
    finally:
        demo.assistant.shutdown()
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
