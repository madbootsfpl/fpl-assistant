"""A rich, position-adaptive **Player Card** for the Streamlit edge (Sprint 139, US-342; the pitch/card pattern,
ADR-084).

**One self-contained HTML/CSS block** (no JS) via `st.markdown(unsafe_allow_html=True)`: a header (photo · club
badge · Team · Position · £price · name) + **FDR fixture pills** + flags (ownership tier · set-pieces · availability
· a **Projected-xP** chip) + a **two-column stat grid whose rows adapt to the player's position** (FWD/MID lead on
goals/xGI/ICT; DEF on xGC/DefCon-90/CBI; GK on xGC/recoveries). A **fixed dark surface** — like the green pitch, it
reads on either Streamlit theme; every value is `html.escape`d. Display-only; never touches xP.

A `compact=True` variant (header + a few key stats, no brand band) feeds the My Squad pitch hover popover (US-344).
Fed by data the page already holds (the `Player` row + `crowd`/price flags); the Projected xP is optional
(`decision_xp`) — the chip just hides when it's not supplied.
"""

import html

import streamlit as st

from src.analytics.crowd import availability_flag, ownership_tier, set_piece_flags
from src.web_streamlit import brand

# Scoped to `.pl-card`; a fixed dark surface (its own colours, like the pitch) that reads on both themes. Lines
# unindented so `st.markdown` doesn't treat the CSS as a code block. Public so the pitch can include it **once**
# and drop a CSS-less `card_body(...)` per kit (US-344, avoids 15× the stylesheet).
CARD_CSS = """
<style>
.pl-card{background:linear-gradient(180deg,#111821,#0c121a);border:1px solid rgba(255,255,255,.09);
border-radius:18px;overflow:hidden;color:#f2f6fb;margin:.5rem 0;box-shadow:0 18px 40px -22px rgba(0,0,0,.7);
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.pl-card .plc-head{display:flex;gap:16px;padding:18px 20px 14px;align-items:center;}
.pl-card .plc-photo{width:84px;height:84px;border-radius:50%;flex:none;background:#1b2430;
border:2px solid rgba(255,255,255,.16);overflow:hidden;}
.pl-card .plc-photo img{width:100%;height:100%;object-fit:cover;object-position:top center;display:block;}
.pl-card .plc-id{min-width:0;flex:1;}
.pl-card .plc-meta{display:flex;align-items:center;gap:8px;color:#aab6c6;font-size:.9rem;font-weight:500;}
.pl-card .plc-meta img{width:18px;height:18px;}
.pl-card .plc-meta b{color:#f2f6fb;}
.pl-card .plc-name{font-size:1.7rem;font-weight:800;line-height:1.05;letter-spacing:-.02em;margin:.12rem 0 .5rem;}
.pl-card .plc-fix{display:flex;align-items:center;gap:7px;flex-wrap:wrap;}
.pl-card .plc-gw{color:#7c8899;font-size:.78rem;font-weight:600;}
.pl-card .plc-pill{border-radius:999px;padding:4px 10px;font-size:.74rem;font-weight:700;color:#fff;
white-space:nowrap;box-shadow:0 1px 2px rgba(0,0,0,.3) inset;}
.pl-card .plc-flags{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;}
.pl-card .plc-flag{font-size:.72rem;font-weight:700;background:rgba(255,255,255,.06);
border:1px solid rgba(255,255,255,.09);padding:3px 8px;border-radius:999px;color:#e6edf5;}
.pl-card .plc-flag.proj{color:#5eead4;}
.pl-card .plc-band{display:flex;justify-content:space-between;align-items:center;margin:2px 14px 0;padding:9px 14px;
border-radius:12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);}
.pl-card .plc-brand{font-weight:800;font-size:.72rem;letter-spacing:.08em;color:#aab6c6;text-transform:uppercase;}
.pl-card .plc-title{font-weight:800;color:#5eead4;}
.pl-card .plc-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 26px;padding:10px 22px 20px;}
.pl-card .plc-stat{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:9px 2px;
border-bottom:1px solid rgba(255,255,255,.08);}
.pl-card .plc-stat .l{color:#aab6c6;font-size:.9rem;}
.pl-card .plc-stat .v{font-weight:800;font-size:1.25rem;font-variant-numeric:tabular-nums;letter-spacing:-.01em;}
.pl-card.compact .plc-head{padding:12px 14px 8px;gap:12px;}
.pl-card.compact .plc-photo{width:58px;height:58px;}
.pl-card.compact .plc-meta{font-size:.8rem;}
.pl-card.compact .plc-name{font-size:1.15rem;margin:.08rem 0 .35rem;}
.pl-card.compact .plc-flags{margin-top:6px;} .pl-card.compact .plc-flag{font-size:.66rem;padding:2px 7px;}
.pl-card.compact .plc-grid{padding:4px 14px 12px;gap:0 16px;}
.pl-card.compact .plc-stat{padding:6px 2px;}
.pl-card.compact .plc-stat .l{font-size:.8rem;} .pl-card.compact .plc-stat .v{font-size:1.02rem;}
.pl-card .plc-gwrow{display:flex;gap:8px;margin-top:9px;}
.pl-card .plc-gwcol{flex:1;min-width:0;text-align:center;}
.pl-card .plc-gwxp{font-weight:800;font-size:1.08rem;font-variant-numeric:tabular-nums;color:#f2f6fb;line-height:1.1;}
.pl-card .plc-gwfx{margin-top:3px;border-radius:8px;padding:2px 4px;font-size:.66rem;font-weight:700;color:#fff;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;box-shadow:0 1px 2px rgba(0,0,0,.3) inset;}
.pl-card .plc-gwlbl{margin-top:3px;font-size:.64rem;font-weight:700;color:#7c8899;text-transform:uppercase;
letter-spacing:.04em;}
.pl-card .plc-gwcol.total .plc-gwxp{color:#5eead4;}
.pl-card.compact .plc-gwrow{gap:6px;margin-top:7px;} .pl-card.compact .plc-gwxp{font-size:.94rem;}
.pl-card.compact .plc-gwfx{font-size:.6rem;padding:2px 3px;}
</style>
"""

