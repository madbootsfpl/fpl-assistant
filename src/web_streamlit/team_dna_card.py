"""The Team DNA browse card — Fixtures ▸ 🧬 Team DNA (Sprint 172, US-419, ADR-119).

Composes the team-level section by **reusing** the Player-DNA pieces: the shared `radar_svg`, the verdict
`gauge_svg` (here showing the A+…D **grade**), and the whole `insights_card`. Adds a grade header, an FDR-tinted
fixtures row and a key-players-to-target table. Display-only; reuses the caller's `players` + `fixtures` — no new
store read, no `decision_xp`/FDR change.
"""

import streamlit as st

from src.analytics import team_insights
from src.analytics.player_dna import _f, _get
from src.web_streamlit import brand
from src.web_streamlit.dna_card import _band, radar_svg
from src.web_streamlit.insights_card import render_insights_card
from src.web_streamlit.verdict_card import gauge_svg

FDR_STYLE = brand.FDR_STYLE

TD_CSS = """
<style>
.td-card{background:linear-gradient(180deg,#141b28,#0e141f);border:1px solid rgba(255,255,255,.10);
border-radius:18px;color:#f2f6fb;margin:.5rem 0;padding:16px 18px;box-shadow:0 18px 40px -22px rgba(0,0,0,.7);
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.td-head{display:flex;gap:15px;align-items:center;margin-bottom:6px;}
.td-gauge{flex:none;width:86px;height:86px;position:relative;}
.td-gauge svg{width:100%;height:100%;display:block;}
.td-gv{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1;}
.td-letter{font-size:1.7rem;font-weight:900;} .td-gv span{font-size:.58rem;color:#7c8899;margin-top:2px;}
.td-name{font-size:1.5rem;font-weight:900;line-height:1.05;} .td-sub{color:#9aa3b2;font-size:.8rem;margin-top:2px;}
.td-tag{font-size:.66rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:#aab6c6;}
.td-card svg.dna-svg{display:block;width:100%;max-width:400px;height:auto;margin:2px auto;}
.td-chips{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:6px;}
.td-chip{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);border-radius:10px;padding:7px 9px;}
.td-cl{font-size:.68rem;color:#aab6c6;line-height:1.15;} .td-cs{color:#7c8899;font-size:.6rem;}
.td-pct{font-size:.72rem;font-weight:900;border-radius:6px;padding:1px 6px;margin-top:4px;display:inline-block;}
.td-ttl{font-weight:800;font-size:.7rem;letter-spacing:.08em;color:#aab6c6;text-transform:uppercase;margin-bottom:8px;}
.td-fxrow{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;}
.td-fx{border-radius:9px;padding:7px 4px;text-align:center;} .td-fx .g{font-size:.62rem;opacity:.85;font-weight:700;}
.td-fx .o{font-size:.9rem;font-weight:900;margin:1px 0;} .td-fx .h{font-size:.6rem;opacity:.9;font-weight:700;}
.td-tbl{width:100%;border-collapse:collapse;font-size:.82rem;} .td-tbl th{text-align:right;color:#7c8899;
font-size:.64rem;font-weight:700;padding:4px 6px;border-bottom:1px solid rgba(255,255,255,.10);}
.td-tbl th:first-child{text-align:left;} .td-tbl td{text-align:right;padding:6px;
border-bottom:1px solid rgba(255,255,255,.05);font-variant-numeric:tabular-nums;}
.td-tbl td:first-child{text-align:left;font-weight:700;} .td-pos{color:#7c8899;font-size:.62rem;margin-left:6px;}
@media(max-width:520px){.td-chips{grid-template-columns:repeat(2,1fr);}}
</style>
"""

_GRADE_TONE = {"A+": "#01fc7a", "A": "#01fc7a", "B": brand.ACCENT_TEAL, "C": "#ffb020", "D": "#ff6b7d"}


def _esc(s) -> str:
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _tone(grade) -> str:
    return _GRADE_TONE.get(grade, brand.ACCENT_TEAL)


def _chip(ax) -> str:
    bg, fg = _band(ax.percentile)
    pct = "—" if ax.percentile is None else f"{ax.percentile}"
    raw = ax.value
    raw_str = f"{raw:,.0f}" if abs(raw) >= 100 else f"{raw:g}"
    return (f'<div class="td-chip"><div class="td-cl">{_esc(ax.label)}<br>'
            f'<span class="td-cs">{_esc(ax.sublabel)} · {raw_str}</span></div>'
            f'<span class="td-pct" style="background:{bg};color:{fg}">{pct}</span></div>')


