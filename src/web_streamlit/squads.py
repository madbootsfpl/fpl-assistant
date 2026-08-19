"""Cloud squad state for the Streamlit edge (ADR-054).

Squads on the deployed app are **per-user, no server**: a session **active squad** in `st.session_state`
(built on the Build page or uploaded), persisted as the **user's own downloadable `squad.json`** (the CLI
`SquadStore` format, so it's interoperable). The demo squad(s) come from `SquadStore` (read-only, a
committed `seed_squads.json`). The web **never writes** — the DB/squads stay read-only.
"""

import datetime
import html
import json
import re

import streamlit as st

from src.analytics import legal_xi_issues, squad_15_issues
from src.manager import fetch_manager_team
from src.squads import SquadStore
from src.storage import Storage

# The FPL squad budget (£m) — the reference for the *soft* over-budget warning on an edit (ADR-055).
FPL_BUDGET = 100.0

_SESSION_KEY = "squad"
_UPLOAD_APPLIED = "_squad_upload_id"
_CLOUD_LINKED = "_cloud_linked_handle"   # the handle this squad is Saved/Loaded under → mirror edits to the cloud


def active_squad():
    """The session's active squad dict (built or uploaded), or None."""
    return st.session_state.get(_SESSION_KEY)


def set_active_squad(squad: dict) -> None:
    st.session_state[_SESSION_KEY] = squad
    _autosync(squad)                     # keep a cloud-linked squad in sync across devices (US-357/C1)


def _autosync(squad: dict) -> None:
    """Best-effort: mirror an edit to the cloud when this squad is **linked** to a handle (the user Saved or Loaded
    it this session, `_CLOUD_LINKED`) and the store is configured — so a **captain** / transfer / bench change syncs
    across devices (US-357/C1), not just the *last manual Save*. **Fail-silent** — a sync hiccup never blocks the
    edit; the manual Save stays the source of truth. Only fires for cloud-linked squads (a built/uploaded squad with
    no handle writes nothing — the opt-in server-write invariant holds, ADR-094/054)."""
    handle = st.session_state.get(_CLOUD_LINKED)
    if not handle:
        return
    try:
        from src.web_streamlit import cloud_store
        if cloud_store.is_configured():
            cloud_store.save_squad(handle, squad)
    except Exception:
        return


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


def substitute(squad: dict, off_id: int, on_id: int, by_id) -> tuple[dict, list]:
    """Substitute a starter for a bench player on a **copy** of `squad` (a lineup change, not a transfer;
    ADR-055/079). `off_id` (a current XI player) goes to the bench, **taking `on_id`'s slot** in the sub
    order; `on_id` (a current bench player) comes into the XI. The set of 15 is unchanged — only the
    XI/bench split moves.

    Returns `(new_squad, issues)` where `issues` is the resulting XI's legality (`legal_xi_issues`): a
    non-empty list means the caller must **not** commit it — e.g. subbing the only GK for an outfielder
    (0 keepers), or a swap that breaks the formation. Copy-not-mutate; no server write (the caller sets the
    active squad). The UI offers only bring-ons that come back with **no** issues."""
    bench = squad.get("bench_ids", [])
    new_bench = [off_id if i == on_id else i for i in bench]     # on → XI; off takes on's bench (priority) slot
    new = set_bench(squad, new_bench)
    bench_set = set(new["bench_ids"])
    xi = [by_id[i] for i in new["player_ids"] if i not in bench_set and i in by_id]
    return new, legal_xi_issues(xi)


def link_and_restore(handle: str) -> None:
    """Link the session's squad to a cloud `handle` and **restore** it from the cloud if none is active yet
    (US-362/ADR-106). Used on Google-auth admit with a per-user key (`auth.user_key`): sets `_CLOUD_LINKED` so every
    future edit **auto-syncs** (S145), and — when the session has **no** active squad (e.g. a mobile reconnect wiped
    it) — re-fetches the user's squad so it **follows them across devices/reconnects**. Best-effort + fail-silent;
    never clobbers a squad already active this session (a fresh build stays)."""
    st.session_state[_CLOUD_LINKED] = handle
    if active_squad() is not None:
        return
    try:
        from src.web_streamlit import cloud_store
        if cloud_store.is_configured():
            loaded = cloud_store.load_squad(handle)
            if loaded:
                set_active_squad(loaded)
    except Exception:
        return


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


