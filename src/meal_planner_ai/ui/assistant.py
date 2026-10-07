"""Qt bridge for local dictation, agent progress and automatic meal creation."""

from PySide6.QtCore import (
    Property,
    QMicrophonePermission,
    QObject,
    QRunnable,
    Qt,
    QThreadPool,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication

from meal_planner_ai.errors import MealPlannerError
from meal_planner_ai.models.coordinator import CoordinatorProposal
from meal_planner_ai.models.execution import MealExecution
from meal_planner_ai.models.planning import PlanningProposal
from meal_planner_ai.ui.speech import LocalParakeet, MissingParakeetError
from meal_planner_ai.workflow.meal_request import build_meal_workflow


class JobSignals(QObject):
    done = Signal(object, str)
    progress = Signal(str)


class Job(QRunnable):
    def __init__(self, operation, sanitize_errors=False, with_progress=False):
        super().__init__()
        self.operation = operation
        self.sanitize_errors = sanitize_errors
        self.with_progress = with_progress
        self.signals = JobSignals()

    def run(self):
        try:
            result = (
                self.operation(self.signals.progress.emit)
                if self.with_progress
                else self.operation()
            )
            self.signals.done.emit(result, "")
        except MealPlannerError as exc:
            self.signals.done.emit(None, str(exc))
        except Exception as exc:
            self.signals.done.emit(
                None,
                "Traitement impossible. Vérifiez la demande et réessayez."
                if self.sanitize_errors
                else str(exc),
            )


class PlanningAssistant(QObject):
    changed = Signal()
    transcribed = Signal(str)
    applied = Signal()
    modelSetupRequested = Signal()

    def __init__(self, store):
        super().__init__(store)
        self.store = store
        self.speech = LocalParakeet()
        self._busy = False
        self._recording = False
        self._error = ""
        self._proposal = None
        self._reply = ""
        self._status = ""
        self._steps = []
        self._completed_commands = None
        self._context = None
        self._conversation = []
        self._request = ""
        self._audio = None
        self._device = None
        self._pcm = bytearray()
        self._job = None
        self._permission_pending = False
        self._model_downloading = False
        self._model_error = ""
        self._pool = QThreadPool(self)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.stopDictation)
        self.store.changed.connect(self.changed)

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(bool, notify=changed)
    def recording(self):
        return self._recording

    @Property(str, notify=changed)
    def error(self):
        return self.store.translate(self._error)

    @Property(str, notify=changed)
    def reply(self):
        return self.store.translate(self._reply)

    @Property(str, notify=changed)
    def status(self):
        return self.store.translate(self._status)

    @Property("QVariantList", notify=changed)
    def steps(self):
        return [self.store.translate(step) for step in self._steps]

    @Property("QVariantList", notify=changed)
    def completedActions(self):
        if self._completed_commands is None:
            return []
        lines = []
        for action in self._completed_commands.actions:
            if action.service == "meal_request":
                line = self.store.translate("Repas ajouté") + f" : {action.title}"
            else:
                label = "À acheter" if action.service == "grocery_add" else "En réserve"
                line = (
                    self.store.translate(label)
                    + f" : {self.store.translate(action.name)}"
                )
            if action.service != "pantry_set":
                line += (
                    f" · {action.period.start.isoformat()}"
                    f" — {action.period.end.isoformat()}"
                )
            lines.append(line)
        return lines

    @Slot(str)
    def _progress(self, message):
        self._status = message
        self._steps.append(message)
        self.changed.emit()

    @Property(bool, notify=changed)
    def modelInstalled(self):
        return self.speech.is_installed()

    @Property(bool, notify=changed)
    def modelDownloading(self):
        return self._model_downloading

    @Property(str, notify=changed)
    def modelError(self):
        return self.store.translate(self._model_error)

    @Property(str, notify=changed)
    def modelPath(self):
        return str(self.speech.path.resolve())

    @Slot()
    def downloadModel(self):
        if self._busy or self._recording or self._permission_pending:
            return
        self._model_downloading = True
        self._model_error = ""
        self._status = "Téléchargement du modèle de dictée Parakeet…"
        self._run(self.speech.download, self._model_downloaded)

    @Slot(object, str)
    def _model_downloaded(self, result, error):
        self._busy = False
        self._job = None
        self._model_downloading = False
        self._status = ""
        self._model_error = (
            "Téléchargement impossible. Vérifiez la connexion et l’espace disque, "
            "puis réessayez."
            if error
            else ""
        )
        self.changed.emit()

    @Property("QVariantMap", notify=changed)
    def proposal(self):
        if self._proposal is None:
            return {}
        result = self._proposal.model_dump(mode="json")
        if isinstance(self._proposal, CoordinatorProposal):
            result["titles"] = []
            for action in self._proposal.actions:
                if action.service == "meal_request":
                    line = (
                        self.store.translate("Repas souhaité")
                        + f" : {action.title} · {action.servings}"
                        + self.store.translate(" pers.")
                    )
                else:
                    service = (
                        "À acheter" if action.service == "grocery_add" else "En réserve"
                    )
                    line = (
                        self.store.translate(service)
                        + f" : {self.store.translate(action.name)} · {action.amount:g}"
                        + f" {self.store.translate(action.unit)}"
                    )
                if action.service != "pantry_set":
                    line += (
                        f" · {action.period.start.isoformat()}"
                        f" — {action.period.end.isoformat()}"
                    )
                result["titles"].append(line)
            return result
        result["titles"] = []
        for index, recipe_id in enumerate(self._proposal.recipe_ids):
            title = self.store.translate(
                self.store.recipe_catalogue[recipe_id]["title"]
            )
            label = f"{self.store.translate('Repas ')}{index + 1}"
            result["titles"].append(f"{label} · {title}")
        return result

    def _run(self, operation, callback, sanitize_errors=False, with_progress=False):
        self._busy = True
        self._error = ""
        if not with_progress:
            self._steps = []
        self._job = Job(
            operation, sanitize_errors=sanitize_errors, with_progress=with_progress
        )
        self._job.signals.done.connect(callback)
        self._job.signals.progress.connect(self._progress)
        self.changed.emit()
        self._pool.start(self._job)

    @Slot(str)
    def plan(self, request):
        if self._busy or self._recording:
            return
        self._proposal = None
        self._reply = ""
        self._status = ""
        self._steps = []
        self._completed_commands = None
        if not request.strip():
            self._error = "Décrivez votre demande."
            self.changed.emit()
            return
        if len(request) > 8000:
            self._error = "La demande est trop longue (8 000 caractères maximum)."
            self.changed.emit()
            return
        if self.store.coordinatorError:
            self._error = self.store.coordinatorError
            self.changed.emit()
            return
        if not self.store.glmApiKey:
            self._error = "Enregistrez votre clé API GLM dans les paramètres."
            self.changed.emit()
            return
        context = self.store.planning_context()
        self._context = context
        self._request = request.strip()
        conversation = self._conversation.copy()
        api_key = self.store.glmApiKey
        self._status = "Préparation de votre demande et du contexte du foyer…"
        self._run(
            lambda progress: build_meal_workflow(
                api_key=api_key, progress=progress
            ).invoke(
                {
                    "request": request.strip(),
                    "context": context,
                    "conversation": conversation,
                },
                {"recursion_limit": 60},
            )["result"],
            self._planned,
            sanitize_errors=True,
            with_progress=True,
        )

    @Slot(object, str)
    def _planned(self, proposal, error):
        self._busy = False
        self._job = None
        self._proposal = None
        self._error = error
        if not error:
            if isinstance(proposal, MealExecution):
                if proposal.commands.clarification:
                    proposal = proposal.commands
                else:
                    if not self._context_matches():
                        self._error = (
                            "Les données ont changé. Envoyez à nouveau votre demande."
                        )
                    else:
                        try:
                            self._progress(
                                "Enregistrement des repas et actualisation des courses…"
                            )
                            self.store.apply_execution(proposal)
                        except OSError:
                            self._error = (
                                "Impossible d’enregistrer les demandes. Réessayez."
                            )
                        except MealPlannerError as exc:
                            self._error = str(exc)
                        except ValueError:
                            self._error = (
                                "La proposition IA est invalide. "
                                "Précisez la demande et réessayez."
                            )
                        else:
                            self._completed_commands = proposal.commands
                            self._conversation.clear()
                            self._reply = (
                                "Demande enregistrée. "
                                "Vos repas et vos courses sont à jour."
                            )
                            self._progress(
                                "Terminé : les changements ont été enregistrés."
                            )
                            self.applied.emit()
                    if self._error:
                        self._status = (
                            "Traitement interrompu. "
                            "Aucun changement n’a été enregistré."
                        )
                    self.changed.emit()
                    return
            if isinstance(proposal, CoordinatorProposal) and proposal.clarification:
                self._status = (
                    "Une précision est nécessaire avant de modifier vos données."
                )
                self._reply = proposal.clarification
                self._conversation = [
                    *self._conversation,
                    {"role": "user", "content": self._request},
                    {"role": "assistant", "content": self._reply},
                ][-6:]
            else:
                self._proposal = proposal
        if self._error:
            self._status = "Traitement interrompu. Aucun changement n’a été enregistré."
        self.changed.emit()

    def _context_matches(self):
        if self._context is None:
            return True
        # Switching interface language does not change ingredient quantities or dates.
        previous = {k: v for k, v in self._context.items() if k != "language"}
        current = {
            k: v for k, v in self.store.planning_context().items() if k != "language"
        }
        return previous == current

    @Slot()
    def discard(self):
        if self._busy:
            return
        self._proposal = None
        self._reply = ""
        self._completed_commands = None
        self._status = ""
        self._steps = []
        self.changed.emit()

    @Slot()
    def apply(self):
        if self._proposal is None or self._busy or self._recording:
            return
        if not self._context_matches():
            self._proposal = None
            self._error = "Les données ont changé. Envoyez à nouveau votre demande."
            self.changed.emit()
            return
        try:
            if isinstance(self._proposal, CoordinatorProposal):
                self.store.apply_commands(self._proposal)
            else:
                self.store.apply_proposal(
                    PlanningProposal.model_validate(self._proposal)
                )
        except OSError:
            self._error = "Impossible d’enregistrer les demandes. Réessayez."
        except ValueError:
            self._error = (
                "La proposition IA est invalide. Précisez la demande et réessayez."
            )
        else:
            self._proposal = None
            self._error = ""
            self._conversation.clear()
            self._reply = "Demande enregistrée dans les services concernés."
            self.applied.emit()
        self.changed.emit()

    @Slot()
    def startDictation(self):
        if self._busy or self._recording or self._permission_pending:
            return
        try:
            self.speech.check_available()
            app = QGuiApplication.instance()
            permission = QMicrophonePermission()
            if app.checkPermission(permission) == Qt.PermissionStatus.Undetermined:
                self._permission_pending = True
                app.requestPermission(permission, self, self._permission_result)
                return
            if app.checkPermission(permission) == Qt.PermissionStatus.Denied:
                raise RuntimeError("Autorisez l’accès au microphone pour dicter.")
            from PySide6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices

            device = QMediaDevices.defaultAudioInput()
            if device.isNull():
                raise RuntimeError(
                    "Aucun microphone disponible. Vérifiez les permissions."
                )
            audio_format = QAudioFormat()
            audio_format.setSampleRate(16000)
            audio_format.setChannelCount(1)
            audio_format.setSampleFormat(QAudioFormat.Int16)
            if not device.isFormatSupported(audio_format):
                raise RuntimeError(
                    "Le microphone ne prend pas en charge le format mono 16 kHz."
                )
            self._error = ""
            self._pcm.clear()
            self._recording = True
            self._audio = QAudioSource(device, audio_format, self)
            self._audio.stateChanged.connect(self._audio_state_changed)
            self._device = self._audio.start()
            if self._device is None:
                raise RuntimeError(
                    "Impossible d’ouvrir le microphone. Vérifiez les permissions."
                )
            self._device.readyRead.connect(self._read_audio)
            self._timer.start(20000)
        except MissingParakeetError as exc:
            self._error = str(exc)
            self.modelSetupRequested.emit()
        except Exception as exc:
            self._release_audio()
            self._error = str(exc)
        self.changed.emit()

    def _permission_result(self, permission):
        if not self._permission_pending:
            return
        self._permission_pending = False
        self.startDictation()

    @Slot()
    def _read_audio(self):
        if self._device is not None:
            # Bound recordings to 20 seconds of 16 kHz, signed 16-bit mono PCM.
            remaining = 640000 - len(self._pcm)
            self._pcm.extend(bytes(self._device.readAll())[:remaining])
            if len(self._pcm) >= 640000:
                self.stopDictation()

    def _release_audio(self):
        self._recording = False
        self._timer.stop()
        self._device = None
        if self._audio is not None:
            audio, self._audio = self._audio, None
            audio.stop()
            audio.deleteLater()

    def _audio_state_changed(self, state):
        from PySide6.QtMultimedia import QAudio

        if self._recording and self._audio and self._audio.error() != QAudio.NoError:
            self._release_audio()
            self._error = (
                "Erreur du microphone. Vérifiez le périphérique et les permissions."
            )
            self.changed.emit()

    @Slot()
    def cancelDictation(self):
        self._permission_pending = False
        self._release_audio()
        self._pcm.clear()
        self.changed.emit()

    @Slot()
    def stopDictation(self):
        if not self._recording:
            return
        # Drain any last samples without recursively invoking this slot.
        if self._device is not None:
            remaining = 640000 - len(self._pcm)
            self._pcm.extend(bytes(self._device.readAll())[:remaining])
        self._release_audio()
        pcm = bytes(self._pcm)
        self._pcm.clear()
        if len(pcm) < 3200:
            self._error = "Enregistrement trop court. Réessayez."
            self.changed.emit()
            return
        self._status = "Transcription locale de votre dictée avec Parakeet…"
        self._run(lambda: self.speech.transcribe(pcm, 16000), self._transcribed)

    @Slot(object, str)
    def _transcribed(self, text, error):
        self._busy = False
        self._job = None
        self._error = error
        self._status = ""
        if not error:
            self.transcribed.emit(text)
        self.changed.emit()

    @Slot()
    def shutdown(self):
        self.cancelDictation()
        # Keep worker signals alive until inference finishes, even when closing.
        self._pool.waitForDone()

    def connect_shutdown(self):
        app = QGuiApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.shutdown)
