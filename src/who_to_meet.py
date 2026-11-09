"""Feature 4: who to meet at this talk.

For a talk, find attendees whose interests match it and who are attending that day.

Run from the project root:  python src/who_to_meet.py t049
"""

from __future__ import annotations

import sys

from elasticsearch import Elasticsearch

import config
from es_client import get_client
from profiles import DEMO_USER_ID
from queries import build_semantic_query

PEOPLE_PER_TALK = 3
PERSON_FIELDS = ["id", "name", "role", "company", "working_on"]


def get_talk(es: Elasticsearch, talk_id: str) -> dict:
    """Return the fields needed to match people to a talk."""
    return es.get(
        index=config.TALKS_INDEX, id=talk_id, source_includes=["title", "abstract", "day"]
    )["_source"]


def who_to_meet(
    es: Elasticsearch,
    talk_id: str,
    exclude_ids: list[str] | None = None,
    size: int = PEOPLE_PER_TALK,
) -> list[dict]:
    """Attendees whose interests match the talk and who are there that day, best first."""
    talk = get_talk(es, talk_id)
    res = es.search(
        index=config.ATTENDEES_INDEX,
        query=build_semantic_query(
            "interests",
            f"{talk['title']}. {talk['abstract']}",
            exclude_ids=exclude_ids,
            filters=[{"term": {"available_days": talk["day"]}}],
        ),
        source_includes=PERSON_FIELDS,
        size=size,
    )
    return [{**hit["_source"], "score": hit["_score"]} for hit in res["hits"]["hits"]]


if __name__ == "__main__":
    talk_id = sys.argv[1] if len(sys.argv) > 1 else "t049"
    es = get_client()
    talk = get_talk(es, talk_id)
    print(f"{talk['title']} ({talk['day']})\n\nWho to meet there:\n")
    for p in who_to_meet(es, talk_id, exclude_ids=[DEMO_USER_ID]):
        print(f"{p['score']:6.2f}  {p['name']} ({p['role']}, {p['company']})")
        print(f"        {p['working_on']}")
