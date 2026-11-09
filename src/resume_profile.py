"""Build an attendee profile from a resume PDF.

1. Extract the resume's text (pypdf).
2. Ask the LLM, through Elasticsearch's inference API, for the profile fields as JSON.
3. Validate and normalize them; the user reviews them before saving.
4. Save only the profile fields to the attendees index, never the resume itself.
"""

from __future__ import annotations

import io
import json
import uuid

from elasticsearch import ApiError, Elasticsearch, TransportError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

import config
from llm import complete

MAX_RESUME_CHARS = 12000  # enough for a few pages; keeps the prompt small
MIN_RESUME_CHARS = 100
MAX_FIELD_CHARS = 300
SAVE_TIMEOUT_SECONDS = 60  # indexing creates embeddings, which can take a few seconds
LEVELS = ["beginner", "intermediate", "advanced"]
GOALS = [
    "learn",
    "hiring",
    "job-seeking",
    "find-contributors",
    "meet-maintainers",
    "evaluate-tools",
    "find-mentor",
    "share-work",
]
NEW_ATTENDEE_LOCATION = "Main Entrance"

PROMPT = """Read the resume below and return ONLY a JSON object with these keys:
- "name": the person's name
- "role": their current job title, short (e.g. "Platform Engineer")
- "company": their current employer
- "experience_level": one of {levels}
- "working_on": one sentence, what they are building or working on now
- "interests": one sentence starting "Interested in", the conference topics they care about
- "goals": a list chosen only from {goals}
Return JSON only, with no other text.

Resume:
{resume}"""


def extract_text(pdf: bytes) -> str:
    """Return the text of a PDF. Raises ValueError if it can't be read."""
    try:
        reader = PdfReader(io.BytesIO(pdf))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except PdfReadError as err:
        raise ValueError("Couldn't read this PDF.") from err
    text = " ".join(text.split())
    if len(text) < MIN_RESUME_CHARS:
        raise ValueError("Couldn't find enough text in this PDF (is it a scanned image?).")
    return text[:MAX_RESUME_CHARS]


def build_prompt(resume_text: str) -> str:
    """Instructions plus the resume text."""
    return PROMPT.format(levels=LEVELS, goals=GOALS, resume=resume_text)


def clean(value: object) -> str:
    """Trim a text field to a safe length."""
    return " ".join(str(value or "").split())[:MAX_FIELD_CHARS]


def parse_profile(raw: str) -> dict:
    """Turn the LLM's reply into validated profile fields. Raises ValueError if unusable."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("The model didn't return a profile.")
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as err:
        raise ValueError("The model returned a malformed profile.") from err

    profile = {
        "name": clean(data.get("name")) or "New Attendee",
        "role": clean(data.get("role")) or "Attendee",
        "company": clean(data.get("company")),
        "experience_level": data.get("experience_level")
        if data.get("experience_level") in LEVELS
        else "intermediate",
        "working_on": clean(data.get("working_on")),
        "interests": clean(data.get("interests")),
        "goals": [g for g in data.get("goals") or [] if g in GOALS],
    }
    if not profile["working_on"] or not profile["interests"]:
        raise ValueError("The resume didn't give enough to describe your work and interests.")
    return profile


def draft_profile(es: Elasticsearch, pdf: bytes) -> dict:
    """Read a resume PDF and return draft profile fields for the user to review."""
    return parse_profile(complete(es, build_prompt(extract_text(pdf))))


def save_profile(es: Elasticsearch, fields: dict) -> str:
    """Save reviewed fields as a new checked-in attendee. Returns the new attendee id."""
    attendee_id = f"me-{uuid.uuid4().hex[:8]}"
    document = {
        **fields,
        "id": attendee_id,
        "available_days": config.CONFERENCE_DAYS,
        "checked_in": True,
        "current_location": NEW_ATTENDEE_LOCATION,
        "bookmarked_talks": [],
    }
    try:
        es.options(request_timeout=SAVE_TIMEOUT_SECONDS).index(
            index=config.ATTENDEES_INDEX, id=attendee_id, document=document, refresh="wait_for"
        )
    except (ApiError, TransportError) as err:
        raise RuntimeError(f"Couldn't save the profile: {err}") from err
    return attendee_id