def apply_transfer_plan(squad: dict, plan: list, players,
                        budget: float = FPL_BUDGET) -> tuple[bool, list, str | None, dict | None]:
    """Apply a **coordinated plan** of transfers (each `{out:{id,…}, in:{id,…}}`, from `suggest_transfer_plan`)
    to a **copy** of `squad`, in one atomic step (ADR-046/055).

    The N-transfer counterpart of `apply_transfer`: maps every `out.id → in.id`, then validates the **whole**
    result once (`squad_15_issues`). Returns `(ok, issues, warning, new_squad)` — a structurally illegal result
    → `ok=False` + `issues`, no change; legal → `ok=True` and the mutated `new_squad` (ids/names/bench updated,
    a captain that was sold cleared), plus a **soft** over-`budget` `warning` (never blocks — prices drift). No
    server write: the caller sets it active."""
    by_id = {p["id"]: p for p in players}
    out_to_in = {m["out"]["id"]: m["in"]["id"] for m in plan}
    new_ids = [out_to_in.get(i, i) for i in squad["player_ids"]]
    new_players = [by_id[i] for i in new_ids if i in by_id]
    issues = squad_15_issues(new_players)
    if issues:
        return False, issues, None, None

    new = dict(squad)
    new["player_ids"] = new_ids
    new["player_names"] = [by_id[i]["web_name"] for i in new_ids]
    new["bench_ids"] = [out_to_in.get(i, i) for i in squad.get("bench_ids", [])]
    if new.get("captain_id") in out_to_in:                # a captain that was sold in the plan → clear it
        new["captain_id"] = None
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
    """A **slim** sidebar squad status (ADR-113/US-385), shown on every squad page: the active-team name + a pointer
    to the one **Your team** panel on My Squad, where import · backup · sync now live together (they used to be
    scattered across the sidebar). The ☁ handle Save/Load stays only as the **no-login fallback** (US-384)."""
    with st.sidebar:
        st.subheader("Your squad")
        act = active_squad()
        st.caption(f"Active: **{act.get('name', 'unnamed')}**" if act
                   else "Active: **none** yet.")
        st.caption("⚙ Import · back up · sync your team in the **Your team** panel on **My Squad**.")
    render_cloud_sync()          # ☁ handle Save/Load — no-login fallback only (hidden when signed in, US-384)


_YTB_CSS = """<style>
.ytb-card{position:relative;border:1.5px solid #cfa4f0;border-radius:14px;
  background:linear-gradient(135deg,#ecdafb 0%,#f4e9fd 62%,#efe0fc 100%);
  box-shadow:0 1px 2px rgba(16,24,40,.06),0 8px 22px -10px rgba(139,47,201,.42);
  padding:14px 18px 13px 22px;overflow:hidden;margin:2px 0 10px;}
.ytb-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:7px;
  background:linear-gradient(180deg,#8B2FC9,#FF6A00);}
.ytb-top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
.ytb-team{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;}
.ytb-ey{font-size:.72rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase;color:#7a1fb8;}
.ytb-nm{font-size:1.34rem;font-weight:800;letter-spacing:-.01em;color:#1c1830;line-height:1.1;}
.ytb-pill{display:inline-flex;align-items:center;gap:6px;background:#e7f6ec;color:#0b6b34;border:1px solid #a6dcb8;
  border-radius:99px;padding:4px 11px;font-size:.78rem;font-weight:700;white-space:nowrap;}
.ytb-pill.sess{background:#efe0fc;color:#6b2fae;border-color:#cfa4f0;}
.ytb-sub{color:#4b4560;font-size:.88rem;margin:9px 0 0;}
.ytb-sub b{color:#1c1830;font-weight:700;}
.ytb-foot{display:flex;justify-content:flex-end;margin-top:10px;}
.ytb-demo{border:1.5px dashed #cbcbd6;border-radius:14px;background:#f1f1f5;padding:14px 18px;margin:2px 0 10px;}
.ytb-h{font-size:1.02rem;font-weight:700;color:#1c1830;}
.ytb-s{color:#5f6472;font-size:.88rem;margin-top:4px;}
</style>"""


