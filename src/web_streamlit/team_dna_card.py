"""The Team DNA browse card — Fixtures ▸ 🧬 Team DNA (Sprint 172, US-419, ADR-119).

Composes the team-level section by **reusing** the Player-DNA pieces: the shared `radar_svg`, the verdict
`gauge_svg` (here showing the A+…D **grade**), and the whole `insights_card`. Adds a grade header, an FDR-tinted
fixtures row and a key-players-to-target table. Display-only; reuses the caller's `players` + `fixtures` — no new
store read, no `decision_xp`/FDR change.
"""

from collections import defaultdict

import streamlit as st

from src.analytics import team_dna_all, team_insights, team_schedule
from src.analytics.gw_form import team_form
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
.td-form{display:flex;align-items:center;gap:6px;margin-top:10px;flex-wrap:wrap;}
.td-fl{color:#7c8899;font-size:.66rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;}
.td-dot{width:20px;height:20px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;
font-size:.66rem;font-weight:800;color:#0c121a;}
.td-dot.w{background:#5eead4;} .td-dot.d{background:#a8b3c4;} .td-dot.l{background:#f98a8a;}
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


def _form_row(form) -> str:
    """The team's recent results as W/D/L pills. Empty when the team hasn't played — never a row of blanks."""
    if not form:
        return ""
    pills = "".join(f'<span class="td-dot {r.lower()}" title="GW{rnd}">{r}</span>' for rnd, r in form)
    return f'<div class="td-form"><span class="td-fl">Form</span>{pills}</div>'


def fixtures_html(fixtures, form=None) -> str:
    """An FDR-tinted next-N fixtures row, with the team's recent W-D-L run beneath it when there is one.

    `fixtures` = list of `(gw, opponent, "H"/"A", fdr)`; `form` = `[(round, "W"|"D"|"L"), …]` (ADR-128, the
    ADR-119 follow-up). What's coming reads better next to what just happened, so they share a card. The form
    row renders nothing at all before a team has played."""
    if not fixtures:
        return ""
    form = _form_row(form)
    cells = ""
    for gw, opp, ha, d in fixtures:
        bg, fg = FDR_STYLE.get(int(d or 3), FDR_STYLE[3])
        cells += (f'<div class="td-fx" style="background:{bg};color:{fg}"><div class="g">GW{gw}</div>'
                  f'<div class="o">{_esc(opp)}</div><div class="h">({_esc(ha)})</div></div>')
    return (TD_CSS + '<div class="td-card"><div class="td-ttl">📅 Fixtures — next '
            f'{len(fixtures)}</div><div class="td-fxrow">{cells}</div>{form}</div>')


def key_players_html(rows, season=None) -> str:
    """A key-players-to-target table. `rows` = list of dicts (name, pos, xgi90, pts90, minpct, own).

    `season` names the season the rows come from when it isn't this one (ADR-126). Ranking here needs ~900
    minutes, so until about gameweek 10 this season cannot answer and last season's numbers are shown instead —
    behind a line saying so, because an unlabelled number from another season is worse than an empty table.
    With no last-season rows either (a promoted side, or players new to the league) the "fills in" note stands.
    """
    if not rows:
        return (TD_CSS + '<div class="td-card"><div class="td-ttl">🎯 Key players to target (FPL impact)</div>'
                '<div class="td-sub">🌱 Fills in as the season plays — a player needs ~900+ minutes to rank here.'
                '</div></div>')
    note = ('<div class="td-sub">📅 <b>' + _esc(str(season)) + '</b> — ranking needs ~900 minutes, so this '
            'season\'s table fills from about GW10. Ownership is current.</div>') if season else ""
    body = "".join(
        f'<tr><td>{_esc(p["name"])}<span class="td-pos">{_esc(p["pos"])}</span></td>'
        f'<td>{p["xgi90"]:.2f}</td><td>{p["pts90"]:.1f}</td><td>{p["minpct"]}%</td>'
        f'<td>{p["own"]:.1f}%</td></tr>' for p in rows)
    return (TD_CSS + '<div class="td-card"><div class="td-ttl">🎯 Key players to target (FPL impact)</div>'
            f'{note}<table class="td-tbl"><thead><tr><th>Player</th><th>xGI/90</th><th>Pts/90</th>'
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


def key_players_this_or_last(players, team, last_rows=None, season_name=None, **kw):
    """A team's key players from this season, or last season's if this season can't rank anyone yet (ADR-126).

    `team_key_players` runs **unchanged** on last season, because `last_season_rows` hands it the same mapping
    shape `get_players()` does — and it filters on the *current* club, which the projection carries, so a
    summer signing is ranked with the side he plays for now. Returns `(rows, season_label)`; the label is None
    when the rows are this season's, so the caller has nothing to announce."""
    rows = team_key_players(players, team, **kw)
    if rows:
        return rows, None
    return team_key_players(last_rows or [], team, **kw), (season_name if last_rows else None)


def render_team_dna(dna, *, fixtures=None, key_players=None, key_players_season=None, form=None) -> None:
    """Render the full Team DNA section: grade header + radar → insights → fixtures → key players. No-op if
    `dna` is None. `key_players_season` names the season behind the table when it isn't this one (ADR-126)."""
    if dna is None:
        return
    st.markdown(head_html(dna), unsafe_allow_html=True)
    render_insights_card(team_insights(dna))
    if fixtures:
        st.markdown(fixtures_html(fixtures, form), unsafe_allow_html=True)
    # renders a "fills in" note when there's nothing for either season
    st.markdown(key_players_html(key_players or [], key_players_season), unsafe_allow_html=True)


# ── My Squad ▸ Health: the "Your teams" strip (US-420) ────────────────────────

YT_CSS = """
<style>
.yt-strip{background:linear-gradient(180deg,#141b28,#0e141f);border:1px solid rgba(139,47,201,.45);
border-radius:16px;padding:14px 16px;margin:.5rem 0;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.yt-ttl{font-weight:800;font-size:.7rem;letter-spacing:.08em;color:#aab6c6;text-transform:uppercase;margin-bottom:8px;}
.yt-row{display:grid;grid-template-columns:44px 34px 1.1fr 1.4fr;gap:10px;align-items:center;padding:8px 0;
border-bottom:1px solid rgba(255,255,255,.06);font-size:.84rem;color:#f2f6fb;}
.yt-row:last-child{border-bottom:none;}
.yt-badge{width:36px;height:24px;border-radius:6px;background:#241b3a;display:grid;place-items:center;
font-weight:800;font-size:.64rem;color:#cdd6e2;}
.yt-grade{font-weight:900;font-size:1.15rem;}
.yt-axes{color:#aab6c6;font-size:.74rem;white-space:nowrap;}
.yt-dot{display:inline-block;width:9px;height:9px;border-radius:50%;vertical-align:middle;margin:0 1px;}
.yt-mine{color:#9aa3b2;font-size:.74rem;overflow:hidden;text-overflow:ellipsis;}
</style>
"""


def your_teams_rows(owned, all_dna) -> list[dict]:
    """One row per club the squad owns players in — grade + key percentiles + the owned players there, best grade
    first. `owned` = the squad's player rows; `all_dna` = `team_dna_all(...)`."""
    by_team: dict = defaultdict(list)
    for p in owned:
        by_team[_get(p, "team")].append(_get(p, "web_name"))
    rows = []
    for t in sorted(by_team, key=lambda t: all_dna[t].grade_score if t in all_dna else -1, reverse=True):
        d = all_dna.get(t)
        if not d:
            continue
        by = {a.label: a.percentile for a in d.axes}
        rows.append({"team": t, "name": d.name, "grade": d.grade, "score": d.grade_score,
                     "att": by.get("Attacking Threat"), "dfc": by.get("Defensive Strength"),
                     "fix": by.get("Fixture Strength"), "players": ", ".join(by_team[t])})
    return rows


def your_teams_strip_html(rows) -> str:
    """The compact "Your teams" strip HTML (a row per club: badge · grade · ATT/DEF/FIX dots · your players)."""
    if not rows:
        return ""
    def dot(v):
        return f'<span class="yt-dot" style="background:{_band(v)[0]}"></span>'
    body = "".join(
        f'<div class="yt-row"><div class="yt-badge">{_esc(r["team"])}</div>'
        f'<div class="yt-grade" style="color:{_tone(r["grade"])}">{_esc(r["grade"])}</div>'
        f'<div class="yt-axes">ATT {dot(r["att"])} · DEF {dot(r["dfc"])} · FIX {dot(r["fix"])}</div>'
        f'<div class="yt-mine">{_esc(r["players"])}</div></div>' for r in rows)
    return (YT_CSS + '<div class="yt-strip"><div class="yt-ttl">🧬 Your teams — strength behind your squad'
            f'</div>{body}</div>')


def render_your_teams(squad, players, fixtures, *, team_names=None, last_rows=None, season_name=None,
                      gw_history=None) -> None:
    """The My Squad ▸ Health "Your teams" strip (ADR-119): each of your clubs' grade + key axes + your players,
    then a drill-in into the full Team DNA card. No-op without a squad. Reuses the caller's `players`/`fixtures`."""
    if not squad or not squad.get("player_ids"):
        return
    owned_ids = set(squad["player_ids"])
    owned = [p for p in players if _get(p, "id") in owned_ids]
    if not owned:
        return
    all_dna = team_dna_all(players, fixtures, team_names=team_names, gw_history=gw_history)
    rows = your_teams_rows(owned, all_dna)
    if not rows:
        return
    st.markdown(your_teams_strip_html(rows), unsafe_allow_html=True)
    st.caption("Dots = percentile vs the league (🟢 elite → 🔴 weak). Your investments, both ends — a hard "
               "**FIX** run is a transfer signal. Pick a club below for its full Team DNA.")
    labels = {f'{r["name"]} ({r["grade"]})': r["team"] for r in rows}
    picked = labels.get(st.selectbox("View a team's DNA", ["—", *labels], key="health_team_dna",
                                     help="Drill into any of your clubs' full Team DNA."))
    if picked:
        sched = team_schedule(fixtures, picked)[:6]
        fx = [(s["event"], s["opponent"], s["venue"], s["difficulty"]) for s in sched]
        _kp, _season = key_players_this_or_last(players, picked, last_rows, season_name)
        render_team_dna(all_dna[picked], fixtures=fx, key_players=_kp, key_players_season=_season,
                        form=team_form(gw_history or {}, players, picked))
