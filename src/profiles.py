"""Attendee profiles: the single source of personalization for every feature."""

from __future__ import annotations

from elasticsearch import Elasticsearch, NotFoundError

import config

DEMO_USER_ID = "demo-user"


def get_profile(es: Elasticsearch, attendee_id: str) -> dict:
    """Return one attendee's profile. Raises ValueError if the id doesn't exist."""
    try:
        return es.get(index=config.ATTENDEES_INDEX, id=attendee_id)["_source"]
    except NotFoundError as err:
        raise ValueError(f"No attendee with id '{attendee_id}'") from err
