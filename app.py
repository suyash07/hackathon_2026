"""Streamlit UI. Displays results only; all logic lives in src/.

Run from the project root:  streamlit run app.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import config  # noqa: E402
from assistant import ask  # noqa: E402
from calendar_export import talk_to_ics  # noqa: E402
from es_client import get_client  # noqa: E402
from matchmaker import find_matches  # noqa: E402
from overview import (  # noqa: E402
    count_by,
    current_time,
    happening_now,
    key_numbers,
    side_events_on,
    up_next,
)
from profiles import DEMO_USER_ID, get_profile, list_profiles  # noqa: E402
from search import recommend_talks, search_talks  # noqa: E402
from voice import get_transcriber, transcribe, voice_enabled  # noqa: E402
from who_to_meet import who_to_meet  # noqa: E402

NO_PROFILE = "(no profile)"

st.set_page_config(page_title="Conference Search", page_icon="🔎", layout="wide")


@st.cache_resource
def es_client():
    """One Elasticsearch client for the whole app session."""
    return get_client()


@st.cache_data(ttl=300)
def profile_choices() -> list[dict]:
    return list_profiles(es_client())


@st.cache_data(ttl=300)
def cached_who_to_meet(talk_id: str, exclude_ids: tuple[str, ...]) -> list[dict]:
    """Cached people-to-meet lookup for one talk."""
    return who_to_meet(es_client(), talk_id, exclude_ids=list(exclude_ids) or None)


@st.cache_data(ttl=60)
def cached_key_numbers() -> dict:
    """Cached metric tiles."""
    return key_numbers(es_client())


def clock(t: datetime) -> str:
    """'2:30' instead of '02:30'."""
    return t.strftime("%I:%M").lstrip("0")


def format_time(start: str, end: str) -> str:
    """'Tue Nov 10 · 2:30–3:05 PM' from ISO timestamps."""
    s, e = datetime.fromisoformat(start), datetime.fromisoformat(end)
    return f"{s:%a %b} {s.day} · {clock(s)}–{clock(e)} {e:%p}"


def talk_card(talk: dict, bookmarked: set[str], people: list[dict] | None = None) -> None:
    """Render one talk, optionally with the people worth meeting there."""
    with st.container(border=True):
        star = "★ " if talk["id"] in bookmarked else ""
        st.markdown(f"**{star}{talk['title']}**")
        st.caption(
            f"{format_time(talk['start'], talk['end'])} · {talk['room']} · "
            f"{talk['track']} · {talk['format']}"
        )
        st.write(", ".join(talk["speakers"]))
        st.caption(" ".join(f"`{tag}`" for tag in talk.get("tags", [])))
        if people:
            names = ", ".join(f"{p['name']} ({p['role']})" for p in people)
            st.markdown(f"🤝 **Who to meet:** {names}")
        st.download_button(
            "📅 Add to calendar",
            data=talk_to_ics(talk),
            file_name=f"{talk['id']}.ics",
            mime="text/calendar",
            key=f"ics-{talk['id']}",
        )


def person_card(person: dict) -> None:
    """Render one attendee match."""
    with st.container(border=True):
        st.markdown(f"**{person['name']}** · {person['role']}, {person['company']}")
        st.write(person["working_on"])
        where = person.get("current_location") or "not checked in"
        st.caption(f"📍 {where} · goals: {', '.join(person.get('goals', []))}")


def sidebar_profile() -> dict | None:
    """Profile picker. Returns the selected profile, or None."""
    st.sidebar.header("Who are you?")
    choices = profile_choices()
    labels = [NO_PROFILE] + [f"{p['name']} — {p['role']}" for p in choices]
    ids = [None] + [p["id"] for p in choices]
    default = ids.index(DEMO_USER_ID) if DEMO_USER_ID in ids else 0
    picked = st.sidebar.selectbox(
        "Profile", range(len(labels)), index=default, format_func=lambda i: labels[i]
    )
    if ids[picked] is None:
        return None

    profile = get_profile(es_client(), ids[picked])
    st.sidebar.markdown(f"**Working on:** {profile['working_on']}")
    st.sidebar.markdown(f"**Interests:** {profile['interests']}")
    st.sidebar.caption(f"Attending: {', '.join(profile['available_days'])}")
    return profile


def talk_search_tab(profile: dict | None) -> None:
    query = st.text_input("Search")
    show_people = st.checkbox("Show who to meet at each talk")
    bookmarked = set(profile["bookmarked_talks"]) if profile else set()
    me = (profile["id"],) if profile else ()

    def people_for(talk: dict) -> list[dict] | None:
        return cached_who_to_meet(talk["id"], me) if show_people else None

    results = search_talks(es_client(), query) if query else []
    if query:
        st.subheader(f"Results for “{query}”")
        if not results:
            st.info("No matching talks.")
        for talk in results:
            talk_card(talk, bookmarked, people_for(talk))

    if profile:
        st.subheader("Based on your profile, you might like")
        shown = [t["id"] for t in results]
        for talk in recommend_talks(es_client(), profile, exclude_ids=shown):
            talk_card(talk, bookmarked, people_for(talk))


def matchmaker_tab(profile: dict | None) -> None:
    if not profile:
        st.info("Pick a profile in the sidebar to find people working on similar things.")
        return
    st.write(f"People working on things like: *{profile['working_on']}*")
    in_building = st.checkbox("Only people in the building right now", value=True)
    matches = find_matches(es_client(), profile, in_building_only=in_building)
    if not matches:
        st.info("No matches found.")
    for person in matches:
        person_card(person)


@st.cache_resource
def transcriber():
    """One OpenAI client for the whole app session."""
    return get_transcriber()


@st.cache_data(show_spinner=False)
def speech_to_text(audio: bytes) -> str:
    """Transcribe once per recording, so reruns don't call the API again."""
    return transcribe(transcriber(), audio)


