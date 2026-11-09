# CLAUDE.md — Conference Search (Cloud Native Hackathon, Elasticsearch track)

Instructions for the coding agent working in this repo. Follow them on every task.

## Project
A conference companion for KubeCon + CloudNativeCon NA 2026 (Salt Lake City), built on Elasticsearch:
1. **Talk search** — semantic search over talk titles + abstracts ("stopping attackers breaking out of containers" finds the right session even without those words).
   - Add-on: below the results, a **"Based on your profile, you might like…"** section with 3 talks matching the selected profile's `interests`. Reuse the same search function with `interests` as the query (no new search logic); exclude talks already in the main results. Hidden when no profile is selected.
   - This is talk recommendation, not the matchmaker (which recommends people). If time runs short, ship this and skip the agenda builder.
2. **Hallway matchmaker** — attendees' "working on" text stored as vectors; find the closest people.
3. **Conference assistant** — RAG: retrieve relevant talks from Elasticsearch, have Claude answer schedule questions with citations.
4. **Personal agenda builder** — from a user's profile/interests, build a conflict-free schedule (semantic search + date filters, no overlapping time slots).
5. **"Who to meet at this talk"** — for each talk, list attendees whose `working_on`/`interests` match it (reuses features 1 + 2).
6. **Streamlit UI** — one app, one tab per feature, with a "logged in as" attendee picker that drives personalization.

Build order: 1 → 2 → 3 → UI → 4 → 5. Stretch only if time remains: image upload (photo of a slide → Claude vision describes it → find related talks/attendees).

## Attendee profile (shared by every feature)
One profile per attendee in the `attendees` index — the single source of personalization. Do not create separate per-feature user stores.

| Field | ES type | Used by |
|---|---|---|
| `id` | keyword | all |
| `name`, `role`, `company` | keyword | display, filters |
| `experience_level` (`beginner` / `intermediate` / `expert`) | keyword | agenda builder, assistant |
| `working_on` | semantic_text | matchmaker, who-to-meet |
| `interests` (1–2 sentences) | semantic_text | search boosting, agenda builder, who-to-meet |
| `goals` (list, e.g. `hiring`, `learn kubernetes`, `find contributors`) | keyword | assistant context, matchmaker |
| `available_days` | keyword | agenda builder |
| `checked_in` | boolean | matchmaker ("in the building" = only checked-in people) |
| `current_location` (room / area, null if not checked in) | keyword | matchmaker ("find them in Room 4") |
| `bookmarked_talks` (talk ids) | keyword | agenda builder seed, "you might like" signal |

- The selected profile is passed into features as a parameter (dependency injection), never read from a global.
- Profile is **optional** for talk search and the assistant (`profile=None` default — they work without login, personalize when given); **required** for the matchmaker, agenda builder and who-to-meet.
- The RAG assistant receives the profile as context so "what should I attend?" is personalized.

## Data rules
- **Talks/speakers:** synthetic, KubeCon-style (~150–300 talks over Nov 9–12, Salt Lake City). Use realistic cloud-native tracks: AI Inference + Agentic, Platform Engineering, Security, Observability, Networking (Cilium, service mesh), plus co-located-event style sessions (CiliumCon, ArgoCon, BackstageCon). Fictional speakers and companies. Do not scrape the real schedule.
- **Talk schema:** `id, title, abstract, speakers (list of names), speaker_ids (list), track, tags (list), format (talk/workshop/panel/lightning), level, room, start, end, day`. Times in ISO 8601 with Salt Lake City offset (`-07:00`).
- **Speaker schema:** `id, name, company, bio`. **Side event schema:** `id, name, description, start, location`.
- **Attendees, side events:** also synthetic (fictional names/companies) — public repo, no real personal data. README → Data states that all data is synthetic.
- Generate with a script `src/generate_data.py` using a fixed random seed so data is reproducible; write to `data/*.json`. Never hand-edit generated files.
- Make synthetic data realistic enough to demo every feature:
  - ~100–150 attendees spanning roles (SRE, platform, security, ML, data, student, PM) and all experience levels.
  - Interests that overlap across people (so matchmaker returns meaningful clusters) and some that **cross** topics (security + AI) to show semantic matching.
  - Overlapping talk time slots in the same interest area, so the agenda builder must resolve conflicts.
  - A few deliberately vague/off-keyword phrasings (e.g. "kernel-level visibility") to prove semantic search beats keyword search.
  - A named demo user (e.g. `demo-user`) whose profile produces a clear, explainable result in every feature.
