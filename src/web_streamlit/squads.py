"""Cloud squad state for the Streamlit edge (ADR-054).

Squads on the deployed app are **per-user, no server**: a session **active squad** in `st.session_state`
(built on the Build page or uploaded), persisted as the **user's own downloadable `squad.json`** (the CLI
`SquadStore` format, so it's interoperable). The demo squad(s) come from `SquadStore` (read-only, a
committed `seed_squads.json`). The web **never writes** — the DB/squads stay read-only.
"""

import json

import streamlit as st

from src.analytics import squad_15_issues
from src.manager import fetch_manager_team
from src.squads import SquadStore
from src.storage import Storage

# The FPL squad budget (£m) — the reference for the *soft* over-budget warning on an edit (ADR-055).
FPL_BUDGET = 100.0

_SESSION_KEY = "squad"
_UPLOAD_APPLIED = "_squad_upload_id"


def active_squad():
    """The session's active squad dict (built or uploaded), or None."""
    return st.session_state.get(_SESSION_KEY)


def set_active_squad(squad: dict) -> None:
    st.session_state[_SESSION_KEY] = squad


def demo_squads() -> dict:
    """`{name: squad_dict}` — the committed demo squads (read-only, via SquadStore). Each dict carries its
    own `name` so every squad (demo or session) is uniformly named (used by the sidebar / after an edit)."""
    store = SquadStore()
    return {name: {**store.load(name), "name": name} for name in store.names()}


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
    choice = st.selectbox(label, labels, index=index, key=key,
                          help="Which squad to work on — your active/built one, or the demo.")
    return choice, squads[choice]


def rename(squad: dict, name: str) -> dict:
    """A copy of `squad` renamed. A blank name keeps the existing one (never nameless)."""
    new = dict(squad)
    new["name"] = name.strip() or squad.get("name", "My squad")
    return new


def set_captain(squad: dict, captain_id) -> dict:
    """A copy of `squad` with `captain_id` set — but only if it's one of the squad's players (else None,
    so a stale captain can't linger). Shown as **(C)** and travels in the download (ADR-055)."""
    new = dict(squad)
    new["captain_id"] = captain_id if captain_id in squad["player_ids"] else None
    return new


def captain_bonus(captain_id, xi_ids, by_gameweek_by_id, next_gw) -> float:
    """The captain's extra points from the armband, for the **next gameweek only** (ADR-083).

    A captain scores double in one GW, and captaincy is re-chosen weekly — so the projected-XI total adds one
    extra copy of the captain's *next-GW* xP, but only when a captain is **set and in the projected XI** (a
    benched captain isn't doubled; FPL auto-subs to the vice). Empty-safe → 0.0."""
    if captain_id is None or next_gw is None or captain_id not in set(xi_ids):
        return 0.0
    return (by_gameweek_by_id.get(captain_id) or {}).get(next_gw, 0.0)


def set_bench(squad: dict, bench_ids) -> dict:
    """A copy of `squad` with a new bench (the rest are the XI). The **order is the sub priority**
    (ADR-079) — preserved as given, not re-sorted. Display/analysis honour the *set*; the order drives the
    auto-sub priority. Legality of the resulting XI is the caller's soft warning (ADR-022), not a block."""
    new = dict(squad)
    new["bench_ids"] = list(bench_ids)
    return new


def move_bench_sub(squad: dict, player_id: int, direction: str, by_id) -> dict:
    """Move an **outfield** bench player up/down one step in the sub priority (ADR-079).

    Copy-not-mutate (ADR-055). The bench GK is keeper-only, so it's excluded from the reorder and kept last.
    A no-op if `player_id` isn't an outfield sub, or it's already at the end it's moving toward. `by_id`
    maps id → player (for the position lookup); `direction` is "up" (higher priority) or "down"."""
    bench = squad.get("bench_ids", [])
    outfield = [i for i in bench if i in by_id and by_id[i]["position"] != "GK"]
    gk = [i for i in bench if i not in outfield]                 # the GK (and any unknown id) kept aside
    if player_id in outfield:
        idx = outfield.index(player_id)
        swap = idx - 1 if direction == "up" else idx + 1
        if 0 <= swap < len(outfield):
            outfield[idx], outfield[swap] = outfield[swap], outfield[idx]
    new = dict(squad)
    new["bench_ids"] = outfield + gk
    return new


def apply_transfer(squad: dict, out_id: int, in_id: int, players,
                   budget: float = FPL_BUDGET) -> tuple[bool, list, str | None, dict | None]:
    """Swap `out_id`→`in_id` on a **copy** of `squad`, legality-checked (ADR-055).

    Returns `(ok, issues, warning, new_squad)`. A structurally illegal result (positions / ≤3-club, via
    `squad_15_issues`) → `ok=False` + the `issues`, no change. Legal → `ok=True`, the mutated `new_squad`
    (ids/names/bench/cost updated; a captain that left is cleared), and a **soft** `warning` string if it's
    over `budget` (never blocks — prices drift). No server write: the caller sets it as the active squad.
    """
    by_id = {p["id"]: p for p in players}
    new_ids = [in_id if i == out_id else i for i in squad["player_ids"]]
    new_players = [by_id[i] for i in new_ids if i in by_id]
    issues = squad_15_issues(new_players)
    if issues:
        return False, issues, None, None

    new = dict(squad)
    new["player_ids"] = new_ids
    new["player_names"] = [by_id[i]["web_name"] for i in new_ids]
    new["bench_ids"] = [in_id if i == out_id else i for i in squad.get("bench_ids", [])]
    if new.get("captain_id") == out_id:
        new["captain_id"] = None                      # the captain was transferred out — clear it
    cost = round(sum(by_id[i]["price"] for i in new_ids), 1)
    new["cost"] = cost
    warning = (f"£{cost - budget:.1f}m over the £{budget:.0f}m budget"
               if budget is not None and cost > budget else None)
    return True, [], warning, new


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
    if data.get("captain_id") is not None and data["captain_id"] not in ids:
        return None, "The captain isn't one of the squad's players."
    data.setdefault("name", "Uploaded squad")
    return data, None


