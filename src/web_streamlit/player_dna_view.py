"""The Player DNA section — one reusable component, two doorways (Sprint 171, ADR-118).

`render_player_dna` composes the four pieces in the approved order — **AI Verdict → DNA radar → AI Insights →
Performance trend** — so the Players tab and My Squad render the *same* thing (no drift). The trend is a per-GW
**points** line that **auto-populates at GW1** (an honest "fills in from Gameweek 1" placeholder until then).
Display-only: everything reuses the `decision_xp` the caller already computed; no `decision_xp` change.
"""

import streamlit as st

from src.analytics import player_gw_points, player_insights
from src.analytics.gw_form import form_dots, stat_series
from src.analytics.player_dna import player_dna_this_or_last
from src.web_streamlit.dna_card import render_dna_card
from src.web_streamlit.insights_card import render_insights_card
from src.web_streamlit.verdict_card import build_verdict, render_verdict_card

_TREND_CSS = """
<style>
.tr-card{background:linear-gradient(180deg,#111821,#0c121a);border:1px solid rgba(255,255,255,.09);
border-radius:18px;color:#f2f6fb;margin:.5rem 0;padding:15px 18px 14px;
box-shadow:0 18px 40px -22px rgba(0,0,0,.7);
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.tr-card .tr-ttl{font-weight:800;font-size:.72rem;letter-spacing:.08em;color:#aab6c6;
text-transform:uppercase;margin-bottom:8px;}
.tr-card svg{display:block;width:100%;max-width:460px;height:auto;margin:2px auto;}
.tr-card .tr-cap{color:#7c8899;font-size:.74rem;font-weight:600;margin-top:6px;}
.tr-card .tr-ph{border:1px dashed rgba(255,255,255,.16);border-radius:12px;padding:18px 14px;text-align:center;
color:#8c93a3;font-size:.84rem;line-height:1.5;}
.tr-card .tr-ph b{color:#cdd6e2;}
.tr-card .tr-one{text-align:center;padding:10px 6px 4px;}
.tr-card .tr-one-n{font-weight:800;font-size:2.1rem;line-height:1;color:#5eead4;
font-variant-numeric:tabular-nums;}
.tr-card .tr-one-l{color:#cdd6e2;font-size:.82rem;font-weight:700;margin-top:4px;}
.tr-card .tr-one-s{color:#7c8899;font-size:.74rem;font-weight:600;margin-top:8px;}
.tr-card .tr-dots{display:flex;align-items:center;gap:7px;margin-top:12px;flex-wrap:wrap;}
.tr-card .tr-dl{color:#7c8899;font-size:.7rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;}
.tr-card .tr-dot{width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;
justify-content:center;font-size:.7rem;font-weight:800;color:#0c121a;}
.tr-card .tr-dot.w{background:#5eead4;} .tr-card .tr-dot.d{background:#a8b3c4;}
.tr-card .tr-dot.l{background:#f98a8a;}
.tr-card .tr-spk{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:10px;margin-top:14px;}
.tr-card .tr-sp{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:9px;
padding:8px 10px;}
.tr-card .tr-sp-l{color:#7c8899;font-size:.66rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase;}
.tr-card .tr-sp svg{width:100%;height:30px;display:block;margin-top:4px;}
</style>
"""


def perf_trend_svg(series, *, w: int = 460, h: int = 90) -> str:
    """A points-per-gameweek line (area-filled) for a `[(round, points), …]` series. Pure SVG, no script."""
    pad = 8
    ys = [max(0, t[1]) for t in series]
    lo, hi = min(ys), max(ys)
    n = len(series)
    flat = hi == lo          # every gameweek scored the same — there is no range to plot against
    def px(i):
        return pad + (i * (w - 2 * pad) / (n - 1)) if n > 1 else w / 2
    def py(v):
        # The line is normalised to the player's own min..max, so a flat run has no meaningful range. Drawing it
        # against a span of 1 pinned every point to the *floor* — which reads as "scored nothing", the opposite
        # of what a steady 6-a-week return means. Centre it instead: flat is flat, not zero.
        return h / 2 if flat else h - pad - (v - lo) * (h - 2 * pad) / (hi - lo)
    pts = [(px(i), py(y)) for i, y in enumerate(ys)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{pad:.1f},{h - pad:.1f} " + line + f" {px(n - 1):.1f},{h - pad:.1f}"
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#5eead4"/>' for x, y in pts)
    last_x, last_y = pts[-1]
    return (
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="points per gameweek trend">'
        '<defs><linearGradient id="trFill" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#5eead4" stop-opacity="0.28"/>'
        '<stop offset="1" stop-color="#5eead4" stop-opacity="0"/></linearGradient></defs>'
        f'<polygon points="{area}" fill="url(#trFill)"/>'
        f'<polyline points="{line}" fill="none" stroke="#5eead4" stroke-width="2" '
        'stroke-linejoin="round" stroke-linecap="round"/>'
        f'{dots}<text x="{last_x - 4:.1f}" y="{last_y - 6:.1f}" text-anchor="end" fill="#f2f6fb" '
        f'font-size="11" font-weight="800" font-family="sans-serif">{ys[-1]}</text></svg>')


def form_dots_html(dots) -> str:
    """A row of W/D/L pills — the team's recent results (ADR-119/128 follow-up).

    A team fact shown on a player's card: it is *his* fixtures that produced his returns. Unplayed gameweeks
    never appear, so a match still to kick off cannot read as a defeat."""
    if not dots:
        return ""
    pills = "".join(f'<span class="tr-dot {r.lower()}" title="GW{rnd}">{r}</span>' for rnd, r in dots)
    return f'<div class="tr-dots"><span class="tr-dl">Team form</span>{pills}</div>'


def sparkline_svg(series, *, w: int = 120, h: int = 30) -> str:
    """A bare line for a `[(round, value), …]` series — no axes, no labels; the number lives beside it."""
    ys = [v for _r, v in series]
    lo, hi = min(ys), max(ys)
    pad = 3
    def px(i):
        return pad + i * (w - 2 * pad) / (len(ys) - 1)
    def py(v):
        # A flat run centres rather than flooring — a steady return is not a zero (the ADR-126 lesson).
        return h / 2 if hi == lo else h - pad - (v - lo) * (h - 2 * pad) / (hi - lo)
    pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(ys))
    lx, ly = px(len(ys) - 1), py(ys[-1])
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="trend">'
            f'<polyline points="{pts}" fill="none" stroke="#5eead4" stroke-width="1.6" '
            'stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.4" fill="#5eead4"/></svg>')