- Validate data before indexing (required fields present, `end > start`, no duplicate ids) and fail with a clear message.
- Indexing script recreates indices from `data/` so the demo can be reset in one command.

## Hackathon rules the agent must respect
- Never use the term "eBPF" anywhere in the app, data, examples or docs; say "kernel-level" / "kernel tracing" instead.
- Main code is written during the hackathon. Do not paste in pre-written feature code; write it fresh with the user.
- The user must be able to explain every line and every architecture decision. After each change, give a 1–3 line "why" for the key decision.
- AI assistance is allowed but must be disclosed — keep the "AI use disclosure" section in README.md.
- Public repo: never commit secrets, private data, or real personal attendee data. Attendee data is synthetic.
- Only use data we have permission to use; record each source in README → Data.

## How to work with the user
- Keep answers short. Step-by-step, one step at a time, each with a one-line "why".
- Give exact terminal commands (macOS, zsh, venv named `hackathon`).
- Ask before large refactors, new dependencies, or deleting files.
- Build in small working increments: make it run, verify, commit, then improve.

## Stack and environment
- Python 3.9 (macOS system Python) in venv `hackathon/`. Code must run on 3.9:
  use `from __future__ import annotations` for `X | None` style hints; no `match` statements.
- Elasticsearch 9.x + Kibana local via start-local (Docker) at `localhost:9200` / `localhost:5601`.
- Embeddings: `semantic_text` fields using the built-in `.elser-2-elasticsearch` endpoint (default). Reranker available: `.rerank-v1-elasticsearch`.
- LLM: Anthropic Claude via the `anthropic` SDK; model from `LLM_MODEL` in `.env`.
- UI: Streamlit.
- Ignore the harmless `NotOpenSSLWarning` from urllib3.

## Repo layout
```
.env / .env.example      secrets (never commit .env)
requirements.txt
README.md
CLAUDE.md
data/                    JSON inputs (talks, speakers, attendees, side_events)
src/
  config.py              ALL settings from .env — the only place that reads env vars
  check_setup.py         connection health check
  es_client.py           single Elasticsearch client factory
  generate_data.py       synthetic attendees / side events (fixed seed)
  indexing.py            validate data, index mappings + bulk load
  agenda.py              feature 4 (agenda builder)
  who_to_meet.py         feature 5
  search.py              feature 1
  matchmaker.py          feature 2
  assistant.py           feature 3 (RAG)
app.py                   Streamlit UI — imports from src/, no ES/LLM logic inline
tests/                   pytest tests
```

