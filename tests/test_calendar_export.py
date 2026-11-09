import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from calendar_export import escape, talk_to_ics, to_utc  # noqa: E402

TALK = {
    "id": "t049",
    "title": "Syscall-Level Defense: From Zero to Production",
    "speakers": ["Maya Rossi", "Arjun Martinez"],
    "track": "Security",
    "format": "talk",
    "room": "Room 4",
    "start": "2026-11-10T11:30:00-07:00",
    "end": "2026-11-10T12:05:00-07:00",
}


def test_to_utc_converts_venue_time():
    assert to_utc("2026-11-10T11:30:00-07:00") == "20261110T183000Z"


def test_escape_special_characters():
    assert escape("a, b; c") == "a\\, b\\; c"


def test_ics_has_event_times_and_reminder():
    ics = talk_to_ics(TALK, now=datetime(2026, 11, 9, tzinfo=timezone.utc))
    assert ics.startswith("BEGIN:VCALENDAR\r\n")
    assert "DTSTART:20261110T183000Z" in ics
    assert "DTEND:20261110T190500Z" in ics
    assert "LOCATION:Room 4" in ics
    assert "TRIGGER:-PT15M" in ics
    assert ics.endswith("END:VCALENDAR\r\n")


def test_non_ascii_lines_are_folded_by_utf8_octets():
    title = "é" * 100
    long_talk = {**TALK, "title": title}
    ics = talk_to_ics(long_talk)

    for line in ics.split("\r\n"):
        assert len(line.encode("utf-8")) <= 75
    assert f"SUMMARY:{title}" in ics.replace("\r\n ", "")
