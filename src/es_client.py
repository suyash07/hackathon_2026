"""Single place that creates the Elasticsearch client."""

from __future__ import annotations

from elasticsearch import Elasticsearch

import config


def get_client() -> Elasticsearch:
    """Return an Elasticsearch client built from config.

    Uses ES_API_KEY when set (Elastic Cloud), otherwise ES_USER/ES_PASSWORD (local).
    """
    if config.ES_API_KEY:
        return Elasticsearch(config.ES_URL, api_key=config.ES_API_KEY)
    if not config.ES_PASSWORD:
        raise ValueError("Set ES_API_KEY (cloud) or ES_PASSWORD (local) in .env")
    return Elasticsearch(config.ES_URL, basic_auth=(config.ES_USER, config.ES_PASSWORD))


if __name__ == "__main__":
    print(get_client().info()["version"]["number"])
