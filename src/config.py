"""All settings in one place. Everything else imports from here."""

import os
from datetime import timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASSWORD = os.getenv("ES_PASSWORD")
ES_API_KEY = os.getenv("ES_API_KEY")  # Elastic Cloud: use an API key instead of user/password

# Elasticsearch inference endpoint that writes RAG answers (see README: "LLM setup").
# The LLM provider's key is stored inside Elasticsearch, not in this app.
LLM_INFERENCE_ID = os.getenv("LLM_INFERENCE_ID", "openai-completion")

# Conference details shown on the Overview tab
CONFERENCE_NAME = "Cloud Native Conference 2026"
CONFERENCE_PLACE = "Salt Lake City, Utah"
CONFERENCE_DATES = "Nov 9–12, 2026"
VENUE_TZ = timezone(timedelta(hours=-7))  # Salt Lake City in November (MST)

# Optional fixed "now" for demos, e.g. 2026-11-10T11:40:00-07:00. Empty = real clock.
DEMO_NOW = os.getenv("DEMO_NOW")

DATA_DIR = ROOT / "data"

# Elasticsearch index names
TALKS_INDEX = "talks"
SPEAKERS_INDEX = "speakers"
ATTENDEES_INDEX = "attendees"
SIDE_EVENTS_INDEX = "side_events"
