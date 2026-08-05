"""Cloud squad state for the Streamlit edge (ADR-054).

Squads on the deployed app are **per-user, no server**: a session **active squad** in `st.session_state`
(built on the Build page or uploaded), persisted as the **user's own downloadable `squad.json`** (the CLI
`SquadStore` format, so it's interoperable). The demo squad(s) come from `SquadStore` (read-only, a
committed `seed_squads.json`). The web **never writes** — the DB/squads stay read-only.
"""

import json

import streamlit as st

from src.squads import SquadStore
from src.storage import Storage

_SESSION_KEY = "squad"
_UPLOAD_APPLIED = "_squad_upload_id"


def active_squad():
    """The session's active squad dict (built or uploaded), or None."""
    return st.session_state.get(_SESSION_KEY)


def set_active_squad(squad: dict) -> None:
    st.session_state[_SESSION_KEY] = squad


def demo_squads() -> dict:
    """`{name: squad_dict}` — the committed demo squads (read-only, via SquadStore)."""
    store = SquadStore()
    return {name: store.load(name) for name in store.names()}


def available_squads() -> dict:
    """`{label: squad_dict}` — the demo squads plus the session active squad (if any)."""
    squads = dict(demo_squads())
    act = active_squad()
    if act:
        squads[f"{act.get('name', 'My squad')} (yours)"] = act
    return squads


def squad_picker(label: str = "Squad", key: str | None = None) -> tuple[str, dict]:
    """A selectbox over the available squads (demo + session) → (label, squad_dict). Defaults to the
    session **active squad** when one is set. There's always at least the committed demo, so it never
    returns nothing. The shared entry point for Transfer/Analyse/Captain (ADR-054)."""
    squads = available_squads()
    labels = list(squads)
    if not labels:                          # no demo seed and nothing built/uploaded (an empty store)
        st.info("No squad yet — **build** one on the Build page, or **upload** a `squad.json` "
                "(sidebar).")
        st.stop()
    act = active_squad()
    index = next((i for i, s in enumerate(squads.values()) if s is act), 0)   # default to the active one
    choice = st.selectbox(label, labels, index=index, key=key)
    return choice, squads[choice]


def parse_uploaded(uploaded) -> tuple[dict | None, str | None]:
    """Validate an uploaded `squad.json` → (squad_dict, error). Accepts a bare squad dict or a
    `{name: squad}` file (the SquadStore format); checks the ids exist in the current data."""
    try:
        data = json.loads(uploaded.getvalue().decode("utf-8"))
    except Exception:
        return None, "That file isn't valid JSON."
    if isinstance(data, dict) and "player_ids" not in data and len(data) == 1:
        name, squad = next(iter(data.items()))     # a {name: squad} file → take the single squad
        data = {**squad, "name": name}
    if not isinstance(data, dict) or "player_ids" not in data:
        return None, "That doesn't look like a squad file (no `player_ids`)."
    ids = data.get("player_ids") or []
    if not (11 <= len(ids) <= 15):
        return None, f"A squad needs 11–15 players (found {len(ids)})."
    store = Storage()
    try:
        known = {p["id"] for p in store.get_players()}
    finally:
        store.close()
    missing = [i for i in ids if i not in known]
    if missing:
        return None, f"{len(missing)} player id(s) aren't in the current data — is this an old squad?"
    data.setdefault("name", "Uploaded squad")
    return data, None


def render_sidebar() -> None:
    """The sidebar squad controls (ADR-054), shown on every squad page: the active-squad name + an
    uploader. The upload is applied once (keyed by the file id), so it won't clobber a built squad."""
    with st.sidebar:
        st.subheader("Your squad")
        act = active_squad()
        st.caption(f"Active: **{act['name'] if act else 'none'}**"
                   if act else "Active: **none** — build one or upload a `squad.json`.")
        uploaded = st.file_uploader("Upload a squad.json", type="json", key="squad_uploader")
        if uploaded is not None and st.session_state.get(_UPLOAD_APPLIED) != uploaded.file_id:
            squad, err = parse_uploaded(uploaded)
            if err:
                st.error(err)
            else:
                set_active_squad(squad)
                st.session_state[_UPLOAD_APPLIED] = uploaded.file_id
                st.success(f"Loaded **{squad['name']}** ({len(squad['player_ids'])} players).")