## Software engineering principles (apply to every change)
- **DRY (Don't Repeat Yourself):** one function per job, reused everywhere. E.g. talk retrieval lives in `search.py` and the RAG assistant calls it; no copy-pasted queries.
- **Reusability:** write generic helpers (e.g. `semantic_search(index, field, query, size)`) that features 1, 2 and 3 all use. No feature-specific copies.
- **Single Responsibility (SOLID "S"):** each module and function does one thing — config reads settings, `es_client` connects, `indexing` loads, features query, `app.py` only renders.
- **Separation of concerns:** UI ↔ business logic ↔ data access stay in separate layers. Streamlit never builds ES queries or LLM prompts itself.
- **Dependency injection:** pass clients in as parameters (`def search_talks(es, query)`) instead of importing globals, so code is testable and swappable.
- **Open/Closed:** add new features (e.g. side-event search) by adding a function/config entry, not by editing working ones.
- **KISS:** simplest solution that works. No frameworks or abstractions we don't need.
- **YAGNI:** don't build features "for later". Hackathon scope only.
- **Readability over cleverness:** descriptive names (`find_similar_attendees`, not `fsa`), no magic numbers — use named constants (`DEFAULT_TOP_K = 5`).
- **Modularity:** small modules with clear public functions; another developer should understand a file in under a minute.
- **Fail fast & explicitly:** validate inputs and config at startup; raise clear errors instead of returning `None` silently.
- **Security by default:** secrets only in `.env`, never logged or printed; no user input concatenated into queries — always pass it as a query parameter.
- **Consistency:** same naming, error-handling and return shapes across all features (e.g. every search returns `list[dict]` with a `score`).

## Coding standards
- **Style:** PEP 8, formatted and linted with `ruff` (`ruff format . && ruff check .`). Line length 100.
- **Types & docs:** type hints on all public functions; short docstrings stating purpose, args, returns.
- **Small, pure functions:** separate "build query" from "run query" so queries are unit-testable without Elasticsearch.
- **Config:** never hard-code URLs, keys, index names or model names — import from `config.py`. Index names live in config as constants.
- **One client:** create the Elasticsearch / Anthropic clients once (`es_client.py`; in Streamlit wrap with `@st.cache_resource`).
- **Errors:** fail with clear messages (missing env var, ES down, index missing). Check `helpers.bulk` errors and report counts — never silently drop documents. No bare `except:`.
- **Logging:** use `logging` in `src/`; `print` only in CLI `__main__` blocks.
- **Idempotent setup:** indexing script can be re-run safely (recreate index, then load).
- **No dead code**, no commented-out blocks, no unused imports.

## Elasticsearch conventions
- Explicit mappings — never rely on dynamic mapping. `keyword` for filters (speaker, room, track), `date` for times, `text` for keyword search, `semantic_text` for meaning-based search.
- Talks: index a combined `content` field (title + abstract) as `semantic_text`.
- Prefer **hybrid search** (BM25 `multi_match` + `semantic`, combined with an RRF retriever) when it improves results; show a before/after example to justify it.
- Use filters (`bool.filter`) for structured constraints like day, room, track — not the LLM.
- Limit `_source` to the fields actually needed.
- Bulk loads use `request_timeout` long enough for first-time model start-up.

## RAG conventions
- Retrieve top-k (default 5) talks via the same search function as feature 1 — no duplicate retrieval logic.
- Prompt: system prompt says answer **only** from provided talks; if not found, say so. Include title, speaker, time, room in context.
- Answers cite talk titles. Keep the prompt in one constant so it is easy to review.
- Set `max_tokens`; handle API errors (auth, rate limit) with a friendly message.

## Testing & verification
- `pytest` for query builders and pure helpers (no network).
- Before saying a feature is done: run it end to end against local Elasticsearch and show the output.
- Keep `python src/check_setup.py` passing.

## Commit checklist (run every time the user says "commit" or "commit and push")
1. `git status` — review what changed; nothing unexpected staged.
2. **Secret scan:** `git diff --cached` must not contain `sk-ant`, passwords, API keys, or `.env`; `.env`, `hackathon/`, `__pycache__/` must not be staged. Stop and warn if found.
3. `ruff format . && ruff check .` — fix issues before committing.
4. `pytest -q` (if tests exist) — must pass.
5. Feature actually runs end to end (or say clearly what's untested).
6. README updated if a feature, setup step, or data source changed.
7. Commit with a Conventional Commit message (`feat:`, `fix:`, `docs:`…) describing *why*, not just what.
8. Push the **feature branch** (never commit straight to `main`), then open a pull request (`gh pr create` if available, otherwise give the user the GitHub compare link).
9. Wait for the **Gitar** review on the PR; fix its findings in new commits on the same branch; merge when clean (`gh pr merge --squash` or the GitHub button), then `git checkout main && git pull`.
10. Report the PR link and a one-line summary.

Gitar review instructions live in `.gitar/review/*.md` (hackathon rules, Python standards, Elasticsearch conventions). Keep them in sync with this file when conventions change.

## Git workflow
- One branch per feature: `feat/<name>`, `fix/<name>`, `docs/<name>`. One PR per branch, reviewed by Gitar before merging to `main`.
- Small commits after each working step, Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Never commit `.env`, `hackathon/`, `__pycache__/`, or large raw data dumps.
- Update README (setup, architecture, data sources) as features land.
