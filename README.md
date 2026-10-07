# Meal Planner AI

A local desktop application for meal and grocery planning, built with Python,
LangGraph, Pydantic, and PySide6/QML, with local JSON storage for coordinator
meal requests and explicit grocery additions.

The desktop opens maximized and supports French and English. No demonstration
meals or inventory are supplied. The pantry, generated meal plan, guest list and
recipe catalogue start empty; they remain in memory for the session. Meal wishes
and explicit purchases created by the coordinator are restored from local JSON.
Language preferences and the GLM API key are also persisted.

## Desktop interface

- **AI assistant:** type or dictate a request, review the extracted actions, then
  apply them. The coordinator routes meal wishes, explicit purchases and pantry
  quantities to their services. It asks for clarification when data is ambiguous.
- **Planning:** choose a period (start date and 1–14 days), a meal count
  (1–28, independent of the number of days), and household size. Meals form a
  list for the whole period, without assigned days or lunch/dinner slots. Cook
  them in any order. Guests are attached to individual meals, and groceries
  cover the full list. Saving settings does not create meals when the catalogue
  is empty.
- **Pantry:** add, edit, search, filter, and remove your own foods.
- **Groceries:** includes explicit purchases even without recipes or planned
  meals. Each added purchase shows its period; check it off, copy it, or remove
  it. Recipe-based shortfalls remain separate from explicit purchases.
- **Household:** configure dietary preferences and exclusions. Guests can be
  assigned once planned meals are available.
- **Settings:** located at the bottom of the sidebar, change the language, save
  the GLM API key, and set up dictation.
- **AI interactions:** located immediately above Settings, inspect the planned
  five-agent architecture. The coordinator is implemented; the other agents
  remain planned. The map describes their roles and does not show live activity.

Use `Ctrl+1` for the assistant, `Ctrl+2` through `Ctrl+6` for Planning, Pantry,
Groceries, Household, and Settings, and `Ctrl+7` for AI interactions. Dialogs
can be closed with Escape. Form defaults, supported categories, translations,
and the architecture map remain part of the interface.

## Language configuration

The app creates `config.toml` in the working directory on its first launch (the
repository root when launched with the setup command below). It defaults to French:

```toml
[application]
language = "fr"
```

Choose `"fr"` or `"en"` in Settings, or edit the file while the app is closed.
Language changes are saved automatically with an atomic file replacement.
The local configuration file is ignored by Git. If it cannot be read, the app
uses French and displays an error in Settings. If a save fails, the current
language remains selected and the error is displayed.

## GLM API key settings

Settings includes a **GLM_ai / glm-5.3-flash** API key field. Enter or replace the
key and click **Save** (save an empty field to remove it). The field displays
password dots by default; the eye button shows or hides the key, and saving
hides it again. The key is restored on the next launch.