# FDR → colour (green easy · amber neutral · red hard), matching the Fixtures ticker feel.
_FDR = {1: "#22a559", 2: "#22a559", 3: "#c98a1a", 4: "#d64545", 5: "#7f1d1d"}


def _i(v):
    return f"{int(v):,}" if v is not None else None


def _f(v, dp):
    return f"{v:.{dp}f}" if v is not None else None


def _stat_rows(player, *, compact=False):
    """(label, value) rows adapted to the player's **position** (ADR-084). Pure; skips missing values. Compact
    keeps the header-relevant few for the pitch popover."""
    p = dict(player)
    pos = (p.get("position") or "").upper()
    price = p.get("price") or 0
    pts = p.get("total_points")
    own = p.get("selected_by")
    catalog = {
        "pts": ("FPL Points", _i(pts)),
        "ppg": ("Points / game", _f(p.get("points_per_game"), 1)),
        "mins": ("Minutes", _i(p.get("minutes"))),
        "value": ("Value", f"{pts / price:.1f} pts/£m" if pts is not None and price else None),
        "own": ("Ownership", f"{own:.1f}%" if own is not None else None),
        "goals": ("Goals", _i(p.get("goals_scored"))),
        "assists": ("Assists", _i(p.get("assists"))),
        "xg": ("Expected Goals", _f(p.get("xg"), 2)),
        "xa": ("Expected Assists", _f(p.get("xa"), 2)),
        "xgi": ("xG Involvement", _f(p.get("xgi"), 2)),
        "xgc": ("Expected GC", _f(p.get("xgc"), 2)),
        "def90": ("DefCon / 90", _f(p.get("defcon_per90"), 2)),
        "cbi": ("Clr + Blk + Int", _i(p.get("cbi"))),
        "tackles": ("Tackles", _i(p.get("tackles"))),
        "recov": ("Recoveries", _i(p.get("recoveries"))),
        "ict": ("ICT Index", _f(p.get("ict_index"), 1)),
    }
    order = {
        "FWD": ["pts", "ppg", "goals", "xgi", "xg", "own", "assists", "value", "xa", "ict", "mins", "def90"],
        "MID": ["pts", "ppg", "goals", "xgi", "assists", "own", "xa", "value", "def90", "ict", "mins", "recov"],
        "DEF": ["pts", "ppg", "xgc", "def90", "cbi", "own", "tackles", "value", "goals", "assists", "mins", "recov"],
        "GK": ["pts", "ppg", "xgc", "def90", "cbi", "own", "recov", "value", "mins"],
    }.get(pos, ["pts", "ppg", "goals", "assists", "xgi", "own", "value", "mins"])
    if compact:
        order = order[:4]                                    # fewer stats so the hover popover fits (US-346)
    return [(catalog[k][0], catalog[k][1]) for k in order if catalog[k][1] is not None]


