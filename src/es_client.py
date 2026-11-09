"""Single place that creates the Elasticsearch client."""

from __future__ import annotations

from elasticsearch import Elasticsearch

import config


def get_client() -> Elasticsearch:
    """Return an Elasticsearch client built from config. Fails fast if the password is missing."""
    if not config.ES_PASSWORD:
        raise ValueError("ES_PASSWORD is empty in .env")
    return Elasticsearch(config.ES_URL, basic_auth=(config.ES_USER, config.ES_PASSWORD))


if __name__ == "__main__":
    print(get_client().info()["version"]["number"])