def voice_question() -> str:
    """Mic input. Returns the transcribed question, or '' if nothing was recorded."""
    if not voice_enabled():
        st.caption("🎤 Voice questions are off: add OPENAI_API_KEY to .env to enable them.")
        return ""
    recording = st.audio_input("Or ask by voice")
    if recording is None:
        return ""
    try:
        with st.spinner("Transcribing..."):
            text = speech_to_text(recording.getvalue())
    except RuntimeError as err:
        st.error(str(err))
        return ""
    st.caption(f"🎤 You said: “{text}”")
    return text


def assistant_tab(profile: dict | None) -> None:
    typed = st.text_input("Ask a question")
    spoken = voice_question()
    question = typed or spoken
    if not question:
        return
    try:
        with st.spinner("Searching the schedule..."):
            answer, talks = ask(es_client(), question, profile)
    except RuntimeError as err:
        st.error(str(err))
        return
    st.markdown(answer)
    with st.expander(f"Talks searched ({len(talks)})"):
        for talk in talks:
            when = format_time(talk["start"], talk["end"])
            st.markdown(f"- **{talk['title']}** · {when} · {talk['room']}")


def day_label(day: str) -> str:
    """'2026-11-10' -> 'Tue Nov 10'."""
    d = datetime.fromisoformat(day)
    return f"{d:%a %b} {d.day}"


def talk_line(talk: dict) -> str:
    """One talk as a compact markdown line."""
    return f"- **{talk['title']}** · {format_time(talk['start'], talk['end'])} · {talk['room']}"


def overview_tab() -> None:
    es = es_client()
    now = current_time()
    st.subheader(config.CONFERENCE_NAME)
    st.write(f"📍 {config.CONFERENCE_PLACE} · 🗓 {config.CONFERENCE_DATES}")
    if config.DEMO_NOW:
        st.caption(f"Demo time: {now:%a %b} {now.day} · {clock(now)} {now:%p}")

    numbers = cached_key_numbers()
    for col, (label, key) in zip(
        st.columns(4),
        [
            ("Talks", "talks"),
            ("Speakers", "speakers"),
            ("Tracks", "tracks"),
            ("In the building now", "in_building"),
        ],
    ):
        col.metric(label, numbers[key])

    now_col, next_col = st.columns(2)
    with now_col:
        st.markdown("#### ⏱ Happening now")
        talks = happening_now(es, now)
        st.markdown("\n".join(talk_line(t) for t in talks) if talks else "Nothing right now.")
    with next_col:
        st.markdown("#### ⏭ Up next (next hour)")
        talks = up_next(es, now)
        st.markdown(
            "\n".join(talk_line(t) for t in talks) if talks else "Nothing in the next hour."
        )

    st.markdown("#### Talks per track")
    st.bar_chart({"talks": count_by(es, "track")}, horizontal=True)

    st.markdown("#### Talks per day")
    per_day = count_by(es, "day", by_key=True)
    for col, (day, n) in zip(st.columns(len(per_day) or 1), per_day.items()):
        col.metric(day_label(day), n)

    st.markdown("#### 🎉 Side events today")
    events = side_events_on(es, now)
    if not events:
        st.write("No side events today.")
    for e in events:
        start = datetime.fromisoformat(e["start"])
        st.markdown(f"- **{e['name']}** · {clock(start)} {start:%p} · {e['location']}")

    st.markdown("#### How to use this app")
    st.markdown(
        "- **Talk Search:** describe what you want to learn; results match by meaning.\n"
        "- **Hallway Matchmaker:** find people in the building working on similar things.\n"
        "- **Assistant:** ask anything about the schedule and get an answer with talks cited."
    )


def main() -> None:
    st.title("🔎 Conference Search")
    st.caption("Conference companion · all data synthetic")
    try:
        profile = sidebar_profile()
    except Exception as err:  # connection problems should show, not crash
        st.error(f"Can't reach Elasticsearch: {err}")
        st.stop()

    overview, search_tab, match_tab, assistant = st.tabs(
        ["Overview", "Talk Search", "Hallway Matchmaker", "Assistant"]
    )
    with overview:
        overview_tab()
    with search_tab:
        talk_search_tab(profile)
    with match_tab:
        matchmaker_tab(profile)
    with assistant:
        assistant_tab(profile)


main()