def team_banner_html(squad: dict, *, is_yours: bool, synced: bool) -> str:
    """A prominent, brand-boxed **Your team** status card for the top of My Squad (US-386/388) — so your team
    stands out on a busy page (was a tester's biggest ask). **Status only** — the real Download/Import controls are
    live Streamlit buttons just below it (US-388: the earlier HTML chips looked clickable but weren't). Two states:
    **your team** (a MADBOOTS-tinted card + the team name + a synced/session pill) and **the demo** (a muted, dashed
    prompt to make it yours). `synced` toggles the pill (signed-in cross-device vs this-session-only)."""
    from src.web_streamlit import brand
    mark = f'<span class="ytb-mark">{brand.mark_html(badge_px=14, font_px=12)}</span>'
    if not is_yours:
        return (_YTB_CSS + '<div class="ytb-demo"><div class="ytb-top"><div>'
                '<div class="ytb-h">👀 You’re viewing the <b>demo squad</b></div>'
                '<div class="ytb-s">Make it yours — <b>import your FPL team</b>, upload a backup, or build one in '
                'Squad Lab (all just below). It’ll then sync to your account across your devices.</div></div>'
                f'{mark}</div></div>')
    # US-423 (density): a compact single-line status card — the pill conveys the sync state; the reassurance
    # paragraph + foot mark are dropped so the pitch sits higher on mobile (the save details live on Help + the
    # ⚙ Backup / import panel below).
    name = html.escape(str(squad.get("name", "My team")))
    pill = ('<span class="ytb-pill">🔄 Synced across your devices</span>' if synced
            else '<span class="ytb-pill sess">💾 This session</span>')
    return (_YTB_CSS + '<div class="ytb-card"><div class="ytb-top">'
            f'<div class="ytb-team"><span class="ytb-ey">🔄 Your team</span><span class="ytb-nm">{name}</span></div>'
            f'{pill}</div></div>')


def _safe_filename(name: str) -> str:
    """A safe download filename stem from a squad name (e.g. `'My Team!'` → `'My-Team'`), so a backup is named
    after the team, not a generic `squad.json` that the browser then de-dupes to `squad-13.json` (US-387).
    Falls back to `'squad'` for an empty/odd name."""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", (name or "").strip()).strip("-.")
    return stem or "squad"


def _download_payload(squad: dict) -> str:
    """`squad` as a downloadable `squad.json` in the SquadStore `{name: {…}}` format — round-trips through
    `parse_uploaded`. Stamps `saved_at`; the squad name is the outer key (ADR-054)."""
    save = {k: v for k, v in squad.items() if k != "name"}
    save.setdefault("saved_at", datetime.date.today().isoformat())
    return json.dumps({squad.get("name", "My squad"): save}, indent=2)


def render_your_team(squad: dict | None, *, is_yours: bool = True) -> None:
    """The **Your team** controls (ADR-113/US-385/388) under the status card — **real, live** buttons (the earlier
    HTML chips looked clickable but weren't; US-388 makes them work). **Backup** is an always-visible
    `st.download_button` (the one people reach for); **import** lives in a labelled panel (Manager-ID · restore from
    a backup · Build in Squad Lab) that **auto-expands when the shown squad isn't yours** (demo/none) so import is
    immediate, and collapses once you have a synced team. `squad` is the squad shown (for the download); import/upload
    set the session's active squad (a rerun reflects it). No server write beyond the account auto-sync in
    `set_active_squad`."""
    # US-423 (density): Backup + Import folded into ONE collapsed panel (was an always-visible Download + a
    # separate expander) so the pitch sits higher on mobile. Auto-expands when the squad isn't yours (import
    # immediate); collapses once you have a synced team.
    with st.expander("⚙ Backup / import your team", expanded=(squad is None or not is_yours)):
        if squad:
            st.download_button("⬇︎ Download a backup", _download_payload(squad),
                               file_name=f"{_safe_filename(squad.get('name', 'squad'))}.json",
                               mime="application/json",
                               help="Save a copy to this device (named after your team) — re-upload it any time.")
        # Get your team — Import by Manager-ID (ADR-058) · restore from a backup (ADR-054) · Build in Squad Lab.
        st.markdown("**Get your team**")
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
                imported, message = fetch_manager_team(int(manager_id.strip()), players)
                if imported:
                    set_active_squad(imported)
                    st.success(message)
                else:
                    st.info(message)

        uploaded = st.file_uploader("…or restore your team from a backup file", type="json", key="squad_uploader",
                                    help="Upload a squad.json you downloaded earlier (a backup, or from Squad Lab).")
        if uploaded is not None and st.session_state.get(_UPLOAD_APPLIED) != uploaded.file_id:
            parsed, err = parse_uploaded(uploaded)
            if err:
                st.error(err)
            else:
                set_active_squad(parsed)
                st.session_state[_UPLOAD_APPLIED] = uploaded.file_id
                st.success(f"Loaded **{parsed['name']}** ({len(parsed['player_ids'])} players).")

        st.caption("🧪 …or **build a fresh squad** in the **Squad Lab** tab (sidebar) — *Use this squad →* "
                   "sends it here.")


