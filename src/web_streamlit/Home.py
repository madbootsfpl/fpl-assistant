"""The Streamlit UI home (ADR-052) — a read-only view over the analytics.

Multipage: this is the landing (the sidebar's **Home** — its label is this file's name); `pages/` holds
Players · Fixtures · My Squad · Squad Lab · Ask · News · Trending · Help · Feedback (ADR-105). Each page
imports the same engine the CLI does and changes nothing in `src/`. Run:  python -m src.web_streamlit
"""

from datetime import datetime, timezone

import streamlit as st

from src.storage import Storage
from src.ui.deadline import deadline_line
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access, secret
from src.web_streamlit.countdown import render_countdown
from src.web_streamlit.status import render_data_status

st.set_page_config(**brand.page_config())
require_access()          # opt-in beta gate (ADR-087) — a no-op unless FPL_ACCESS_CODE is set
analytics.boot("Home")    # anonymous usage analytics (ADR-100) — a no-op unless FPL_ANALYTICS is set
render_data_status()
# US-349: the badge + the two-tone MADBOOTS wordmark (ADR-103), replacing the old ⚽-emoji title.
_logo, _name = st.columns([1, 7], vertical_alignment="center")
_logo.image(brand.badge_path(), width=78)
_name.markdown(brand.wordmark_html(42), unsafe_allow_html=True)
st.caption(f"**{brand.TAGLINE}** The analytics decide; you stay in control.")

# The next FPL deadline — a countdown that escalates in urgency (ADR-086/US-267), rolling forward each GW.
_store = Storage()
try:
    _line = deadline_line(_store.get_upcoming_fixtures(), datetime.now(timezone.utc))
finally:
    _store.close()
if _line:
    _gw, _deadline, _text, _urgency = _line
    render_countdown(_gw, _deadline, datetime.now(timezone.utc), _urgency)   # the live clock (ADR-088)
    st.caption(_text)          # the accessible, no-JS text line (context + date) beneath the clock
    if _urgency != "calm":     # a nudge to the pre-deadline actions when it's close
        st.page_link("pages/3_My_Squad.py",
                     label="⚙️ Before it locks — set your captain · make transfers · pick a chip →")
st.markdown(
    """
**Explore the sidebar:**

- **Players** — browse, filter and sort the full player pool and stats; view player cards and **compare** two.
- **Fixtures** — upcoming fixtures and difficulty (1–8 GWs), for all teams or just your squad.
- **My Squad** — manage your XI, transfers, captain and chips, with **AI Tips** and **Health** analysis.
- **Squad Lab** — 🧪 build and optimise a fresh 15 (season start · wildcard · revamp); **Use this squad →** sends
  it to My Squad.
- **Ask** — ask a question in plain English — a grounded chat; every answer is checked against the data.
- **News** — official FPL player news (injuries · doubts · returns), most serious first.
- **Trending** — what the crowd's doing (most-owned · transferred in/out · in-form) + **Community Signals**.
- **Help** — a step-by-step guide to getting started with MADBOOTS.

**Your squad**

- **Build** it in **🧪 Squad Lab** — name it, then **Use this squad →**.
- **Saved to your account** and **auto-synced across your devices** — or **Download** a `squad.json` backup.
- **Upload** a saved squad, or **import your real FPL team** by Manager-ID (from GW1).
- **Manage** transfers · captaincy · chips · analysis in **My Squad**.
- A **demo** squad populates the views on first visit.
"""
)
st.info("🧭 **New here?** The **Help** tab (bottom of the sidebar) is a step-by-step guide to building "
        "your team with the assistant.")
st.info("🧪 **Testing this?** Tell us what breaks or feels off on the **📣 Feedback** tab (bottom of the "
        "sidebar) — or [open a GitHub issue](https://github.com/madbootsfpl/fpl-assistant/issues/new).")

_signup = secret("FPL_SIGNUP_URL")          # a founding-tester signup link, only when configured (ADR-087)
if _signup:
    st.link_button("✋ Join the beta (founding testers)", _signup,
                   help="Sign up with your email — founding testers get free access as the app grows.")

st.divider()
st.caption(brand.DISCLAIMER)                 # US-350 (ADR-103): the not-affiliated line
