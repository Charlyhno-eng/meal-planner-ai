"""Shared output-language policy for model-generated user-facing text."""


def output_language(context: dict) -> str:
    language = {"en": "English", "fr": "French"}[context.get("language", "fr")]
    return (
        f"The application language is {language}. Write ALL user-facing text in "
        f"{language}, regardless of the language of the request, dish names, "
        "conversation history or examples. This includes every recipe title, "
        "subtitle, every instruction in every recipe, and clarification messages. "
        "Translate descriptive dish titles while preserving the dish identity; "
        "traditional dish names such as Tiramisu may remain unchanged. "
        "Only structured ingredient identities, units, categories and schema keys "
        "keep their required canonical values; this exception never applies to "
        "recipe prose. Before returning JSON, review EACH recipe and clarification "
        f"and rewrite any text that is not in {language}. "
    )
