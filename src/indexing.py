"""Validate data/*.json and load it into Elasticsearch.

Recreates every index, so re-running resets the demo.
Run from the project root:  python src/indexing.py
"""

from __future__ import annotations

import json
import logging

from elasticsearch import Elasticsearch, helpers

import config
from es_client import get_client

logger = logging.getLogger(__name__)

# First load starts the ELSER model, which can take a few minutes.
BULK_TIMEOUT_SECONDS = 900
BULK_CHUNK_SIZE = 50

KEYWORD = {"type": "keyword"}
TEXT = {"type": "text"}
SEMANTIC = {"type": "semantic_text"}  # embedded by the built-in ELSER model
DATE = {"type": "date"}

MAPPINGS = {
    config.TALKS_INDEX: {
        "id": KEYWORD,
        "title": TEXT,
        "abstract": TEXT,
        "content": SEMANTIC,  # title + abstract, built in prepare_talk()
        "speakers": KEYWORD,
        "speaker_ids": KEYWORD,
        "track": KEYWORD,
        "tags": KEYWORD,
        "format": KEYWORD,
        "level": KEYWORD,
        "room": KEYWORD,
        "start": DATE,
        "end": DATE,
        "day": KEYWORD,
    },
    config.SPEAKERS_INDEX: {
        "id": KEYWORD,
        "name": KEYWORD,
        "company": KEYWORD,
        "bio": SEMANTIC,
    },
    config.ATTENDEES_INDEX: {
        "id": KEYWORD,
        "name": KEYWORD,
        "role": KEYWORD,
        "company": KEYWORD,
        "experience_level": KEYWORD,
        "working_on": SEMANTIC,
        "interests": SEMANTIC,
        "goals": KEYWORD,
        "available_days": KEYWORD,
        "checked_in": {"type": "boolean"},
        "current_location": KEYWORD,
        "bookmarked_talks": KEYWORD,
    },
    config.SIDE_EVENTS_INDEX: {
        "id": KEYWORD,
        "name": TEXT,
        "description": SEMANTIC,
        "start": DATE,
        "location": KEYWORD,
    },
}

REQUIRED = {
    config.TALKS_INDEX: ["id", "title", "abstract", "track", "room", "start", "end", "day"],
    config.SPEAKERS_INDEX: ["id", "name", "bio"],
    config.ATTENDEES_INDEX: ["id", "name", "role", "working_on", "interests"],
    config.SIDE_EVENTS_INDEX: ["id", "name", "description", "start", "location"],
}


def load_json(index: str) -> list[dict]:
    """Read data/<index>.json."""
    path = config.DATA_DIR / f"{index}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run: python src/generate_data.py")
    return json.loads(path.read_text())


def validate(index: str, docs: list[dict]) -> None:
    """Fail with a clear message if required fields are missing, ids repeat, or times are wrong."""
    ids = [d.get("id") for d in docs]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{index}: duplicate ids")
    for doc in docs:
        missing = [f for f in REQUIRED[index] if not doc.get(f)]
        if missing:
            raise ValueError(f"{index} {doc.get('id')}: missing {missing}")
        if index == config.TALKS_INDEX and doc["end"] <= doc["start"]:
            raise ValueError(f"talk {doc['id']}: end is not after start")


def prepare_talk(talk: dict) -> dict:
    """Add the combined field that semantic search runs on."""
    return {**talk, "content": f"{talk['title']}. {talk['abstract']}"}


def recreate_index(es: Elasticsearch, index: str) -> None:
    """Delete the index if it exists, then create it with explicit mappings."""
    es.options(ignore_status=404).indices.delete(index=index)
    es.indices.create(index=index, mappings={"properties": MAPPINGS[index]})


def bulk_load(es: Elasticsearch, index: str, docs: list[dict]) -> int:
    """Index docs and return how many loaded. Raises if any document failed."""
    actions = ({"_index": index, "_id": d["id"], "_source": d} for d in docs)
    ok, errors = helpers.bulk(
        es.options(request_timeout=BULK_TIMEOUT_SECONDS),
        actions,
        chunk_size=BULK_CHUNK_SIZE,
        raise_on_error=False,
    )
    if isinstance(errors, list) and errors:
        raise RuntimeError(f"{index}: {len(errors)} docs failed, first error: {errors[0]}")
    return ok


def index_all(es: Elasticsearch) -> None:
    """Validate and load every index."""
    for index in MAPPINGS:
        docs = load_json(index)
        validate(index, docs)
        if index == config.TALKS_INDEX:
            docs = [prepare_talk(t) for t in docs]
        recreate_index(es, index)
        count = bulk_load(es, index, docs)
        logger.info("%s: loaded %d docs", index, count)
    es.indices.refresh(index=",".join(MAPPINGS))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("elastic_transport").setLevel(logging.WARNING)
    index_all(get_client())
    print("Done.")
