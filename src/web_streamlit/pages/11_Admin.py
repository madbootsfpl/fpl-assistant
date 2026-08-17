"""Admin — beta analytics (ADR-100, US-337).

A **gated** owner view over the anonymous `events` table: sessions, returning devices, most-used pages/features,
success rates, and median/P95 performance. Gated by **`FPL_ADMIN_KEY`** (an owner password) — **inert when unset**
(the public deploy shows a "not configured" note; testers can't see the numbers). Reads via `analytics` (the first
analytics read — needs an anon SELECT policy, docs/ANALYTICS.md); best-effort, so a store hiccup shows a note, not
a crash. The heavy lifting is `analytics.summarise` (pure); this page just renders.
"""

import streamlit as st

from src.web_streamlit import analytics, brand
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