def render_sidebar() -> None:
    """The sidebar squad controls (ADR-054), shown on every squad page: the active-squad name + an
    uploader. The upload is applied once (keyed by the file id), so it won't clobber a built squad."""
    with st.sidebar:
        st.subheader("Your squad")
        act = active_squad()
        st.caption(f"Active: **{act.get('name', 'unnamed')}**"
                   if act else "Active: **none** — build one or upload a `squad.json`.")
        uploaded = st.file_uploader("Upload a squad.json", type="json", key="squad_uploader",
                                    help="Load a squad.json you downloaded earlier (from Build Squad).")
        if uploaded is not None and st.session_state.get(_UPLOAD_APPLIED) != uploaded.file_id:
            squad, err = parse_uploaded(uploaded)
            if err:
                st.error(err)
            else:
                set_active_squad(squad)
                st.session_state[_UPLOAD_APPLIED] = uploaded.file_id
                st.success(f"Loaded **{squad['name']}** ({len(squad['player_ids'])} players).")

        # Import your real FPL team by manager-ID (ADR-058) — sets the session active squad (no server
        # write). Picks are public only after the GW1 deadline; degrades with a clear message until then.
        st.caption("— or import your FPL team —")
        manager_id = st.text_input(
            "FPL manager-ID", key="manager_id", placeholder="e.g. 1234567",
            help="Your FPL team's numeric id (in your team's URL on fantasy.premierleague.com). "
                 "Imports your real squad — picks are public from the GW1 deadline.")
        if st.button("Import team", help="Fetch your real squad for this manager-ID (no login needed).") \
                and manager_id.strip():
            if not manager_id.strip().isdigit():
                st.error("The manager-ID should be a number (find it in your FPL team URL).")
            else:
                store = Storage()
                try:
                    players = store.get_players()
                finally:
                    store.close()
                squad, message = fetch_manager_team(int(manager_id.strip()), players)
                if squad:
                    set_active_squad(squad)
                    st.success(message)
                else:
                    st.info(message)

    render_cloud_sync()          # ☁ cross-device Save/Load in the sidebar (US-331) — below the squad controls


def render_cloud_sync() -> None:
    """The ☁ cross-device **Save / Load** (US-310/331, ADR-094), shown in the **Squads sidebar** so it's visible on
    every sub-view — not buried under My Squad. **Secret-gated:** hidden unless the store is configured (the app
    otherwise stays download/upload-only, ADR-054). **Save** needs an active squad (disabled + a hint otherwise);
    **Load**/**Clear** work by handle and set the session's active squad. A handle is the key — no login."""
    from src.web_streamlit import cloud_store
    if not cloud_store.is_configured():
        return
    squad = active_squad()
    with st.sidebar, st.expander("☁ Save / Load across devices"):
        handle = st.text_input("Your handle", key="cloud_handle",
                               help="A name only you'd guess — it's the key to your squad on any device.")
        clean = cloud_store.clean_handle(handle)
        c_save, c_load, c_clear = st.columns(3)
        if c_save.button("Save", disabled=not (clean and squad), key="cloud_save"):
            try:
                taken = cloud_store.exists(clean)              # US-321: new vs overwrite (a handle isn't private)
                cloud_store.save_squad(clean, squad)
                if taken:
                    st.warning(f"Updated **{clean}** — overwrote the squad already saved under that handle. "
                               "(Handles aren't private — pick one only you'd guess.)")
                else:
                    st.success(f"Saved as **{clean}** — load it on any device with that handle.")
            except Exception as exc:   # surface the real store error (e.g. an RLS policy), not a blind note
                st.error(f"Save failed — **{cloud_store.store_error(exc)}**. Your download still works.")
        if c_load.button("Load", disabled=not clean, key="cloud_load"):
            try:
                loaded = cloud_store.load_squad(clean)
            except Exception as exc:
                loaded = None
                st.error(f"Load failed — **{cloud_store.store_error(exc)}**.")
            if loaded:
                set_active_squad(loaded)
                st.success(f"Loaded **{clean}**.")
                st.rerun()
            elif clean:
                st.info(f"No squad saved under **{clean}** yet — Save one first.")
        if c_clear.button("Clear", disabled=not clean, key="cloud_clear"):
            try:
                cloud_store.delete_squad(clean)
                st.success(f"Cleared **{clean}**.")
            except Exception as exc:
                st.error(f"Clear failed — **{cloud_store.store_error(exc)}**.")
        if handle and not clean:
            st.caption("A handle is 2–32 letters, numbers, - or _.")
        if not squad:
            st.caption("Build or load a squad first to **Save** it — **Load** works any time.")
        st.caption("Stored: your handle + squad (public FPL players), **no login**. Anyone who knows the "
                   "handle can read or overwrite it — use one only you'd guess. **Clear** removes it.")
