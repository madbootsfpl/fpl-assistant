"""A formation "pitch" view for the Streamlit edge (Sprint 062; redesigned Sprint 099, ADR-084).

A styled **green pitch**: players laid out by formation (GK / DEF / MID / FWD) + a bench strip, each a compact
**kit card** — the photo/club-shirt image · name · xP chip · £ · next opponent (H/A) · (C) armband · sub badge
· crowd/set-piece flags. One self-contained HTML/CSS block via `st.markdown(unsafe_allow_html=True)` (no JS),
so it's themeable + headless-testable (the HTML is inspectable via `AppTest.markdown`). Pure presentation over
data the page already holds; **display-only** — the edit controls are separate widgets on the page.
"""

import html

import streamlit as st

from src.analytics import crowd_flags, set_piece_flags

_ROWS = ("GK", "DEF", "MID", "FWD")
_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
_ROLE_ORDER = {"1st": 0, "2nd": 1, "3rd": 2, "4th": 3, "GK": 4}

# One self-contained stylesheet (scoped to `.fpl-pitch`). A green pitch with mow stripes + a faint centre
# circle; light kit cards that read on both Streamlit themes. Lines are unindented so st.markdown doesn't
# treat them as a code block.
_PITCH_CSS = """
<style>
.fpl-pitch{
background:
radial-gradient(circle at 50% 42%, rgba(255,255,255,.16) 0 62px, rgba(255,255,255,0) 63px),
repeating-linear-gradient(0deg,#218a4c 0 44px,#1e8047 44px 88px);
border-radius:16px;padding:16px 8px 20px;box-shadow:inset 0 0 0 3px rgba(255,255,255,.28);
}
.fpl-pitch .row{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin:14px 0;}
.fpl-pitch .kit{width:80px;text-align:center;color:#fff;}
.fpl-pitch .kit img{width:46px;height:46px;object-fit:contain;display:block;margin:0 auto 4px;
filter:drop-shadow(0 2px 3px rgba(0,0,0,.35));}
.fpl-pitch .name{font-weight:700;font-size:.76rem;line-height:1.05;text-shadow:0 1px 2px rgba(0,0,0,.5);
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.fpl-pitch .xp{display:inline-block;margin-top:2px;padding:0 7px;border-radius:9px;background:#fff;
color:#0a7a34;font-weight:700;font-size:.72rem;}
.fpl-pitch .meta{font-size:.64rem;opacity:.92;text-shadow:0 1px 2px rgba(0,0,0,.5);margin-top:2px;}
.fpl-pitch .cap{color:#ffd23f;font-weight:800;}
.fpl-pitch .flags{font-size:.66rem;margin-top:2px;line-height:1.2;}
.fpl-pitch .sub{font-size:.62rem;color:#eafff0;opacity:.9;margin-bottom:2px;}
.fpl-pitch .bench-label{color:#eafff0;font-size:.72rem;letter-spacing:.12em;text-align:center;
margin:18px 0 2px;opacity:.85;text-transform:uppercase;}
.fpl-pitch .bench{background:rgba(0,0,0,.16);border-radius:12px;padding:10px 6px;margin-top:2px;}
</style>
"""


def _kit_html(player, *, captain_id, xp_by_id, photos, next_opp, sub_role=None) -> str:
    """One player's kit card (ADR-084) — image · name (+ (C)) · xP chip · £ · next opponent · crowd/set-piece
    flags · sub badge. Every text value is HTML-escaped so a name with `&`/`<`/`'` can't break the markup."""
    e = html.escape
    img = photos.get(player["id"], "")
    img_html = f'<img src="{e(img)}" alt="">' if img else ""
    cap = ' <span class="cap">(C)</span>' if player["id"] == captain_id else ""
    xp = round(xp_by_id.get(player["id"], 0), 1)
    opp = next_opp.get(player["team"])
    opp_str = f'{e(opp["opponent"])} ({e(opp["venue"])})' if opp else "—"
    meta = f'£{player["price"]:.1f}m · {opp_str}'
    flags = crowd_flags(player) + set_piece_flags(player)
    flags_html = f'<div class="flags">{e(" ".join(flags))}</div>' if flags else ""
    sub_html = ""
    if sub_role:
        label = "GK sub" if sub_role == "GK" else f"{sub_role} sub"
        sub_html = f'<div class="sub">🔁 {e(label)}</div>'
    return (f'<div class="kit">{sub_html}{img_html}'
            f'<div class="name">{e(player["web_name"])}{cap}</div>'
            f'<div class="xp">{xp}</div>'
            f'<div class="meta">{meta}</div>{flags_html}</div>')


def render_pitch(xi, bench, *, captain_id, xp_by_id, photos, next_opp, bench_roles=None) -> None:
    """Lay out the XI by formation rows + a bench strip, each player a kit card (ADR-084).

    `xi` / `bench` are player rows; `next_opp` maps a team short_name → its next fixture cell
    (`{opponent, venue, ...}`) or None. `bench_roles` (US-246) maps id → sub role ("1st"/"2nd"/"3rd"/"GK");
    when given, the bench is ordered by that priority. Emits one self-contained HTML/CSS block (no JS) —
    display-only; the edit controls live on the page.
    """
    kw = dict(captain_id=captain_id, xp_by_id=xp_by_id, photos=photos, next_opp=next_opp)
    parts = [_PITCH_CSS, '<div class="fpl-pitch">']

    for pos in _ROWS:
        line = [p for p in xi if p["position"] == pos]
        if not line:
            continue
        cells = "".join(_kit_html(p, **kw) for p in line)
        parts.append(f'<div class="row">{cells}</div>')

    if bench:
        if bench_roles:
            ordered = sorted(bench, key=lambda p: _ROLE_ORDER.get(bench_roles.get(p["id"]), 9))
        else:
            ordered = sorted(bench, key=lambda p: _ORDER.get(p["position"], 9))
        cells = "".join(_kit_html(p, sub_role=(bench_roles or {}).get(p["id"]), **kw) for p in ordered)
        parts.append(f'<div class="bench-label">Bench</div><div class="row bench">{cells}</div>')

    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