def render_cloud_sync() -> None:
    """The ☁ cross-device **Save / Load** (US-310/331, ADR-094) — the **no-login fallback** only.

    **Retired in signed-in mode (ADR-113/US-384).** When Google auth is configured, the **account is the store**:
    your team auto-syncs to your account (`user_key`, ADR-106), so a hand-typed handle is redundant — and its
    divergent write (saving under the *handle*, while a refresh restores the *account*) was the **refresh-revert
    bug** the tester hit. So this renders **only when auth is *not* configured** (local/dev/open deploy), where it
    stays the sole cross-device option. Also **secret-gated** on the store (else download/upload-only, ADR-054)."""
    from src.web_streamlit import analytics, auth, cloud_store
    if auth.is_configured():          # ADR-113: signed-in → the account is the store; retire the handle tool
        return
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
                with analytics.timed("squad_save", page="Squads"):   # perf (US-336)
                    cloud_store.save_squad(clean, squad)
                st.session_state[_CLOUD_LINKED] = clean        # link → auto-sync future edits (US-357/C1)
                analytics.track("squad_saved")                 # usage only — NO handle/contents (anonymity, US-335)
                if taken:
                    st.warning(f"Updated **{clean}** — overwrote the squad already saved under that handle. "
                               "(Handles aren't private — pick one only you'd guess.)")
                else:
                    st.success(f"Saved as **{clean}** — load it on any device with that handle.")
            except Exception as exc:   # surface the real store error (e.g. an RLS policy), not a blind note
                analytics.track("error", component="squad_save")
                st.error(f"Save failed — **{cloud_store.store_error(exc)}**. Your download still works.")
        if c_load.button("Load", disabled=not clean, key="cloud_load"):
            try:
                with analytics.timed("squad_load", page="Squads"):   # perf (US-336)
                    loaded = cloud_store.load_squad(clean)
            except Exception as exc:
                loaded = None
                analytics.track("error", component="squad_load")
                st.error(f"Load failed — **{cloud_store.store_error(exc)}**.")
            if loaded:
                st.session_state[_CLOUD_LINKED] = clean        # link first, so autosync targets this handle
                set_active_squad(loaded)
                analytics.track("squad_loaded")                # usage only — NO handle/contents (anonymity, US-335)
                st.success(f"Loaded **{clean}** — edits now auto-sync across devices.")
                st.rerun()
            elif clean:
                st.info(f"No squad saved under **{clean}** yet — Save one first.")
        if c_clear.button("Clear", disabled=not clean, key="cloud_clear"):
            try:
                cloud_store.delete_squad(clean)
                if st.session_state.get(_CLOUD_LINKED) == clean:
                    st.session_state.pop(_CLOUD_LINKED, None)   # unlink — stop syncing to a cleared handle
                st.success(f"Cleared **{clean}**.")
            except Exception as exc:
                st.error(f"Clear failed — **{cloud_store.store_error(exc)}**.")
        if linked := st.session_state.get(_CLOUD_LINKED):
            st.caption(f"🔄 **Auto-syncing** your edits (captain, transfers, bench…) to **{linked}** across devices.")
        if handle and not clean:
            st.caption("A handle is 2–32 letters, numbers, - or _.")
        if not squad:
            st.caption("Build or load a squad first to **Save** it — **Load** works any time.")
        st.caption("Stored: your handle + squad (public FPL players), **no login**. Anyone who knows the "
                   "handle can read or overwrite it — use one only you'd guess. **Clear** removes it.")
