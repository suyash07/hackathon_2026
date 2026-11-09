# Elasticsearch conventions

- Explicit mappings only (see `src/indexing.py`); never rely on dynamic mapping.
- `semantic_text` for meaning-based fields, `keyword` for filters, `date` for times, `text` for keyword search.
- Exact conditions (day, room, checked_in) go in `bool.filter`, not `must`, so they don't change scores.
- Limit returned fields with `source_includes`.
- `helpers.bulk` errors must be checked and reported; documents must never be silently dropped.
- Index names come from `config.py`.
