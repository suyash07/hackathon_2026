"""Feature 3: conference assistant (RAG).

1. Retrieve the most relevant talks with search_talks().
2. Send the question + those talks to an LLM hosted in Elastic Cloud.
3. Return the answer and the talks it was based on (for citations).

Run from the project root:  python src/assistant.py "When can I learn about securing containers?"
"""

from __future__ import annotations

import sys

from elasticsearch import Elasticsearch

from es_client import get_client
from llm import complete
from profiles import DEMO_USER_ID, get_profile
from search import TALK_FIELDS, search_talks

RAG_TOP_K = 6
RAG_FIELDS = [*TALK_FIELDS, "abstract"]

INSTRUCTIONS = """You are a helpful conference assistant.
Answer the attendee's question using ONLY the talks listed below.
- Mention each talk you use by its exact title, with day, time and room.
- If the talks don't answer the question, say you couldn't find it in the schedule.
- Keep the answer short: a few sentences or a short list.
- Times are local venue time."""


def format_talk(talk: dict) -> str:
    """One talk as plain text for the prompt."""
    return (
        f"- {talk['title']} | {', '.join(talk['speakers'])} | "
        f"{talk['start'][:16].replace('T', ' ')} to {talk['end'][11:16]} | {talk['room']} | "
        f"{talk['track']} | {talk['format']}\n  {talk['abstract']}"
    )


def build_prompt(question: str, talks: list[dict], profile: dict | None = None) -> str:
    """Combine instructions, attendee context, retrieved talks and the question."""
    parts = [INSTRUCTIONS]
    if profile:
        parts.append(
            f"About the attendee: {profile['role']}, {profile['experience_level']} level. "
            f"{profile['interests']} Attending: {', '.join(profile['available_days'])}."
        )
    parts.append("Talks:\n" + "\n".join(format_talk(t) for t in talks))
    parts.append(f"Question: {question}")
    return "\n\n".join(parts)


def ask(es: Elasticsearch, question: str, profile: dict | None = None) -> tuple[str, list[dict]]:
    """Answer `question` from the schedule. Returns (answer, talks used as sources)."""
    talks = search_talks(es, question, size=RAG_TOP_K, fields=RAG_FIELDS)
    if not talks:
        return "I couldn't find any talks related to that.", []
    return complete(es, build_prompt(question, talks, profile)), talks


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "When can I learn about securing containers?"
    es = get_client()
    answer, sources = ask(es, q, get_profile(es, DEMO_USER_ID))
    print(f"Q: {q}\n\n{answer}\n\nSources:")
    for t in sources:
        print(f"  - {t['title']} ({t['room']}, {t['start'][:16]})")
