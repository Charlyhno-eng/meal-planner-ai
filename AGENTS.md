# meal-planner-ai

## Project Goal

Build a local multi-agent application that helps users plan meals and generate a grocery list based on their available food, household constraints, dietary preferences, and planning period.

The application is built with:

* **Python**
* **uv** for project and dependency management
* **LangGraph** for agent orchestration
* **Pydantic** for data models and validation
* **PySide6 + QML** for the desktop UI
* **Local JSON files** for persistent data storage

## User Inputs

The user provides:

* Food currently available at home
* Number of meals to plan
* Planning period (e.g. 7 days)
* Number of people eating
* Optional guests, including the meal(s) concerned and number of guests
* Dietary preferences and food dislikes

## Agent Architecture

### Coordinator Agent

The main entry point of the system.

Responsibilities:

* Receive and structure user inputs
* Coordinate the other agents
* Maintain the global planning state
* Persist relevant data to local JSON files

This component should remain as deterministic as possible. AI should only be used where it provides a clear benefit; simple data-processing pipelines should be preferred for storage, validation, and state management.

### Meal Planning Agent

Responsible for creating a meal plan based on:

* Available ingredients
* Number of meals
* Number of people
* Guests
* Planning period
* Dietary preferences and restrictions

### Grocery List Agent

Responsible for generating the grocery list required to prepare the planned meals.

It should distinguish between:

* Ingredients already available
* Ingredients that need to be purchased

### Grocery Verification Agent

Validates the meal plan and grocery list to ensure that all required ingredients and quantities are accounted for.

It should detect missing ingredients, inconsistencies, or insufficient quantities.

### Food Preferences Agent

Responsible for enforcing individual food preferences.

It ensures that proposed meals, recipes, and grocery items do not contain foods explicitly disliked or excluded by household members.

## Core Principle

The system should separate **data management and deterministic processing** from **LLM-based reasoning**.

Agents should have clear responsibilities, structured inputs/outputs, and validated data models. LangGraph should be used to orchestrate the workflow and state transitions between agents.

## Working rules

- Follow existing project conventions and keep changes focused on the ticket.
- Update these instructions only when lasting project guidance changes.