Credentials are stored in plain text in `glm-credentials.json` beside
`config.toml`, with owner-only permissions when saved, and ignored by Git.
The coordinator uses this key with **glm-5.3-flash** through the
[Z.AI chat completion API](https://docs.z.ai/api-reference/llm/chat-completion).
Sending a request shares its text, recent clarification exchanges and planning
context with Z.AI. Audio is transcribed locally and is not sent to Z.AI. No
request is sent without a saved key; authentication and connection failures are
displayed without applying changes.

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run
from the repository root:

```sh
uv sync --locked
uv run meal-planner-ai
```

uv uses Python 3.12 (see `.python-version`) and creates a local `.venv` with
runtime and development dependencies, including the CPU speech runtime for
Parakeet. No voice extra is required. Commit `uv.lock` to keep installs reproducible.
Launching the UI requires a graphical desktop and Qt platform libraries.
On Linux, missing system libraries must be installed using your distribution's
package manager.

You can also launch the application with `uv run python -m meal_planner_ai`.

## Local dictation and AI planning

Model weights are **not bundled or downloaded automatically**. Reuse models you
already have by configuring the paths below. If the speech model is missing or
incomplete, clicking **Dictate my request** opens **Settings**, where you can
download Parakeet explicitly. Typed requests remain available. Parakeet performs speech recognition. Both typed and transcribed text go through
the same coordinator when you click **Send request**.

### Parakeet TDT 0.6B v3

The CPU speech runtime (`onnx-asr[cpu]`, NumPy and ONNX Runtime) is installed by
the standard `uv sync --locked` command. If an existing environment reports
missing dictation dependencies, close the app, run that command from the project
root, then relaunch with `uv run meal-planner-ai`. This installs packages, not
model weights.

In **Settings**, click **Download Parakeet** to install the model from Hugging
Face (about 2.6 GB; Internet access and sufficient disk space are required).
The download runs in the background, displays its status, and can be retried
if it fails. Files are staged before installation, including external ONNX
weights. Closing the app waits for an active download to finish.

You can also use the [onnx-asr compatible Parakeet v3 export](https://huggingface.co/istupakov/parakeet-tdt-0.6b-v3-onnx)
from a local directory. An original NeMo `.nemo` checkpoint cannot be loaded by
this ONNX runtime. The directory must contain the unquantized `config.json`,
`vocab.txt`, `encoder-model.onnx`, and `decoder_joint-model.onnx`, together with
any external weight files referenced by the ONNX graphs (including
`encoder-model.onnx.data` when supplied by the export). Keep the export's
configuration unchanged. See [onnx-asr local model usage](https://istupakov.github.io/onnx-asr/usage/).

By default the app looks in `models/parakeet-tdt-0.6b-v3` relative to its working
directory. Alternatively, point it to your existing export:

```sh
MEAL_PLANNER_PARAKEET_DIR=/absolute/path/to/parakeet-v3 uv run meal-planner-ai
```

Click **Dictate my request**, speak, then **Stop and transcribe**. The app captures
16 kHz, signed 16-bit mono microphone audio and stops automatically after 20 seconds.
Repeat to append another segment. Microphone access must be allowed by the OS and
the device must support that format. Cancel or leave the home page to discard an
unfinished recording. Audio stays in memory and is transcribed locally on CPU;
no recording files are saved. Loading and transcription run in the background.
The first transcription loads the model; later ones reuse it for the session.
Closing during inference waits for the active job to finish.

### Coordinator workflow

The first agent interprets French or English requests using GLM. A LangGraph
workflow then validates a Pydantic discriminated union and routes each action
through the meal-request, grocery-addition or pantry-update node. Routing,
quantity validation, date resolution and storage are deterministic. Unknown
services, extra fields, invalid dates, non-finite or negative quantities, and
fractional piece counts are rejected. The model is instructed to ask questions
instead of inventing missing data. Recent clarification exchanges stay in memory
so you can answer a follow-up in the same input.

Examples:

- **“I want to make tiramisu for six people.”** Records a meal wish with six
  servings, visible in Planning. It does not invent a recipe or its ingredients;
  recipe generation is reserved for the future meal planning agent.
- **“Add three potatoes to buy next week.”** Adds three pieces to Groceries,
  dated for the next Monday–Sunday week. Explicit purchases do not consume pantry
  stock. Purchases containing an explicitly excluded food are rejected.
- **“I have 500 g of rice.”** Updates the available pantry quantity to 500 g.
  Pantry updates are absolute quantities and remain in memory for the session.

One request can contain multiple actions. Without a specified period, meals and
purchases use the configured planning period; “next week” is resolved from the
local current date. Without a serving count, the model uses household size.
Review the extracted quantities and dates before clicking **Apply request**.
Only those actions are applied, without replacing the existing meal plan or
household settings. If context changes during review, send the request again.

Meal wishes and explicit purchases are saved to `data/coordinator.json` beside
`config.toml`, with validated loading and atomic replacement. They can be removed
from their respective pages. A failed save applies none of the staged actions;
a corrupt file is reported and preserved. Pantry quantities and grocery
checkmarks are session-only. The key is not included in this data file.

The earlier local Ollama recipe-planning workflow remains available in code but
is not called by the desktop coordinator. Sample recipes and inventory exist
only in test fixtures. The other four agents and recipe generation remain
unimplemented.

## Layout

```text
src/meal_planner_ai/
  agents/       # Meal, grocery, verification, and preference reasoning
  workflow/     # Deterministic coordinator and LangGraph orchestration
  models/       # Pydantic data models
  storage/      # TOML configuration, credentials and coordinator JSON records
  ui/           # Session data, dictation, AI bridge, translations, and QML
data/           # Local runtime JSON files (ignored by Git)
tests/          # Automated checks
```

Keep validation, storage, and state management deterministic. Use LLM reasoning
only where it benefits interpretation and planning. The coordinator is the first
implemented agent.

## Development checks

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

The desktop checks load QML using Qt's offscreen platform so they can run
without a graphical session. Session-state checks cover quantity updates and
editing flows, recipe translations, language configuration persistence, the AI
proposal review flow, and local-only speech loading.
Speech-runtime checks run with the standard test suite. Tests use fake
model inference and do not download weights or require microphone hardware or a
live GLM or Ollama server.
