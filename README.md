# Conference Search (Cloud Native Hackathon – Elasticsearch track)

> Project description goes here.

## Features
- [ ] Talk search by meaning
- [ ] Hallway matchmaker
- [ ] Conference assistant (RAG)

## Setup
1. Start Elasticsearch + Kibana locally (needs Docker):
   `curl -fsSL https://elastic.co/start-local | sh`
2. Create a virtual environment:
   ```bash
   python3 -m venv hackathon
   source hackathon/bin/activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your values.
4. Check everything connects: `python src/check_setup.py`

## Architecture

![Architecture](docs/architecture.png)

<details><summary>Mermaid source</summary>

```mermaid
flowchart LR
    U([Attendee]) --> UI

    subgraph APP["Streamlit app (app.py) — UI only"]
        UI["Tabs: Search · Matchmaker · Assistant · Agenda · Who to meet<br/>+ profile picker"]
    end

    subgraph LOGIC["Feature logic (src/)"]
        S["search.py<br/>talk search + 'you might like'"]
        M["matchmaker.py<br/>similar attendees"]
        A["assistant.py<br/>RAG"]
        AG["agenda.py"]
        W["who_to_meet.py"]
    end

    subgraph ES["Elasticsearch (Docker, localhost:9200)"]
        IDX[("talks · attendees<br/>speakers · side_events")]
        ELSER["ELSER embedding model<br/>(built in, no key)"]
    end

    LLM["Claude API<br/>(Anthropic key)"]

    subgraph DATA["Data pipeline (run once)"]
        G["generate_data.py<br/>synthetic JSON"] --> I["indexing.py<br/>validate + bulk load"]
    end

    UI --> S & M & A & AG & W
    AG --> S
    W --> S
    A -- "1. retrieve top talks" --> S
    S & M --> IDX
    IDX <--> ELSER
    I --> IDX
    A -- "2. talks + question" --> LLM
    LLM -- "3. cited answer" --> A
    CFG["config.py + .env"] -.-> LOGIC
```
</details>

**Layers**
| Layer | Files | Responsibility |
|---|---|---|
| UI | `app.py` | Streamlit tabs + profile picker. Displays results only — no queries or prompts. |
| Feature logic | `src/search.py`, `matchmaker.py`, `assistant.py`, `agenda.py`, `who_to_meet.py` | One module per feature. All talk retrieval goes through `search.py` (DRY). |
| Data access | `src/es_client.py`, `src/config.py` | One Elasticsearch client; all settings from `.env`. |
| Storage + vectors | Elasticsearch (Docker) | Indices: `talks`, `attendees`, `speakers`, `side_events`. `semantic_text` fields are embedded by the built-in ELSER model — no external embedding API. |
| Generation | Claude API | Used only by the assistant (RAG) to write answers from retrieved talks. |
| Data pipeline | `src/generate_data.py` → `src/indexing.py` | Generate synthetic JSON, validate, bulk-load. Run once; re-run to reset the demo. |

**Request flows**
- **Talk search:** query → `semantic` query on `talks.content` → ranked talks (+ "you might like" using the profile's `interests`).
- **Matchmaker:** profile's `working_on` → `semantic` query on `attendees.working_on` (excluding self) → closest people.
- **Assistant (RAG):** question → retrieve top talks via `search.py` → talks + question (+ profile) sent to Claude → answer citing talk titles.
- **Agenda / who to meet:** reuse `search.py` + filters (time slots, attendees) — no new retrieval logic.

## Data
_Describe data sources here._

## AI use disclosure
This project was built with help from Claude (Anthropic) as a coding assistant.
