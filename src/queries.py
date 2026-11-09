"""Query builders shared by every feature. Pure functions: no network, easy to test."""

from __future__ import annotations


def build_semantic_query(
    field: str,
    text: str,
    exclude_ids: list[str] | None = None,
    filters: list[dict] | None = None,
) -> dict:
    """Match `text` by meaning on a semantic_text field.

    exclude_ids: document ids to leave out (e.g. talks already shown, the user themself).
    filters: exact conditions that must hold (e.g. checked_in is true) and don't affect score.
    """
    semantic = {"semantic": {"field": field, "query": text}}
    if not exclude_ids and not filters:
        return semantic
    query: dict = {"bool": {"must": semantic}}
    if exclude_ids:
        query["bool"]["must_not"] = {"ids": {"values": exclude_ids}}
    if filters:
        query["bool"]["filter"] = filters
    return query
