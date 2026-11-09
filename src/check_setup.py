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


def anthropic_key():
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is empty in .env")
    import anthropic

    r = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY).messages.create(
        model=config.LLM_MODEL,
        max_tokens=10,
        messages=[{"role": "user", "content": "Say ok"}],
    )
    return f"{config.LLM_MODEL} replied '{r.content[0].text.strip()}'"


def streamlit():
    import streamlit as st

    return "version " + st.__version__


check("Elasticsearch", elasticsearch)
check("Embedding endpoints", embedding_model)
check("Anthropic API", anthropic_key)
check("Streamlit", streamlit)