def head_html(dna) -> str:
    """The grade header + radar + percentile chips for a `TeamDNA`."""
    tone = _tone(dna.grade)
    chips = "".join(_chip(a) for a in dna.axes)
    return (TD_CSS + '<div class="td-card"><div class="td-head">'
            f'<div class="td-gauge">{gauge_svg(dna.grade_score, tone, size=86)}'
            f'<div class="td-gv"><span class="td-letter" style="color:{tone}">{_esc(dna.grade)}</span>'
            f'<span>{dna.grade_score}/100</span></div></div>'
            f'<div><div class="td-tag">🧬 Team DNA</div><div class="td-name">{_esc(dna.name)}</div>'
            '<div class="td-sub">Percentile rank vs all 20 Premier League teams</div></div></div>'
            f'{radar_svg(dna.axes, label=dna.name)}<div class="td-chips">{chips}</div></div>')


def fixtures_html(fixtures) -> str:
    """An FDR-tinted next-N fixtures row. `fixtures` = list of `(gw, opponent, "H"/"A", fdr)`."""
    if not fixtures:
        return ""
    cells = ""
    for gw, opp, ha, d in fixtures:
        bg, fg = FDR_STYLE.get(int(d or 3), FDR_STYLE[3])
        cells += (f'<div class="td-fx" style="background:{bg};color:{fg}"><div class="g">GW{gw}</div>'
                  f'<div class="o">{_esc(opp)}</div><div class="h">({_esc(ha)})</div></div>')
    return (TD_CSS + '<div class="td-card"><div class="td-ttl">📅 Fixtures — next '
            f'{len(fixtures)}</div><div class="td-fxrow">{cells}</div></div>')


def key_players_html(rows) -> str:
    """A key-players-to-target table. `rows` = list of dicts (name, pos, xgi90, pts90, minpct, own)."""
    if not rows:
        return ""
    body = "".join(
        f'<tr><td>{_esc(p["name"])}<span class="td-pos">{_esc(p["pos"])}</span></td>'
        f'<td>{p["xgi90"]:.2f}</td><td>{p["pts90"]:.1f}</td><td>{p["minpct"]}%</td>'
        f'<td>{p["own"]:.1f}%</td></tr>' for p in rows)
    return (TD_CSS + '<div class="td-card"><div class="td-ttl">🎯 Key players to target (FPL impact)</div>'
            '<table class="td-tbl"><thead><tr><th>Player</th><th>xGI/90</th><th>Pts/90</th>'
            f'<th>Mins</th><th>Own</th></tr></thead><tbody>{body}</tbody></table></div>')


def team_key_players(players, team, *, n: int = 7, min_minutes: int = 900) -> list[dict]:
    """The team's top players by FPL points (min. `min_minutes`), each with the target-table fields.
    Row/dict safe; per-90 rates + a minutes% of a full season (38×90)."""
    ps = [p for p in players if _get(p, "team") == team and _f(_get(p, "minutes")) >= min_minutes]
    ps.sort(key=lambda p: _f(_get(p, "total_points")), reverse=True)
    out = []
    for p in ps[:n]:
        mins = _f(_get(p, "minutes"))
        p90 = mins / 90 or 1
        out.append({"name": _get(p, "web_name"), "pos": _get(p, "position"),
                    "xgi90": _f(_get(p, "xgi")) / p90, "pts90": _f(_get(p, "total_points")) / p90,
                    "minpct": min(100, round(mins / 3420 * 100)), "own": _f(_get(p, "selected_by"))})
    return out


def render_team_dna(dna, *, fixtures=None, key_players=None) -> None:
    """Render the full Team DNA section: grade header + radar → insights → fixtures → key players. No-op if
    `dna` is None."""
    if dna is None:
        return
    st.markdown(head_html(dna), unsafe_allow_html=True)
    render_insights_card(team_insights(dna))
    if fixtures:
        st.markdown(fixtures_html(fixtures), unsafe_allow_html=True)
    if key_players:
        st.markdown(key_players_html(key_players), unsafe_allow_html=True)
