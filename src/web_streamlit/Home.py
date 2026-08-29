"""The Streamlit UI home (ADR-052) — a read-only view over the analytics.

Multipage: this is the landing (the sidebar's **Home** — its label is this file's name); `pages/` holds
My Squad · FDR · Signals · Team DNA · Players · Trending · Help · Feedback · Admin. ADR-166 folded
Squad Lab and Leagues into My Squad, and Maddie Explains into Help ▸ Watch; ADR-168 retired Ask to Admin —
**eight**, and ADR-169 split FDR from Team DNA and reordered the lot by how often each is
actually needed.
Each page imports the same engine the CLI does and changes nothing in `src/`.
Run:  python -m src.web_streamlit

⚠️ **The tour below names every page, so it goes stale on any rename or addition** (US-433: it still said
*Fixtures* and *News* long after ADR-134 and ADR-149 renamed them, and never mentioned 🏆 Leagues at all).
Its twin is the public `madboots.com` grid — `docs/08_Marketing/Homepage_Copy.md`. **Change both together**;
they drifted apart because nothing tied them.
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
        st.page_link("pages/1_My_Squad.py",
                     label="⚙️ Before it locks — set your captain · make transfers · pick a chip →")

# US-398 (rev, owner 2026-08-17): ONE highlighted "get started" box — a purple CTA button (links to Squad Lab via
# its page slug, same tab) with the New-here / Maddie / Testing nudges consolidated (were three separate callouts).
_HERO_CSS = (
    "<style>.mb-hero{border:1px solid #cfa4f0;border-radius:12px;"
    "background:linear-gradient(135deg,#f3e9fd,#efe0fc);padding:16px 18px;margin:2px 0 16px;}"
    ".mb-hero .cta{display:inline-block;background:#8B2FC9;color:#fff !important;font-weight:800;border-radius:9px;"
    "padding:10px 18px;text-decoration:none;font-size:1rem;}"
    ".mb-hero .cta:hover{background:#7a1fb8;}"
    ".mb-hero .nudges{color:#2a2140;font-size:.9rem;line-height:1.7;margin-top:12px;}"
    ".mb-hero a.ext{color:#7a1fb8;font-weight:700;}</style>")
st.markdown(
    _HERO_CSS + '<div class="mb-hero">'
    '<a class="cta" href="My_Squad" target="_self">🧪 Build your first squad → My Squad ▸ Lab</a>'
    '<div class="nudges">'
    '🧭 <b>New here?</b> The <b>Help</b> tab is a step-by-step guide.&nbsp;&nbsp;'
    '🎥 <b>Help ▸ Watch</b> has quick video guides — 90 seconds or less.<br>'
    '🧪 <b>Testing this?</b> Tell us what breaks on the <b>Feedback</b> tab — or '
    '<a class="ext" href="https://github.com/madbootsfpl/fpl-assistant/issues/new">open a GitHub issue</a>.'
    '</div></div>', unsafe_allow_html=True)

st.markdown(
    """
**Explore the sidebar:**

- 👟 **Players** — browse, filter and sort the full player pool and stats; view player cards and **compare** two.
- 📅 **FDR** — every club's next few gameweeks, shaded by difficulty; easiest run first.
- 🧬 **Team DNA** — how strong every club is at both ends, and the players to target there.
- 🧩 **My Squad** — your XI, transfers, captain and chips, with **AI Tips**, your squad's **DNA**, your
  🏆 **Leagues** (effective ownership · captain split · transfer flow · head-to-head), and the **Lab** for
  building a fresh 15 (season start · wildcard · revamp).
- 📡 **Signals** — everything the table doesn't say, most reliable first: official FPL news, unexplained
  sell-offs, and reported moves out of the league.
- 📈 **Trending** — what the crowd is *doing*, in numbers: most-owned · transferred in/out · in-form.
- 🧭 **Help** — a step-by-step guide to getting started, the **FPL rules** MADBOOTS checks against, plus
  **Maddie's** 90-second video explainers.
- 📣 **Feedback** — tell us what broke, or what would help.

**Your squad**

- 🧪 **Build** it in **My Squad ▸ Lab** — name it, then **Use this squad →**.
- ☁ **Saved to your account** and **auto-synced across your devices** — or **Download** a backup to your device.
- 📤 **Upload** a saved backup, or **import your real FPL team** by Manager-ID — the same id then opens your
  mini-leagues on **Leagues**, so you only enter it once.
- 🧩 **Manage** transfers · captaincy · chips · analysis in **My Squad**.
- 👀 A **demo** squad populates the views on first visit.
"""
)

_signup = secret("FPL_SIGNUP_URL")          # a founding-tester signup link, only when configured (ADR-087)
if _signup:
    st.link_button("✋ Join the beta (founding testers)", _signup,
                   help="Sign up with your email — founding testers get free access as the app grows.")

st.divider()
st.caption(brand.DISCLAIMER)                 # US-350 (ADR-103): the not-affiliated line
