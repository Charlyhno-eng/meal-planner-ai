"""Local Parakeet transcription with explicit model installation."""

import os
import shutil
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from src.localization import source_text

MODEL_NAME = "nemo-parakeet-tdt-0.6b-v3"
MODEL_FILES = (
    "config.json",
    "vocab.txt",
    "encoder-model.onnx",
    "decoder_joint-model.onnx",
    "encoder-model.onnx.data",
)
MODEL_URL = "https://huggingface.co/istupakov/parakeet-tdt-0.6b-v3-onnx/resolve/8f23f0c"


class MissingParakeetError(RuntimeError):
    pass


class LocalParakeet:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(
            os.environ.get("MEAL_PLANNER_PARAKEET_DIR", "models/parakeet-tdt-0.6b-v3")
        )
        self._model = None

    def is_installed(self):
        return all(
            (self.path / name).is_file() and (self.path / name).stat().st_size > 0
            for name in MODEL_FILES
        )

    def download(self):
        self.path.mkdir(parents=True, exist_ok=True)
        # Stage the entire export so a failed transfer never installs partial files.
        with TemporaryDirectory(prefix=".parakeet-", dir=self.path.parent) as staging:
            staging = Path(staging)
            for name in MODEL_FILES:
                with urlopen(f"{MODEL_URL}/{name}", timeout=60) as response:
                    with (staging / name).open("wb") as destination:
                        shutil.copyfileobj(response, destination)
                    expected = response.headers.get("Content-Length")
                    if expected and (staging / name).stat().st_size != int(expected):
                        raise RuntimeError("Incomplete model file")
                if not (staging / name).stat().st_size:
                    raise RuntimeError("Empty model file")
            for name in MODEL_FILES:
                (staging / name).replace(self.path / name)
        self._model = None

    def check_available(self):
        if not self.is_installed():
            raise MissingParakeetError(
                source_text("text.parakeet_tdt_0_6b_v3_is_missing_or_incomplete")
            )
        if any(
            find_spec(module) is None for module in ("onnx_asr", "onnxruntime", "numpy")
        ):
            raise RuntimeError(
                source_text(
                    "text.dictation_dependencies_are_missing_close_the_app_and_run"
                )
            )

    def transcribe(self, pcm: bytes, sample_rate: int) -> str:
        self.check_available()
        import numpy as np
        import onnx_asr

        if self._model is None:
            # A custom local model type never resolves a remote model repository.
            self._model = onnx_asr.load_model(
                "nemo-conformer-tdt", self.path, providers=["CPUExecutionProvider"]
            )
        samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768
        text = self._model.recognize(samples, sample_rate=sample_rate)
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(
                source_text("text.no_speech_recognized_try_again_near_the_microphone")
            )
        return text.strip()
