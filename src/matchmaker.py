"""Feature 2: hallway matchmaker — people in the building working on similar things.

Run from the project root:  python src/matchmaker.py [attendee_id]
"""

from __future__ import annotations

import sys

from elasticsearch import Elasticsearch

import config
from es_client import get_client
from profiles import DEMO_USER_ID, get_profile
from queries import build_semantic_query

DEFAULT_MATCHES = 5
MATCH_FIELDS = ["id", "name", "role", "company", "working_on", "current_location", "goals"]
IN_BUILDING = {"term": {"checked_in": True}}


def find_matches(
    es: Elasticsearch,
    profile: dict,
    size: int = DEFAULT_MATCHES,
    in_building_only: bool = True,
) -> list[dict]:
    """Return attendees whose work is closest to `profile`'s, best first, excluding themself."""
    res = es.search(
        index=config.ATTENDEES_INDEX,
        query=build_semantic_query(
            "working_on",
            profile["working_on"],
            exclude_ids=[profile["id"]],
            filters=[IN_BUILDING] if in_building_only else None,
        ),
        source_includes=MATCH_FIELDS,
        size=size,
    )
    return [{**hit["_source"], "score": hit["_score"]} for hit in res["hits"]["hits"]]


if __name__ == "__main__":
    attendee_id = sys.argv[1] if len(sys.argv) > 1 else DEMO_USER_ID
    es = get_client()
    me = get_profile(es, attendee_id)
    print(f"{me['name']} is working on: {me['working_on']}\n")
    print("Closest matches in the building:\n")
    for m in find_matches(es, me):
        who = f"{m['name']} ({m['role']}, {m['company']})"
        print(f"{m['score']:6.2f}  {who} — {m['current_location']}")
        print(f"        {m['working_on']}")
