"""Checks every connection works. Run from conf-search/:  python src/check_setup.py"""

import config
from es_client import get_client


def check(name, fn):
    try:
        print(f"OK    {name}: {fn()}")
    except Exception as e:
        print(f"FAIL  {name}: {e}")


def elasticsearch():
    mode = "API key" if config.ES_API_KEY else "user/password"
    return f"version {get_client().info()['version']['number']} at {config.ES_URL} ({mode})"


def embedding_model():
    ids = [e["inference_id"] for e in get_client().inference.get()["endpoints"]]
    return ", ".join(ids)


def llm():
    res = get_client().inference.completion(
        inference_id=config.LLM_INFERENCE_ID, input="Reply with just: ok"
    )
    return f"{config.LLM_INFERENCE_ID} replied '{res['completion'][0]['result'].strip()}'"


def streamlit():
    import streamlit as st

    return "version " + st.__version__


check("Elasticsearch", elasticsearch)
check("Embedding endpoints", embedding_model)
check("LLM via Elasticsearch", llm)
check("Streamlit", streamlit)
