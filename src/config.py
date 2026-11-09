"""All settings in one place. Everything else imports from here."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASSWORD = os.getenv("ES_PASSWORD")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5-5")

DATA_DIR = ROOT / "data"
