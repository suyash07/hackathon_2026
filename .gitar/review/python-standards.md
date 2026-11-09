# Python standards

- Must run on Python 3.9: `from __future__ import annotations` for `X | None` hints, no `match` statements.
- Type hints and a one-line docstring on every public function.
- DRY: talk retrieval goes through `search.search_talks`; query building goes through `queries.build_semantic_query`. Flag duplicated query or retrieval logic.
- Single responsibility: `app.py` only renders Streamlit UI. Flag Elasticsearch queries, LLM prompts or business logic inside `app.py`.
- Dependency injection: functions take the Elasticsearch client as a parameter (`es`), never a module-level global.
- No hard-coded URLs, keys, index names or model names: use `config.py`.
- No magic numbers: use named constants (`DEFAULT_TOP_K`).
- No bare `except:`. In `src/`, use `logging`, not `print` (except inside `if __name__ == "__main__":`).
- No dead code, commented-out blocks or unused imports.
