"""The AI Insights card — grounded, plain-English observations under the radar (Sprint 170, US-415, ADR-118).

Renders `analytics.player_insights` as a self-contained dark card: a bulleted list, each with a kind icon
(✓ strength · ⚡ set-piece · ℹ info · ⚠ caution). Display-only; reuses the `PlayerDNA` the Card view already
computed — no new store read, no `decision_xp` change.
"""

import streamlit as st

# kind → (icon, tint background, icon colour) — on-dark, matching the DNA/verdict cards.
_KIND = {
    "good": ("✓", "rgba(1,252,122,.16)", "#01fc7a"),
    "sp":   ("⚡", "rgba(139,47,201,.22)", "#c9a2f0"),
    "info": ("ℹ", "rgba(94,234,212,.16)", "#5eead4"),
    "warn": ("!", "rgba(255,176,32,.16)", "#ffb020"),
}

INS_CSS = """
<style>
.ins-card{background:linear-gradient(180deg,#111821,#0c121a);border:1px solid rgba(255,255,255,.09);
border-radius:18px;color:#f2f6fb;margin:.5rem 0;padding:15px 18px 16px;
box-shadow:0 18px 40px -22px rgba(0,0,0,.7);
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.ins-card .ins-ttl{font-weight:800;font-size:.72rem;letter-spacing:.08em;color:#aab6c6;
text-transform:uppercase;margin-bottom:10px;}
.ins-card .ins-row{display:flex;gap:10px;align-items:flex-start;font-size:.86rem;line-height:1.4;
color:#dbe3ee;margin:8px 0;}
.ins-card .ins-ic{flex:none;width:22px;height:22px;border-radius:6px;display:flex;align-items:center;
justify-content:center;font-size:.72rem;font-weight:800;}
</style>
"""


def _esc(s) -> str:
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def insights_card_html(insights) -> str:
    """The full AI Insights card: a titled list of grounded bullets (icon + text)."""
    rows = ""
    for i in insights:
        icon, bg, fg = _KIND.get(i.kind, _KIND["info"])
        rows += (f'<div class="ins-row"><span class="ins-ic" style="background:{bg};color:{fg}">{icon}</span>'
                 f'<span>{_esc(i.text)}</span></div>')
    return (INS_CSS + '<div class="ins-card"><div class="ins-ttl">✦ AI Insights</div>'
            f'{rows}</div>')


def render_insights_card(insights) -> None:
    """Render a list of `Insight`s as the card (no-op if the list is empty)."""
    if not insights:
        return
    st.markdown(insights_card_html(insights), unsafe_allow_html=True)
