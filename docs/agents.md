# Agent implementation guide

The desktop request entry point is `PlanningAssistant.plan()` in
`src/meal_planner_ai/ui/assistant.py`. It runs the graph in a Qt worker and applies
a successful result on the UI thread. Typed and transcribed text use the same path.

## Source map

All paths below are relative to `src/meal_planner_ai/`.

| Component | Implementation | Responsibility |
| --- | --- | --- |
| Coordinator | `agents/coordinator/agent.py` | Interpret the request with GLM; emit commands or a clarification |
| Meal Planning Agent | `agents/meal_planning/agent.py` | Generate a validated recipe for each requested dish |
| Food Preferences Agent | `agents/food_preferences/agent.py` | Reject incompatible vegetarian recipes and excluded foods |
| Grocery List Agent | `agents/grocery_list/agent.py` | Aggregate requirements, subtract available stock and round piece purchases |
| GLM transport | `providers/glm.py` | HTTP authentication, JSON completions, timeouts and safe provider errors |
| Desktop graph | `workflow/meal_request.py` | Run agents in sequence and assemble the complete result |
| Coordinator routing | `workflow/coordinator.py` | Validate commands, resolve periods and stage service actions |
| Food vocabulary | `domain/foods.py` | Stable food identities and French/English matching |
| UI services | `ui/demo.py` | Revalidate results, save atomically and expose meals and groceries to QML |
| Persistence | `storage/coordinator.py` | Validate and load/save `data/coordinator.json` |

Each agent package exports its public functions from `__init__.py`; its behavior
lives in `agent.py`. No agent mutates the desktop session or writes JSON files.
The separate Grocery Verification Agent remains planned.

## Libraries and contracts

- **LangGraph** (`langgraph.graph.StateGraph`): graph nodes, conditional routing and
  state transitions. The desktop graph runs the coordinator subgraph, then meal
  planning, preferences and groceries. Clarifications bypass generation and saving.
- **Pydantic**: rejects extra fields, invalid quantities, missing recipe content,
  incomplete batches and mismatched dishes/servings. `models/coordinator.py`
  defines commands and persisted records; `models/recipes.py` defines `Ingredient`,
  `Recipe` and `RecipeBatch`; `models/groceries.py` defines `GroceryRequirement`;
  `models/execution.py` defines the complete `MealExecution` output.
- **Python standard library** (`urllib.request`, `json`): the shared GLM client.
  Both GLM calls use JSON output and the model schema in the prompt. The existing
  configured model is `glm-5.3-flash`; no additional SDK or provider is needed.
- **PySide6**: `QRunnable`/`QThreadPool` execute the graph. Queued Qt signals relay
  real stage changes to QML. The interface uses a spinner and elapsed time while
  waiting for GLM, then shows saving and completion or an actionable error.

Versions and development dependencies are in `pyproject.toml` and `uv.lock`.
Provider references: [Z.AI Chat Completion](https://docs.z.ai/api-reference/llm/chat-completion),
[LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api).

## Quantities, preferences and saving

Recipe ingredient quantities cover all `Recipe.servings`. Generated meals keep
the coordinator's title, period and serving count. Extra guests scale those
quantities. Pantry stock is shared once across all recipes; explicit purchases
remain independent. The Grocery List Agent is reused by the desktop whenever
recipes, stock or guests change, avoiding a separate UI calculation algorithm.

Only interpretation and recipe generation use GLM. Preferences, period resolution,
quantity arithmetic, validation and persistence are deterministic. Preference
checks reject the recipe flag or common animal ingredients for vegetarian mode,
and match household exclusions in ingredient names, known English aliases and
recipe text. Unknown food names remain unchanged; the vocabulary can be extended
in `domain/foods.py`.

Before saving, the UI checks that planning data still matches the snapshot,
revalidates the execution and recomputes its groceries. It stages all commands
and recipes, saves one validated JSON document with an atomic replacement, then
updates session state. Failed generation or saving applies none of the batch.
Optional recipe and guest fields preserve compatibility with earlier version 1
meal records. Recipe shortfalls are derived from saved recipes and current stock.

## Offline checks

`tests/test_meal_workflow.py` covers the connected graph, the tiramisu example,
calendar weeks, compound requests, shared pantry stock, preference rejection,
invalid recipes, live progress, automatic saving, restoring recipes, guests and
failed persistence. Existing coordinator, dictation and QML checks remain in
`tests/`. Tests mock GLM HTTP or recipe reasoning; they do not use real credentials,
download models or require microphone hardware.

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```
