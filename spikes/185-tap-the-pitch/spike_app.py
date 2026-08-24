"""SPIKE (ADR-108 follow-on): can you tap a shirt on the real pitch and get the player id back?

Not production code. It answers four questions the ADR could only guess at:

  1. Does a pre-built PyPI component avoid the front-end build toolchain?   (no npm here — see findings.md)
  2. Does the real ADR-084 pitch — CSS, hover cards and all — survive inside the component's iframe?
  3. Does the iframe auto-size, or does it clip the pitch? (ADR-084 rejected components.v1.html over this.)
  4. Does it work on Streamlit Community Cloud?                             (owner's step — see findings.md)

Run:  ./venv/bin/python -m streamlit run spikes/185-tap-the-pitch/spike_app.py
"""

import re

import streamlit as st
from st_click_detector import click_detector

from src.analytics import decision_xp, team_schedule
from src.squads import SquadStore
from src.storage import Storage
from src.web_streamlit.badges import photo_url_by_id, shirt_url_by_id
from src.web_streamlit.pitch import render_pitch

st.set_page_config(page_title="Spike — tap the pitch", layout="wide")
st.title("🥾 Spike — tap the pitch")

store = Storage()
players, upcoming, teams = store.get_players(), store.get_upcoming_fixtures(), store.get_teams()
history, gw_history = store.get_history_by_code(), store.get_gw_history_by_code()
store.close()

squad = SquadStore().load("RoboTS")
by_id = {p["id"]: p for p in players}
owned = [by_id[i] for i in squad["player_ids"] if i in by_id]
bench_ids = set(squad.get("bench_ids") or [])
xi = [p for p in owned if p["id"] not in bench_ids]
bench = [p for p in owned if p["id"] in bench_ids]

ranked = decision_xp(players, upcoming, history, horizon=1, gw_history_by_code=gw_history)
xp_by_id = {r["id"]: r["xp"] for r in ranked}
next_opp = {t: (team_schedule(upcoming, t) or [None])[0] for t in {p["team"] for p in owned}}

# FINDING: `render_pitch` writes straight to `st.markdown` and returns nothing, so there is no HTML to hand
# to a component. The real build needs a `pitch_html()` split out of it (build → render). Captured here.
_captured = []
_real_markdown = st.markdown
st.markdown = lambda body, **kw: _captured.append(body)
render_pitch(xi, bench, captain_id=squad.get("captain_id"), xp_by_id=xp_by_id,
             photos=photo_url_by_id(players, teams), next_opp=next_opp,
             team_names={t["short_name"]: t["name"] for t in teams},
             kits=shirt_url_by_id(players, teams))
st.markdown = _real_markdown
html = "".join(_captured)

# The real build would emit this anchor from `_kit_html`; a regex is enough to answer "does it work?".
# Every kit card becomes <a id="{player id}"> wrapping the existing markup — nothing else changes.
ids = [p["id"] for p in xi] + [p["id"] for p in bench]
_seen = iter(ids)
clickable = re.sub(r'<div class="kit">',
                   lambda _m: f'<a href="#" id="{next(_seen)}" class="kit-a"><div class="kit">', html)
clickable = clickable.replace("</div></div></div>", "</div></div></div></a>")
clickable = clickable.replace("<style>", "<style>.kit-a{text-decoration:none;color:inherit;display:block;}")

st.caption("Tap any shirt. If the id appears below, the round-trip works.")
clicked = click_detector(clickable, key="pitch")
st.subheader(f"clicked → {clicked or '(nothing yet)'}")
if clicked and clicked.isdigit() and int(clicked) in by_id:
    p = by_id[int(clicked)]
    st.success(f"✅ {p['web_name']} ({p['team']}, {p['position']}) — £{p['price']}m · xP {xp_by_id.get(p['id'])}")
