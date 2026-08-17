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
st.caption(f"**{brand.TAGLINE}** {brand.MANTRA}")

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

# US-398: one clear primary action up top (the value path), above the "explore" list — not buried in bullets.
st.page_link("pages/4_Squad_Lab.py", label="🧪 **Build your first squad** → Squad Lab")

st.markdown(
    """
**Explore the sidebar:**

- 👟 **Players** — browse, filter and sort the full player pool and stats; view player cards and **compare** two.
- 📅 **Fixtures** — upcoming fixtures and difficulty (1–8 GWs), for all teams or just your squad.
- 🧩 **My Squad** — manage your XI, transfers, captain and chips, with **AI Tips** and **Health** analysis.
- 🧪 **Squad Lab** — build and optimise a fresh 15 (season start · wildcard · revamp); **Use this squad →** sends
  it to My Squad.
- 💬 **Ask** — ask a question in plain English — a grounded chat; every answer is checked against the data.
- 📰 **News** — official FPL player news (injuries · doubts · returns), most serious first.
- 📈 **Trending** — what the crowd's doing (most-owned · transferred in/out · in-form) + **Community Signals**.
- 🧭 **Help** — a step-by-step guide to getting started with MADBOOTS.
- 🎥 **Maddie Explains** — quick 60-second video guides, from **Maddie**, your MADBOOTS guide.

**Your squad**

- 🧪 **Build** it in **Squad Lab** — name it, then **Use this squad →**.
- ☁ **Saved to your account** and **auto-synced across your devices** — or **Download** a backup to your device.
- 📤 **Upload** a saved backup, or **import your real FPL team** by Manager-ID (from GW1).
- 🧩 **Manage** transfers · captaincy · chips · analysis in **My Squad**.
- A **demo** squad populates the views on first visit.
"""
)
# Brand-purple callouts (US-389) — replacing Streamlit's default-blue st.info so the nudges read as MADBOOTS.
_NOTE_CSS = ("<style>.mb-note{display:flex;gap:10px;align-items:flex-start;border:1px solid #cfa4f0;"
             "border-radius:10px;background:linear-gradient(135deg,#f3e9fd,#efe0fc);color:#2a2140;"
             "padding:11px 14px;margin:0 0 10px;font-size:.92rem;line-height:1.5;}"
             ".mb-note .i{font-size:1.05rem;}.mb-note a{color:#7a1fb8;font-weight:700;}</style>")
st.markdown(_NOTE_CSS + '<div class="mb-note"><span class="i">🧭</span><span><b>New here?</b> The <b>Help</b> tab '
            "(bottom of the sidebar) is a step-by-step guide to building your team with the assistant.</span></div>",
            unsafe_allow_html=True)
st.page_link("pages/9_Maddie_Explains.py",
             label="🎥 **Maddie Explains** — quick 60-second video guides of each feature →")

_signup = secret("FPL_SIGNUP_URL")          # a founding-tester signup link, only when configured (ADR-087)
if _signup:
    st.link_button("✋ Join the beta (founding testers)", _signup,
                   help="Sign up with your email — founding testers get free access as the app grows.")

st.divider()
# US-398: the beta/Testing nudge moved to a lighter footer (was a mid-page callout → banner-blindness).
st.caption("🧪 **Testing this?** Tell us what breaks or feels off on the **📣 Feedback** tab — or "
           "[open a GitHub issue](https://github.com/madbootsfpl/fpl-assistant/issues/new).")
st.caption(brand.DISCLAIMER)                 # US-350 (ADR-103): the not-affiliated line
