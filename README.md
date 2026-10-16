# Meal Planner AI

---

Meal Planner AI helps households plan meals and prepare grocery lists.
Add pantry items to track food already available at home.
Use Add food in My pantry on the assistant screen or in the Pantry page.
Enter a total quantity, or choose Boxes / tubs / packets and enter the package
count and weight/volume per package. The form shows and saves the calculated
total (for example, two 250 g tubs of mascarpone means 500 g), without an AI call.
Use pieces for countable foods such as eggs. If existing pantry stock is in pieces
but a recipe needs grams or millilitres, planning asks for clarification before
saving meals or purchases when that stock could cover a shortfall. Reply with
the size or total quantity; the assistant uses the original request to continue.
Set the planning period and household size for your meals.
Record guests and dietary preferences for the household.
In Household, use Edit to set the number of residents, add people, and enter each
person’s name and comma-separated intolerances or disliked foods. The shared
“Foods to avoid” list applies to everyone; add items with Enter or Add.
Add guest groups even before generating meals. Select the meal numbers each group
will attend and enter each guest’s name and foods to avoid. Repeat for different
groups during the week. Groups are saved locally; selected meal numbers refer to
positions in the meal list. Their portions are added only to those meals, and their
food exclusions apply only to those meals. Resident preferences and shared
exclusions apply to every meal. The assistant shows these scopes before planning;
each recipe shows its guests and applicable exclusions. New requests append meals
to the existing list, so select guest meal numbers accordingly.
Incompatible existing recipes must be removed or changed before saving new
exclusions for those meals.
Ask the assistant to create meals and recipes from a written request.
The recipe agent receives explicit exclusions for each meal before generation,
including common ingredient sources. It creates suitable variants of requested
dishes (for example, an egg-free tiramisu) instead of rejecting the request.
If verification finds a conflict, only the affected recipes are regenerated,
with specific feedback, up to two times. The grocery list is then recalculated.
If no compatible variant is produced, the assistant asks for an alternative dish;
no incompatible recipe or partial batch is saved. Exclusions remain in force.
Review recipes and see which ingredients are available or need buying.
A deterministic verification agent checks proposed recipes and grocery requirements
against the household foods to avoid before saving.
It checks ingredients even when pantry stock covers them, using the shared
French/English food vocabulary and common gluten and lactose ingredient sources.
These text checks do not identify undeclared allergens in product labels.
Add grocery purchases and check them off while shopping.
Removal buttons ask for confirmation before deleting pantry items, meals, grocery
purchases, or guests. Cancel to keep the item.
Household settings, recipes, and grocery purchases are stored locally.
The desktop interface automatically follows the operating system’s preferred UI
languages at startup, using the first supported language (English or French).
If neither is supported, it uses English. No language setting is needed; any old
language preference in `config.toml` is ignored. Restart the app after changing
the system language.
AI recipes and clarification messages follow the detected application language,
even when the request is written in the other language.
AI meal planning uses a GLM API key saved in Settings.

---

## See Meal Planner AI in action

![Meal Planner AI planning screen](docs/preview.png)

---

## Quickstart

### Install

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from the project directory:

```bash
uv sync --locked
```

### Run

```bash
uv run meal-planner-ai
```

The app requires Python 3.12 and a graphical desktop with Qt platform libraries.
Add your GLM API key in Settings to use AI meal planning.
