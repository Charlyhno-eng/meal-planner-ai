# Application languages

Only **French (`fr`)** and **English (`en`)** are supported.

- `fr.json`: French text.
- `en.json`: English text with exactly the same stable identifiers.
- `catalogs.py`: shared loading, lookup, and template formatting.
- `system.py`: operating-system UI language detection.
- `vocabulary.json`: maps persisted canonical food/unit/category values to IDs.
  These identities remain stable when the French display text changes.

At startup, use the first supported language in the OS preference list. Regional
variants such as `fr-CA` and `en-GB` are supported. Fall back to English if none
matches. There is no persistent application-language override; restart after
changing the OS language preferences.

## Editing text

Change the value of an entry in either JSON catalog, keeping its identifier.
For new built-in text, add the same identifier to both catalogs. Application
screens use `I18n.tr("text.settings")`; Python uses `translate(key, language)`
or stores the key until display. Do not embed translated sentences in QML or
Python. Add entries to both catalogs before referencing a new identifier.

Fixed messages with dynamic content use named placeholders, for example
`{foods}` in `workflow.ask_package_size`. Preserve the same placeholder names in
both languages and pass values to `translate`. Whitespace in prefix and suffix
entries is intentional. Dates use Qt locale formatting and the catalog's date
format; unit singular/plural labels are also in the catalogs.

Errors and progress APIs that return plain strings use `source_text(key)` to
resolve the French source text. The desktop translates these messages when
rendering them, without introducing Qt or session state into agent logic.

Canonical ingredient, category and unit values used by models, storage, and
calculations are data identities. The UI adapter resolves their display labels
through the catalogs. The compatibility French-to-English lookup also supports
older recipe examples. User-provided names and generated recipe prose are not
static catalog entries: preserve that content, and instruct AI agents to write
in the selected application language. Model prompts and dietary matching rules
are reasoning/validation logic rather than interface translations.

Run `uv run pytest tests/test_language.py` to check both catalogs, referenced
identifiers, templates, OS detection, and rendering in both languages.
