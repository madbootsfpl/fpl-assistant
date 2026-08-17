"""A web-native **Captain Pick** card for the Streamlit edge (Sprint 116, US-294; the pitch pattern, ADR-084).

Renders the same grounded decision as the mono `render_captain_picks` block (ADR-089) — the 🥇 pick (Team · Pos
· a Projected-xP chip) · a Confidence·Band pill · Edge (✓) / Risk (⚠) · Alternatives (🥈/🥉 + xP) — as **one
self-contained HTML/CSS block** (no JS) via `st.markdown(unsafe_allow_html=True)`. Neutral, theme-aware colours
(text inherits the Streamlit theme; the chips carry their own); every value is `html.escape`d. Pure presentation
over data the page already holds — display-only; never touches xP.
"""

import html

import streamlit as st

from src.web_streamlit import brand

# Scoped to `.cap-card`; rgba-grey neutrals read on both themes, chips carry explicit colours. Lines unindented
# so `st.markdown` doesn't treat the CSS as a code block.
_CARD_CSS = """
<style>
.cap-card{border:1px solid rgba(128,128,128,.35);border-radius:14px;padding:14px 16px;margin:.4rem 0;
background:rgba(128,128,128,.06);}
.cap-card .cc-head{font-weight:800;font-size:1.02rem;margin-bottom:.5rem;}
.cap-card .cc-scope{font-weight:500;opacity:.7;font-size:.85rem;margin-left:.4rem;}
.cap-card .cc-pick{display:flex;align-items:center;flex-wrap:wrap;gap:.45rem .7rem;margin-bottom:.55rem;}
.cap-card .cc-name{font-size:1.25rem;font-weight:800;}
.cap-card .cc-team{opacity:.75;}
.cap-card .cc-proj{background:#1f6feb;color:#fff;border-radius:999px;padding:.12rem .6rem;font-weight:700;
font-size:.85rem;}
.cap-card .cc-conf{border-radius:999px;padding:.12rem .6rem;font-weight:700;font-size:.85rem;}
.cap-card .cc-cols{display:flex;flex-wrap:wrap;gap:1.2rem;margin:.1rem 0 .5rem;}
.cap-card .cc-col{flex:1 1 220px;}
.cap-card .cc-h{text-transform:uppercase;letter-spacing:.04em;font-size:.72rem;opacity:.65;margin-bottom:.15rem;}
.cap-card ul{margin:0;padding-left:1.15rem;}
.cap-card li{margin:.12rem 0;}
.cap-card .cc-alts{opacity:.92;font-size:.92rem;border-top:1px solid rgba(128,128,128,.25);padding-top:.5rem;}
.cap-card .cc-brand{margin-top:.55rem;padding-top:.5rem;border-top:1px solid rgba(128,128,128,.25);
display:flex;align-items:center;justify-content:space-between;}
.cap-card .cc-brand .cc-t{text-transform:uppercase;letter-spacing:.08em;font-size:.68rem;opacity:.55;}
</style>
"""

_MEDALS = ("🥇", "🥈", "🥉")
# Confidence bands → the shared semantic tokens (ADR-114): a (tint, fg) pair so the chip is always legible.
_BAND_STYLE = {"High": (brand.GOOD_TINT, brand.GOOD_FG),
               "Medium": (brand.WARN_TINT, brand.WARN_FG),
               "Low": (brand.BAD_TINT, brand.BAD_FG)}


def captain_card_html(ranked, explanation, *, scope: str = "", team_names=None) -> str:
    """The Captain Pick card as an HTML string (pure — no Streamlit; testable). `ranked` is the `captain_picks`
    list sliced so `[0]` is the chosen pick; `team_names` maps a team short code → a friendly name. Empty-safe."""
    if not ranked:
        return ""
    e = html.escape
    top = ranked[0]
    team = (team_names or {}).get(top.get("team"), top.get("team") or "")
    scope_html = f'<span class="cc-scope">{e(scope)}</span>' if scope else ""

    proj = f'<span class="cc-proj">{top["xp"]:.1f} pts</span>' if top.get("xp") is not None else ""
    conf_html = ""
    why_html = risk_html = ""
    if explanation is not None:
        _bg, _fg = _BAND_STYLE.get(explanation.band, _BAND_STYLE["Low"])
        conf_html = (f'<span class="cc-conf" style="background:{_bg};color:{_fg}">'
                     f'{explanation.confidence}/100 · {e(explanation.band)}</span>')
        if explanation.reasons:
            lis = "".join(f"<li>✓ {e(r)}</li>" for r in explanation.reasons)
            why_html = f'<div class="cc-col"><div class="cc-h">Edge</div><ul>{lis}</ul></div>'
        if explanation.risks:
            lis = "".join(f"<li>⚠ {e(r)}</li>" for r in explanation.risks)
            risk_html = f'<div class="cc-col"><div class="cc-h">Risk</div><ul>{lis}</ul></div>'

    alts = ranked[1:3]
    alts_html = ""
    if alts:
        bits = " · ".join(f'{_MEDALS[i + 1]} {e(a["web_name"])} {a["xp"]:.1f}' for i, a in enumerate(alts))
        alts_html = f'<div class="cc-alts"><span class="cc-h">Alternatives</span> {bits}</div>'

    return (
        f'{_CARD_CSS}<div class="cap-card">'
        f'<div class="cc-head">🥇 Captain Pick{scope_html}</div>'
        f'<div class="cc-pick"><span class="cc-name">{e(top["web_name"])}</span>'
        f'<span class="cc-team">{e(team)} · {e(top.get("position") or "")}</span>{proj}{conf_html}</div>'
        f'<div class="cc-cols">{why_html}{risk_html}</div>'
        f'{alts_html}'
        # US-355: the MADBOOTS mark — the captain card joins the player card's brand family (ADR-103/084).
        f'<div class="cc-brand">{brand.mark_html(badge_px=15, font_px=12)}'
        f'<span class="cc-t">Captain Pick</span></div></div>'
    )


def render_captain_card(ranked, explanation, *, scope: str = "", team_names=None) -> None:
    """Render the Captain Pick card (US-294). Display-only; a no-op when there are no picks."""
    markup = captain_card_html(ranked, explanation, scope=scope, team_names=team_names)
    if markup:
        st.markdown(markup, unsafe_allow_html=True)
