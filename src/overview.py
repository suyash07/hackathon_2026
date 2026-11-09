"""Overview tab: live conference stats from Elasticsearch counts and aggregations."""

from __future__ import annotations

from datetime import datetime, timedelta

from elasticsearch import Elasticsearch

import config
from search import TALK_FIELDS

UP_NEXT_MINUTES = 60
MAX_LIST = 20
MAX_BUCKETS = 50


def current_time() -> datetime:
    """'Now' in venue time: DEMO_NOW if set, otherwise the real clock."""
    if config.DEMO_NOW:
        return datetime.fromisoformat(config.DEMO_NOW).astimezone(config.VENUE_TZ)
    return datetime.now(config.VENUE_TZ)


def key_numbers(es: Elasticsearch) -> dict:
    """Totals for the metric tiles."""
    tracks = es.search(
        index=config.TALKS_INDEX,
        size=0,
        aggs={"tracks": {"cardinality": {"field": "track"}}},
    )
    return {
        "talks": es.count(index=config.TALKS_INDEX)["count"],
        "speakers": es.count(index=config.SPEAKERS_INDEX)["count"],
        "tracks": tracks["aggregations"]["tracks"]["value"],
        "in_building": es.count(index=config.ATTENDEES_INDEX, query={"term": {"checked_in": True}})[
            "count"
        ],
    }


def count_by(es: Elasticsearch, field: str, by_key: bool = False) -> dict[str, int]:
    """Talks per value of a keyword field (terms aggregation), biggest first or by key."""
    order = {"_key": "asc"} if by_key else {"_count": "desc"}
    res = es.search(
        index=config.TALKS_INDEX,
        size=0,
        aggs={"by": {"terms": {"field": field, "size": MAX_BUCKETS, "order": order}}},
    )
    return {b["key"]: b["doc_count"] for b in res["aggregations"]["by"]["buckets"]}


def talks_between(es: Elasticsearch, query: dict) -> list[dict]:
    """Talks matching a time query, earliest first."""
    res = es.search(
        index=config.TALKS_INDEX,
        query=query,
        sort=[{"start": "asc"}],
        source_includes=TALK_FIELDS,
        size=MAX_LIST,
    )
    return [hit["_source"] for hit in res["hits"]["hits"]]


def happening_now(es: Elasticsearch, now: datetime) -> list[dict]:
    """Talks that have started and not ended yet."""
    t = now.isoformat()
    return talks_between(
        es, {"bool": {"filter": [{"range": {"start": {"lte": t}}}, {"range": {"end": {"gt": t}}}]}}
    )


def up_next(es: Elasticsearch, now: datetime, minutes: int = UP_NEXT_MINUTES) -> list[dict]:
    """Talks starting within the next `minutes`."""
    later = (now + timedelta(minutes=minutes)).isoformat()
    return talks_between(es, {"range": {"start": {"gt": now.isoformat(), "lte": later}}})


def side_events_on(es: Elasticsearch, day: datetime) -> list[dict]:
    """Side events on the same venue day as `day`, earliest first."""
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    res = es.search(
        index=config.SIDE_EVENTS_INDEX,
        query={
            "range": {
                "start": {"gte": start.isoformat(), "lt": (start + timedelta(days=1)).isoformat()}
            }
        },
        sort=[{"start": "asc"}],
        size=MAX_LIST,
    )
    return [hit["_source"] for hit in res["hits"]["hits"]]