def sparklines_html(by_stat) -> str:
    """A small grid of per-stat sparklines — `{label: [(round, value), …]}` (ADR-118's tracked follow-up).

    Drawn only for stats with **two or more** played gameweeks. A line through one point is not a trend, and
    inviting the reader to see a direction that isn't there is the bug this project has now fixed three times.
    """
    cards = []
    for label, series in (by_stat or {}).items():
        if len(series) < 2:
            continue
        last = series[-1][1]
        val = f"{last:.2f}" if isinstance(last, float) else f"{last}"
        cards.append(f'<div class="tr-sp"><div class="tr-sp-l">{label} · {val}</div>'
                     f'{sparkline_svg(series)}</div>')
    return f'<div class="tr-spk">{"".join(cards)}</div>' if cards else ""


def trend_panel_html(series, dots=None, by_stat=None) -> str:
    """The performance-trend card: a real per-GW line once there are two gameweeks to join, the single score
    on its own after one, else the honest pre-season placeholder.

    `dots` adds the team's W-D-L run and `by_stat` a grid of per-stat sparklines (ADR-118/119's tracked GW1
    follow-ups, ADR-128). Both are additive — each renders nothing at all when its data isn't there yet, so
    the card degrades to exactly what it was before rather than to a row of empty boxes."""
    if not series:
        body = ('<div class="tr-ph">📈 <b>Fills in from Gameweek 1.</b><br>'
                'Points per gameweek, recent form and rate sparklines draw themselves once real results land '
                '(GW1 · 21 Aug 2026).</div>')
        cap = ""
    elif len(series) == 1:
        # A line through one point is not a trend, and drawing one invites the reader to see a direction that
        # isn't there. State the result instead; the chart earns its place at GW2.
        (gw, pts), = series
        body = (f'<div class="tr-one"><div class="tr-one-n">{int(pts)}</div>'
                f'<div class="tr-one-l">points in GW{gw}</div>'
                '<div class="tr-one-s">One gameweek is a result, not a trend — the line draws from GW2.</div>'
                '</div>')
        cap = ""
    else:
        gws = ", ".join(f"GW{r}" for r, _ in series)
        body = perf_trend_svg(series)
        cap = f'<div class="tr-cap">Points per gameweek · {gws}</div>'
    return (_TREND_CSS + '<div class="tr-card"><div class="tr-ttl">📈 Performance trend</div>'
            f'{body}{cap}{form_dots_html(dots)}{sparklines_html(by_stat)}</div>')


def _code(player):
    try:
        return player["code"]
    except (KeyError, IndexError, TypeError):
        return None


def render_player_dna(player, players, xp_by_id, *, gw_history=None, owned=None,
                      last_rows=None, season_name=None) -> None:
    """Render the full Player DNA section for `player`: verdict (owned-aware) → radar → insights → trend.
    No-op if `player` is falsy. Reuses `xp_by_id`; computes one `player_dna`.

    The peer pool needs 450 minutes, so early in a season nobody qualifies and every percentile is None —
    the radar had nothing to draw. `last_rows`/`season_name` (ADR-126) let it rank against last season
    instead, captioned so nobody reads a full-season fingerprint as this week's form."""
    if not player:
        return
    dna, season = player_dna_this_or_last(player, players, last_rows, season_name)
    render_verdict_card(build_verdict(player, players, xp_by_id, dna, owned=owned, horizon=1))
    if season:
        st.caption(f"🧬 DNA percentiles are **{season}** — ranking needs ~5 matches, so this season's "
                   "fingerprint draws from about GW5. Price, ownership and set-piece duty are current.")
    render_dna_card(dna)
    render_insights_card(player_insights(player, dna))
    code = _code(player)
    gwh = gw_history or {}
    # ADR-128: the per-GW table now carries the week itself, so the trend card can show the team's W-D-L run
    # and a sparkline per stat. Both no-op until there are results to draw.
    by_stat = {"Points": stat_series(gwh, code, "total_points"),
               "BPS": stat_series(gwh, code, "bps"),
               "xG": stat_series(gwh, code, "xg"),
               "xA": stat_series(gwh, code, "xa"),
               "ICT": stat_series(gwh, code, "ict_index"),
               "Minutes": stat_series(gwh, code, "minutes")}
    st.markdown(trend_panel_html(player_gw_points(gwh, code), form_dots(gwh, code), by_stat),
                unsafe_allow_html=True)
