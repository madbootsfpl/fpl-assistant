"""Admin — beta analytics (ADR-100, US-337).

A **gated** owner view over the anonymous `events` table: sessions, returning devices, most-used pages/features,
success rates, and median/P95 performance. Gated by **`FPL_ADMIN_KEY`** (an owner password) — **inert when unset**
(the public deploy shows a "not configured" note; testers can't see the numbers). Reads via `analytics` (the first
analytics read — needs an anon SELECT policy, docs/ANALYTICS.md); best-effort, so a store hiccup shows a note, not
a crash. The heavy lifting is `analytics.summarise` (pure); this page just renders.
"""

import streamlit as st

from src.web_streamlit import analytics, auth, brand, cloud_store, roster, user_store
from src.web_streamlit.access import require_access, secret

st.set_page_config(**brand.page_config("Admin"))
require_access()          # testers still pass the beta gate first (ADR-087)
analytics.boot("Admin")
st.title("📊 Admin — beta analytics")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)

_KEY = secret("FPL_ADMIN_KEY")
if not _KEY:
    st.info("Admin analytics isn't configured. Set **`FPL_ADMIN_KEY`** (and `FPL_ANALYTICS`) + add the anon "
            "SELECT policy — see **docs/ANALYTICS.md**.")
    st.stop()

_OK = "_admin_ok"
if not st.session_state.get(_OK):
    st.caption("Owner only — enter the admin key.")
    entered = st.text_input("Admin key", type="password", key="_admin_key")
    if entered and entered == _KEY:
        st.session_state[_OK] = True
        st.rerun()
    elif entered:
        st.error("That admin key isn't right.")
    st.stop()

# --- unlocked -----------------------------------------------------------------------
if not analytics.is_enabled():
    st.warning("Analytics is currently **off** (`FPL_ANALYTICS` unset) — no new events are being collected.")

rows = analytics.recent_events()
if rows is None:
    st.error("Couldn't read the events store. Check the store secrets + the **anon SELECT policy** on `events` "
             "(docs/ANALYTICS.md).")
    st.stop()

s = analytics.summarise(rows)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Events", s["events"])
c2.metric("Sessions", s["sessions"])
c3.metric("Devices", s["devices"])
c4.metric("Returning", s["returning"])
span = f" · {s['since'][:10]} → {s['until'][:10]}" if s.get("since") else ""
pct = f" · {s['success_pct']}% ok" if s.get("success_pct") is not None else ""
st.caption(f"Last {len(rows)} events{span}{pct}. Anonymous — no personal data (ADR-100).")

if not rows:
    st.info("No events yet. Once `FPL_ANALYTICS=1` and testers use the app, they'll appear here.")
    st.stop()

# --- Load & concurrency (ADR-120) ------------------------------------------------------
# Registered testers is cheap; the real limit is how many are active *at once* on one small container. The
# failure mode is sluggishness, not a crash — most likely at a deadline spike.
_load = analytics.load_summary(rows)
_icon = {"green": "🟢", "amber": "🟡", "red": "🔴"}[_load["health"]]
st.subheader(f"{_icon} Load & concurrency")
l1, l2, l3 = st.columns(3)
l1.metric("Active now", _load["active_now"], help=f"Distinct sessions with an event in the last "
                                                  f"{_load['window_min']} minutes.")
l2.metric("Peak concurrent", _load["peak_concurrent"], help="The busiest such window in this data — the number "
                                                            "to watch at a deadline.")
l3.metric("P95 latency", f"{_load['p95_ms']} ms" if _load["p95_ms"] else "—",
          help="Slowest 5% of analysis / data-load timings. Climbing P95 alongside concurrency means the "
               "container is stretched.")
st.caption("Both counts are **proxies** — an event is a click, not a held connection, so an idle open tab is "
           "invisible. Directional: watch the trend beside P95. Thresholds are uncalibrated heuristics "
           "(ADR-120) — tune them against real load.")

# --- Tester activity (ADR-120) ---------------------------------------------------------
# The analytics above are anonymous by design and cannot name anyone. This is a *separate* join over the
# owner's own allow-list — never a de-anonymisation of an event.
st.subheader("👥 Tester activity")
_emails = user_store.all_emails()
if not _emails:
    st.caption("No allow-list to read (store unconfigured, or `beta_users` is empty).")
else:
    # ADR-142 — TWO signals, kept apart. "Signed in" is *used the app*; "saved a squad" is a much rarer,
    # much stronger act. The panel used to judge activity on the save alone, which reported 18 of 25 testers
    # as ⚪ never while at least two were using it daily.
    _keys = {e: auth.user_key(e) for e in _emails}
    _saved = cloud_store.updated_at_by_handle(_keys.values())
    _seen = user_store.last_seen_by_email(_emails)
    _rows = roster.build(_emails, _saved, key_for=_keys.get, seen_by_email=_seen)
    _t = roster.totals(_rows)
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Registered", _t["registered"])
    r2.metric("🟢 Active", _t["active"], help="Signed in within the last 7 days.")
    r3.metric("🟡 Dormant", _t["dormant"], help="Last signed in 7–30 days ago.")
    r4.metric("⚪ Never", _t["never"], help="On the allow-list but has never signed in.")
    _badge = {"active": "🟢 active", "dormant": "🟡 dormant", "lapsed": "🔴 lapsed", "never": "⚪ never"}
    st.dataframe([{"Tester": r["email"], "Status": _badge[r["status"]],
                   "Last used": r["last_seen"][:10] if r["last_seen"] else "—",
                   "Last saved a squad": r["last_saved"][:10] if r["last_saved"] else "—",
                   "Days ago": r["days"] if r["days"] is not None else "—"} for r in _rows],
                 hide_index=True, use_container_width=True)
    if not _seen:
        # Say it plainly rather than showing a column of dashes and letting it read as "nobody has been here".
        st.warning("**Sign-in times aren't being recorded yet**, so status below falls back to *when a squad "
                   "was last saved* — which most testers never do, and is why this panel under-reported "
                   "activity. Add the column once and it starts working:  "
                   "`alter table beta_users add column if not exists last_seen timestamptz;`")
    st.caption("**Last used** = signed in. **Last saved a squad** = pressed save, which is rarer and a "
               "stronger signal — someone actively managing a team rather than visiting. A tester browsing "
               "**signed-out** appears in neither. Read it beside the anonymous totals above; those stay "
               "anonymous and are never joined to this (ADR-100).")

left, right = st.columns(2)
with left:
    st.subheader("Most-viewed pages")
    st.dataframe(s["top_pages"] or [{"page": "—", "views": 0}], hide_index=True, use_container_width=True)
with right:
    st.subheader("Events")
    st.dataframe(s["event_counts"], hide_index=True, use_container_width=True)

st.subheader("Performance — median / P95 (ms)")
if s["perf"]:
    st.dataframe(s["perf"], hide_index=True, use_container_width=True)
else:
    st.caption("No `perf` events yet (data-load / analysis / save / load timings appear here).")
