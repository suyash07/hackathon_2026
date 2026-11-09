"""One place to call the LLM through Elasticsearch's inference API."""

from __future__ import annotations

from elasticsearch import ApiError, Elasticsearch, TransportError

import config

LLM_TIMEOUT_SECONDS = 60  # the client's default is 10s; LLM answers can take longer


def complete(es: Elasticsearch, prompt: str) -> str:
    """Return the LLM's text for `prompt`. Raises RuntimeError with a readable message."""
    try:
        res = es.options(request_timeout=LLM_TIMEOUT_SECONDS).inference.completion(
            inference_id=config.LLM_INFERENCE_ID,
            input=prompt,
            timeout=f"{LLM_TIMEOUT_SECONDS}s",
        )
    except (ApiError, TransportError) as err:
        raise RuntimeError(
            f"LLM call failed ({config.LLM_INFERENCE_ID}). Is this endpoint available on your "
            f"Elasticsearch deployment? Details: {err}"
        ) from err
    return res["completion"][0]["result"]