def card_body(player, *, team_name="", photo_url=None, badge_url=None,
              fixtures=None, projected_xp=None, total_xp=None, compact=False) -> str:
    """The player card's `<div>` **without** the `<style>` (pure; empty-safe). Use when the CSS is already on the
    page (the pitch includes `CARD_CSS` once). `fixtures` is a list of `{"opp","home","fdr"}` (first 3 shown); when
    each also carries an `"xp"` (ADR-109), the fixtures render as a **per-GW row** (xP over the fixture) instead of
    plain pills, with a **Total** column when `total_xp` is given (horizon >3). `projected_xp` a float (our
    `decision_xp`) → a chip when there's no per-GW row, or None to hide."""
    if not player:
        return ""
    e = html.escape
    p = dict(player)
    name = e(p.get("web_name") or "")
    pos = e(p.get("position") or "")
    price = p.get("price")
    price_html = f"£{price:.1f}m" if price is not None else ""

    photo = f'<img src="{e(str(photo_url))}" alt="{name}">' if photo_url else ""
    badge = f'<img src="{e(str(badge_url))}" alt="{e(team_name)}"> ' if badge_url else ""

    fx = list(fixtures or [])[:3]
    show_gw = bool(fx) and any(f.get("xp") is not None for f in fx)
    fix_html = ""
    if show_gw:
        # ADR-109: a per-GW row — xP (bold) over an FDR-tinted OPP (H/A) — the tester's card-under-the-shirt
        # layout. A Total column appears only when `total_xp` is given (the caller passes it when horizon > 3).
        cols = "".join(
            f'<div class="plc-gwcol"><div class="plc-gwxp">{float(f.get("xp") or 0):.1f}</div>'
            f'<div class="plc-gwfx" style="background:{_FDR.get(int(f.get("fdr") or 3), "#c98a1a")}">'
            f'{e(str(f.get("opp") or "?"))} ({"H" if f.get("home") else "A"})</div></div>'
            for f in fx)
        total_col = (f'<div class="plc-gwcol total"><div class="plc-gwxp">{total_xp:.1f}</div>'
                     f'<div class="plc-gwlbl">Total</div></div>') if total_xp is not None else ""
        fix_html = f'<div class="plc-gwrow">{cols}{total_col}</div>'
    elif fx:
        pills = "".join(
            f'<span class="plc-pill" style="background:{_FDR.get(int(f.get("fdr") or 3), "#c98a1a")}">'
            f'{e(str(f.get("opp") or "?"))} ({"H" if f.get("home") else "A"})</span>'
            for f in fx)
        fix_html = f'<div class="plc-fix"><span class="plc-gw">Next {len(fx)}</span>{pills}</div>'

    flags = []
    if projected_xp is not None and not show_gw:      # the per-GW row already carries xP (ADR-109), so skip the chip
        flags.append(f'<span class="plc-flag proj">◆ Proj. {projected_xp:.1f} xP</span>')
    if tier := ownership_tier(p):
        flags.append(f'<span class="plc-flag">{e(tier)}</span>')          # tier carries its own emoji
    flags += [f'<span class="plc-flag">{e(sp)}</span>' for sp in set_piece_flags(p)]
    if avail := availability_flag(p):
        flags.append(f'<span class="plc-flag">{e(avail)}</span>')
    flags_html = f'<div class="plc-flags">{"".join(flags)}</div>' if flags else ""

    grid = "".join(
        f'<div class="plc-stat"><span class="l">{e(lbl)}</span><span class="v">{e(val)}</span></div>'
        for lbl, val in _stat_rows(p, compact=compact))
    # US-349/355: the shared MB badge + two-tone MADBOOTS lockup (US-355 fixes the MAD/BOOTS gap); PURPLE_LT
    # reads on the band's dark ground.
    band = "" if compact else (
        f'<div class="plc-band">{brand.mark_html(badge_px=15, font_px=12, purple=brand.PURPLE_LT)}'
        '<span class="plc-title">Player Card</span><span class="plc-brand">Last season</span></div>')

    return (
        f'<div class="pl-card{" compact" if compact else ""}">'
        f'<div class="plc-head"><div class="plc-photo">{photo}</div>'
        f'<div class="plc-id"><div class="plc-meta">{badge}{e(team_name)} · {pos} · <b>{price_html}</b></div>'
        f'<div class="plc-name">{name}</div>{fix_html}{flags_html}</div></div>'
        f'{band}<div class="plc-grid">{grid}</div></div>'
    )


def player_card_html(player, **kwargs) -> str:
    """The full card — `CARD_CSS` + the body (pure; empty-safe)."""
    body = card_body(player, **kwargs)
    return f"{CARD_CSS}{body}" if body else ""


def render_player_card(player, **kwargs) -> None:
    """Render the player card (US-342). Display-only; a no-op when there's no player."""
    markup = player_card_html(player, **kwargs)
    if markup:
        st.markdown(markup, unsafe_allow_html=True)
