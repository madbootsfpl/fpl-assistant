"""The AI Verdict card — a headline call + a gauge + grounded Edge/Risk (Sprint 169, US-413, ADR-118).

Renders `analytics.player_verdict` as a self-contained dark card with a **server-built SVG gauge** (the score arc)
sitting above the DNA radar. `build_verdict` computes the verdict's inputs by **reusing what the Card view already
has** — the `decision_xp` map and the `PlayerDNA` percentiles — so there is no new store read and no
`decision_xp` change. Display-only.
"""

import math
import statistics

import streamlit as st

from src.analytics import player_verdict
from src.analytics.optimizer import is_unavailable
from src.web_streamlit import brand

# Verdict word → a tone colour (on-dark, legible), reinforcing the call on the gauge + label. Grouped by strength
# so the owned-aware words (Hold/Sell · Buy/Consider/Pass) share the browse tones.
_TONE_GOOD = {"Strong pick", "Strong Hold", "Buy"}
_TONE_OK = {"Solid pick", "Hold", "Consider"}
_TONE_MEH = {"Risky", "Sell", "Pass"}


def _tone(label: str) -> str:
    if label in _TONE_GOOD:
        return "#01fc7a"
    if label in _TONE_OK:
        return brand.ACCENT_TEAL
    if label in _TONE_MEH:
        return "#ffb020"
    return "#ff6b7d"      # Avoid

VD_CSS = """
<style>
.vd-card{background:linear-gradient(180deg,#141b28,#0e141f);border:1px solid rgba(255,255,255,.10);
border-radius:18px;color:#f2f6fb;margin:.5rem 0;padding:15px 18px;display:flex;gap:16px;align-items:center;
box-shadow:0 18px 40px -22px rgba(0,0,0,.7);
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.vd-card .vd-gauge{flex:none;width:92px;height:92px;position:relative;}
.vd-card .vd-gauge svg{width:100%;height:100%;display:block;}
.vd-card .vd-score{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
justify-content:center;line-height:1;}
.vd-card .vd-num{font-size:1.5rem;font-weight:800;font-variant-numeric:tabular-nums;}
.vd-card .vd-den{font-size:.6rem;color:#7c8899;margin-top:2px;}
.vd-card .vd-body{min-width:0;}
.vd-card .vd-tag{font-size:.66rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:#aab6c6;}
.vd-card .vd-label{font-size:1.45rem;font-weight:800;line-height:1.1;margin:1px 0 7px;letter-spacing:-.01em;}
.vd-card .vd-line{font-size:.82rem;line-height:1.45;color:#cdd6e2;}
.vd-card .vd-line + .vd-line{margin-top:2px;}
.vd-card .vd-line.risk{color:#e6b98a;}
.vd-card .vd-k{font-weight:800;}
.vd-card .vd-k.edge{color:#5eead4;} .vd-card .vd-k.risk{color:#ffb020;}
@media(max-width:520px){.vd-card .vd-label{font-size:1.25rem;}}
</style>
"""


def _esc(s) -> str:
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def gauge_svg(score, tone, *, size: int = 92) -> str:
    """A donut gauge whose coloured arc fills to `score`/100 (the rest a faint track). Pure SVG, no script."""
    r = size / 2 - 7
    circ = 2 * math.pi * r
    frac = max(0, min(100, score)) / 100.0
    cx = cy = size / 2
    return (
        f'<svg viewBox="0 0 {size} {size}" role="img" aria-label="verdict score {score} out of 100">'
        f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="rgba(255,255,255,.10)" stroke-width="8"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{tone}" stroke-width="8" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ * (1 - frac):.1f}" '
        f'transform="rotate(-90 {cx} {cy})"/></svg>')


def verdict_card_html(verdict) -> str:
    """The full verdict card: the gauge + the one-word call + grounded Edge (✓) / Risk (⚠) lines."""
    tone = _tone(verdict.label)
    lines = ""
    if verdict.edge:
        lines += f'<div class="vd-line"><span class="vd-k edge">Edge</span> {_esc(" · ".join(verdict.edge))}</div>'
    if verdict.risk:
        lines += (f'<div class="vd-line risk"><span class="vd-k risk">Risk</span> '
                  f'{_esc(" · ".join(verdict.risk))}</div>')
    return (VD_CSS + '<div class="vd-card">'
            f'<div class="vd-gauge">{gauge_svg(verdict.score, tone)}'
            f'<div class="vd-score"><span class="vd-num">{verdict.score}</span>'
            '<span class="vd-den">/100</span></div></div>'
            '<div class="vd-body"><div class="vd-tag">✦ AI Verdict</div>'
            f'<div class="vd-label" style="color:{tone}">{_esc(verdict.label)}</div>'
            f'{lines}</div></div>')


def build_verdict(player, players, xp_by_id, dna, *, owned=None, horizon: int = 1):
    """Assemble a `Verdict` for `player`, reusing the `xp_by_id` map and the `PlayerDNA` the Card view already has.

    Computes the value verdict's inputs (xP/£m value + the position median + the value rank among **available**
    same-position players) and the xP percentile-in-position, then calls `analytics.player_verdict`. `dna` (from
    `player_dna`) supplies the Value + Consistency percentiles. `owned` frames the label (browse → Strong pick/…;
    True → Hold/Sell; False → Buy/…). Returns None if `dna`/`player` is missing."""
    if not player or dna is None:
        return None
    pos = player["position"]
    xp = xp_by_id.get(player["id"])
    price = player["price"] or 0.0

    def _val(r):
        pr = r["price"] or 0.0
        return (xp_by_id.get(r["id"], 0.0) / pr) if pr > 0 else 0.0

    peers = [r for r in players if r["position"] == pos and not is_unavailable(r)]
    values = [_val(r) for r in peers]
    value = (xp / price) if (xp is not None and price > 0) else 0.0
    median = statistics.median(values) if values else 0.0
    ranked = sorted(peers, key=_val, reverse=True)
    rank = next((i + 1 for i, r in enumerate(ranked) if r["id"] == player["id"]), None)
    n_peers = len(peers)
    xp_pct = round(100 * sum(1 for r in peers if xp_by_id.get(r["id"], 0.0) <= (xp or 0.0)) / n_peers) \
        if n_peers else 50

    by_axis = {a.label: a.percentile for a in dna.axes}
    return player_verdict(
        player, xp=xp, xp_percentile=xp_pct, value=value, median=median, rank=rank, n_peers=n_peers,
        value_percentile=by_axis.get("Value"), consistency_percentile=by_axis.get("Consistency"),
        available=not is_unavailable(player), doubtful=(player["status"] == "d"),
        chance=player["chance"], owned=owned, horizon=horizon)


def render_verdict_card(verdict) -> None:
    """Render a `Verdict` as the gauge card (no-op if `verdict` is None)."""
    if verdict is None:
        return
    st.markdown(verdict_card_html(verdict), unsafe_allow_html=True)
