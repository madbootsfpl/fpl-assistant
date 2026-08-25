"""SPIKE — put the actions ON the shirt, so the page below it can shrink (ADR-108/133 follow-on).

**The goal is less page, not more interaction.** Today a single selected player is served by six or seven
separate widgets stacked below the pitch: a picker, a Boot Battle pool, a club selector, a compare-with picker,
a captain button, a substitute picker and its confirm. Every one of them is vertical space on a phone, and
tester feedback on My Squad has twice been about density (US-423).

If a shirt carries its own actions, most of that chain stops needing to exist on the page at all.

The question this answers is narrow and mechanical: **can one tap distinguish *which action* on *which
player*?** If yes, the design work is real; if no, the idea dies here.

Run:  ./venv/bin/python -m streamlit run spikes/188-actions-on-the-shirt/spike_app.py
"""

import streamlit as st
from st_click_detector import click_detector

st.set_page_config(page_title="Spike — actions on the shirt", layout="wide")
st.title("🥾 Spike — actions on the shirt")

CSS = """
<style>
.pitch{background:linear-gradient(180deg,#1b7a3e,#12602f);border-radius:14px;padding:18px;display:flex;
gap:14px;flex-wrap:wrap;justify-content:center;}
.kit{background:#f7fafc;border-radius:10px;width:104px;padding:8px 6px;text-align:center;
box-shadow:0 6px 14px -8px rgba(0,0,0,.6);}
.kit-hit{display:block;text-decoration:none;color:#0c121a;}
.kit-hit .nm{font-weight:800;font-size:.78rem;} .kit-hit .xp{font-weight:800;color:#0a7d45;font-size:.9rem;}
.kit-hit .mt{font-size:.66rem;color:#5a6472;}
.acts{display:flex;gap:4px;justify-content:center;margin-top:6px;border-top:1px solid #e3e8ee;padding-top:6px;}
.acts a{text-decoration:none;font-size:.82rem;line-height:1;padding:3px 6px;border-radius:6px;
background:#eef2f6;color:#243040;}
.acts a:hover{background:#d7e3f0;}
</style>
"""

SQUAD = [(1, "Raya", "GK", 4.1), (2, "Gabriel", "DEF", 5.2), (3, "Virgil", "DEF", 4.6),
         (4, "Saka", "MID", 6.8), (5, "Ødegaard", "MID", 5.4), (6, "Haaland", "FWD", 7.9)]


def card(pid, name, pos, xp):
    """A kit card whose actions are **siblings** of the select-anchor, never children.

    HTML forbids `<a>` inside `<a>` — a browser silently closes the outer one — so the whole card cannot be one
    anchor if the actions are to be individually clickable. That constraint is the only structural change the
    real build needs.
    """
    return (f'<div class="kit">'
            f'<a href="#" id="sel:{pid}" class="kit-hit">'
            f'<div class="nm">{name}</div><div class="xp">{xp}</div><div class="mt">{pos}</div></a>'
            f'<div class="acts">'
            f'<a href="#" id="cap:{pid}" title="Make captain">©</a>'
            f'<a href="#" id="sub:{pid}" title="Substitute">🔁</a>'
            f'<a href="#" id="cmp:{pid}" title="Compare">⚔️</a>'
            f'</div></div>')


html = CSS + '<div class="pitch">' + "".join(card(*p) for p in SQUAD) + "</div>"

st.caption("Tap a **name** to select, or one of the three actions under it. The id that comes back carries "
           "**both** the action and the player.")
clicked = click_detector(html, key="shirt_actions")

st.subheader(f"returned → `{clicked or '(nothing yet)'}`")
if clicked and ":" in clicked:
    action, pid = clicked.split(":", 1)
    who = next((n for i, n, *_ in SQUAD if str(i) == pid), "?")
    label = {"sel": "Select — open the card", "cap": "Make captain",
             "sub": "Substitute", "cmp": "⚔️ Boot Battle — compare"}.get(action, action)
    st.success(f"✅ **{label}** → **{who}** (id `{pid}`)")
    st.caption("One tap resolved both *which action* and *which player* — so the widgets that currently do "
               "this below the pitch would not need to be on the page.")
