"""Feature 1: talk search by meaning, plus "You might like" recommendations.

Run from the project root:  python src/search.py "stopping attackers breaking out of containers"
"""

from __future__ import annotations

import sys

from elasticsearch import Elasticsearch

import config
from es_client import get_client
from profiles import DEMO_USER_ID, get_profile
from queries import build_semantic_query

DEFAULT_TOP_K = 5
RECOMMEND_TOP_K = 3
TALK_FIELDS = ["id", "title", "speakers", "track", "tags", "format", "room", "start", "end"]


def search_talks(
    es: Elasticsearch,
    query: str,
    size: int = DEFAULT_TOP_K,
    exclude_ids: list[str] | None = None,
    fields: list[str] | None = None,
) -> list[dict]:
    """Return the talks closest in meaning to `query`, best first, each with a `score`."""
    res = es.search(
        index=config.TALKS_INDEX,
        query=build_semantic_query("content", query, exclude_ids),
        source_includes=fields or TALK_FIELDS,
        size=size,
    )
    return [{**hit["_source"], "score": hit["_score"]} for hit in res["hits"]["hits"]]


def recommend_talks(
    es: Elasticsearch, profile: dict, exclude_ids: list[str] | None = None
) -> list[dict]:
    """'You might like': talks matching the profile's interests, minus ones already shown."""
    return search_talks(es, profile["interests"], RECOMMEND_TOP_K, exclude_ids)


def print_talks(talks: list[dict]) -> None:
    for talk in talks:
        print(f"{talk['score']:6.2f}  {talk['title']}")
        print(f"        {talk['track']} · {talk['room']} · {talk['start'][:16]}")


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "stopping attackers breaking out of containers"
    es = get_client()

    results = search_talks(es, text)
    print(f"Query: {text}\n")
    print_talks(results)

    profile = get_profile(es, DEMO_USER_ID)
    print(f"\nBased on your profile, you might like ({profile['name']}):\n")
    print_talks(recommend_talks(es, profile, exclude_ids=[t["id"] for t in results]))
