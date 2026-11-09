import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from resume_profile import build_prompt, parse_profile  # noqa: E402

GOOD = """Here you go:
{"name": "Jordan Ellis", "role": "Platform Engineer", "company": "Lumenfield Systems",
 "experience_level": "advanced",
 "working_on": "Kernel-level runtime security for Kubernetes.",
 "interests": "Interested in runtime security and AI agents for operations.",
 "goals": ["learn", "find-contributors", "make-friends"]}"""


def test_parses_json_inside_extra_text():
    p = parse_profile(GOOD)
    assert p["name"] == "Jordan Ellis"
    assert p["experience_level"] == "advanced"


def test_drops_unknown_goals():
    assert parse_profile(GOOD)["goals"] == ["learn", "find-contributors"]


def test_unknown_level_falls_back():
    raw = GOOD.replace('"advanced"', '"guru"')
    assert parse_profile(raw)["experience_level"] == "intermediate"


def test_missing_interests_is_rejected():
    raw = GOOD.replace("Interested in runtime security and AI agents for operations.", "")
    with pytest.raises(ValueError):
        parse_profile(raw)


def test_non_json_is_rejected():
    with pytest.raises(ValueError):
        parse_profile("Sorry, I can't help with that.")


def test_prompt_contains_resume_and_allowed_values():
    prompt = build_prompt("RESUME TEXT")
    assert "RESUME TEXT" in prompt and "find-mentor" in prompt and "advanced" in prompt
