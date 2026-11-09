"""Streamlit UI. Displays results only; all logic lives in src/.

Run from the project root:  streamlit run app.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from assistant import ask  # noqa: E402
from calendar_export import talk_to_ics  # noqa: E402
from es_client import get_client  # noqa: E402
from matchmaker import find_matches  # noqa: E402
from profiles import DEMO_USER_ID, get_profile, list_profiles  # noqa: E402
from search import recommend_talks, search_talks  # noqa: E402
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


def assistant_tab(profile: dict | None) -> None:
    question = st.text_input("Ask a question")
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


def main() -> None:
    st.title("🔎 Conference Search")
    st.caption("Conference companion · all data synthetic")
    try:
        profile = sidebar_profile()
    except Exception as err:  # connection problems should show, not crash
        st.error(f"Can't reach Elasticsearch: {err}")
        st.stop()

    search_tab, match_tab, assistant = st.tabs(["Talk Search", "Hallway Matchmaker", "Assistant"])
    with search_tab:
        talk_search_tab(profile)
    with match_tab:
        matchmaker_tab(profile)
    with assistant:
        assistant_tab(profile)


main()
