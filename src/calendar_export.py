"""Turn a talk into an .ics calendar file (works with Google, Apple and Outlook calendars)."""

from __future__ import annotations

from datetime import datetime, timezone

REMINDER_MINUTES = 15
PRODID = "-//Conference Search//EN"
MAX_LINE = 73  # iCalendar lines must be folded at 75 octets


def to_utc(iso: str) -> str:
    """'2026-11-10T10:30:00-07:00' -> '20261110T173000Z'."""
    return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def escape(text: str) -> str:
    """Escape characters that have a special meaning in iCalendar text."""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line: str) -> str:
    """Split long lines; continuation lines start with a space."""
    parts = [line[i : i + MAX_LINE] for i in range(0, len(line), MAX_LINE)] or [""]
    return "\r\n ".join(parts)


def talk_to_ics(talk: dict, now: datetime | None = None) -> str:
    """Return a one-event calendar file for `talk`, with a reminder before it starts."""
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    details = f"{', '.join(talk['speakers'])} | {talk['track']} | {talk['format']}"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "BEGIN:VEVENT",
        f"UID:{talk['id']}@conference-search",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{to_utc(talk['start'])}",
        f"DTEND:{to_utc(talk['end'])}",
        f"SUMMARY:{escape(talk['title'])}",
        f"LOCATION:{escape(talk['room'])}",
        f"DESCRIPTION:{escape(details)}",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{escape(talk['title'])}",
        f"TRIGGER:-PT{REMINDER_MINUTES}M",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(fold(line) for line in lines) + "\r\n"
