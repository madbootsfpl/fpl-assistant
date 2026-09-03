"""A formation "pitch" view for the Streamlit edge (Sprint 062; redesigned Sprint 099, ADR-084).

A styled **green pitch**: players laid out by formation (GK / DEF / MID / FWD) + a bench strip, each a compact
**kit card** — the photo/club-shirt image · name · xP chip · £ · next opponent (H/A) · (C) armband · sub badge
· crowd/set-piece flags. One self-contained HTML/CSS block via `st.markdown(unsafe_allow_html=True)` (no JS),
so it's themeable + headless-testable (the HTML is inspectable via `AppTest.markdown`). Pure presentation over
data the page already holds; **display-only** — the edit controls are separate widgets on the page.
"""

import html

import streamlit as st

from src.analytics.crowd import CROWD_KEY, SET_PIECES, crowd_glyphs, set_piece_glyphs
from src.web_streamlit.player_card import CARD_CSS, card_body

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
.fpl-pitch .kit{width:80px;text-align:center;color:#fff;transition:transform .12s ease;}
.fpl-pitch .kit:hover{transform:translateY(-3px);}
.fpl-pitch .pic{position:relative;width:46px;height:46px;margin:0 auto 4px;}
.fpl-pitch .pic img{width:46px;height:46px;object-fit:contain;display:block;
filter:drop-shadow(0 2px 3px rgba(0,0,0,.35));}
.fpl-pitch .noimg{width:46px;height:46px;display:flex;align-items:center;justify-content:center;
font-size:1.5rem;filter:drop-shadow(0 2px 3px rgba(0,0,0,.35));}
.fpl-pitch .c-badge{position:absolute;top:-5px;right:-6px;width:17px;height:17px;border-radius:50%;
background:#ffd23f;color:#1a1a1a;font-size:.62rem;font-weight:800;line-height:17px;text-align:center;
box-shadow:0 1px 2px rgba(0,0,0,.45);}
/* The vice sits in the same corner, deliberately quieter: he only plays if the captain does not, so an
   equally loud badge would read as a second captain. Same size and place, muted fill. */
.fpl-pitch .v-badge{position:absolute;top:-5px;right:-6px;width:17px;height:17px;border-radius:50%;
background:#d9d4e6;color:#3a3350;font-size:.62rem;font-weight:800;line-height:17px;text-align:center;
box-shadow:0 1px 2px rgba(0,0,0,.35);}
.fpl-pitch .s-badge{position:absolute;top:-5px;left:-6px;height:17px;min-width:17px;border-radius:9px;
background:#0a7a34;color:#fff;font-size:.6rem;font-weight:700;line-height:17px;text-align:center;padding:0 4px;
box-shadow:0 1px 2px rgba(0,0,0,.45);}
.fpl-pitch .name{font-weight:700;font-size:.76rem;line-height:1.05;text-shadow:0 1px 2px rgba(0,0,0,.5);
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.fpl-pitch .xp{display:inline-block;margin-top:2px;padding:0 7px;border-radius:9px;background:#fff;
color:#0a7a34;font-weight:700;font-size:.72rem;box-shadow:0 1px 2px rgba(0,0,0,.25);}
.fpl-pitch .meta{font-size:.64rem;opacity:.92;text-shadow:0 1px 2px rgba(0,0,0,.5);margin-top:2px;}
.fpl-pitch .flags{font-size:.8rem;margin-top:2px;line-height:1.45;letter-spacing:1px;}
.fpl-pitch .weeks{font-size:.62rem;margin-top:2px;color:#2b6a3f;font-variant-numeric:tabular-nums;}
.fpl-pitch .bench-label{color:#eafff0;font-size:.72rem;letter-spacing:.12em;text-align:center;
margin:18px 0 2px;opacity:.85;text-transform:uppercase;}
.fpl-pitch .bench{background:rgba(0,0,0,.16);border-radius:12px;padding:10px 6px;margin-top:2px;}
.fpl-pitch .kit{position:relative;}
.fpl-pitch .kit:hover{z-index:40;}
.fpl-pitch .kit-pop{position:absolute;left:50%;top:calc(100% + 6px);transform:translateX(-50%);
width:250px;max-width:76vw;display:none;z-index:40;text-align:left;cursor:default;}
.fpl-pitch .kit:hover .kit-pop{display:block;}
.fpl-pitch .kit-pop .pl-card{margin:0;}
</style>
"""

# Sub role → the short badge text on a bench kit (US-258): the auto-sub priority number, or "GK" for the
# keeper (it only ever replaces the starting keeper). ADR-078/079.
_SUB_BADGE = {"1st": "1", "2nd": "2", "3rd": "3", "4th": "4", "GK": "GK"}


# The tap styling (ADR-133; link states learned the hard way 2026-08-25).
#
# **Every link state must be pinned.** The click component renders inside an iframe that ships
# `bootstrap.min.css`, which styles `a:visited` blue-and-underlined — so the card you had just clicked turned
# into a visible hyperlink while every other card looked fine. Styling only the base `a` state is not enough
# inside someone else's CSS. This survived the ADR-135 revert because it is a genuine bug fix, not part of the
# menu that was reverted.
_TAP_CSS = """
<style>
.kit-a,.kit-a:link,.kit-a:visited,.kit-a:hover,.kit-a:active,.kit-a:focus{
text-decoration:none!important;color:inherit!important;display:block;}
.kit.selected{outline:2px solid #5eead4;outline-offset:2px;border-radius:10px;z-index:41;}
/* The selected player's compact card, in place under his shirt (ADR-139 rev). Only the selected kit carries
   a .kit-pop at all on a clickable pitch, so this can never open two at once — which is what the hover did. */
.kit.selected .kit-pop{display:block;}
/* US-444 rev — a full-bleed anchor BEHIND the shirts. Tapping the grass returns a different id from the last
   shirt, which is the only way a "close it" gesture can reach us at all (see tap.CLEAR_ID).

   Two mistakes to not make again, both shipped once (US-450):
   * **No `z-index` on `.row`.** It creates a stacking context per row, which traps `.kit-pop`'s `z-index:40`
     *inside* that row — so a card opened on the defenders rendered BEHIND the midfielders' shirts. `.kit` is
     already `position:relative`, so the rows need nothing: positioned descendants paint in tree order, and
     the anchor is first in the DOM.
   * **`pointer-events` matter more than paint order here.** A `.row` is a full-width flex container, so it
     covers the grass either way and swallowed every tap meant for the anchor beneath — which is why "tap the
     pitch to close" did nothing. The rows pass clicks through; the shirts take their own. */
.fpl-pitch{position:relative;}
.fpl-pitch .pitch-bg{position:absolute;inset:0;z-index:0;display:block;}
.fpl-pitch .row{pointer-events:none;}
.fpl-pitch .kit{pointer-events:auto;}
</style>
"""


_SHIRT_WEEKS = 3          # per-gameweek figures that fit under a 104px kit card (ADR-179)


def _kit_html(player, *, captain_id, xp_by_id, photos, next_opp, team_names=None, sub_role=None,
              vice_captain_id=None, market=False, per_gw_xp=None,
              fixtures_by_id=None, kits=None, clickable=False, selected=False) -> str:
    """One player's kit card (ADR-084) — image (with a **C** captain armband + a **sub-number** badge overlaid)
    · name · xP chip · £ · next opponent · crowd/set-piece flags. A 👕 placeholder if even the shirt is missing.
    Every text value is HTML-escaped so a name with `&`/`<`/`'` can't break the markup.

    The **pitch image is the live club kit** (`kits`, ADR-084 rev 2026-08-22) — transfer-proof, like FPL's own
    pitch — while the **hover card keeps the mugshot** (`photos`), which self-heals when FPL refreshes it. Falls
    back to `photos` for the kit when no `kits` map is passed (older callers/tests)."""
    e = html.escape
    photo = photos.get(player["id"], "")                       # the mugshot — for the hover card (US-255)
    kit = (kits if kits is not None else photos).get(player["id"], "")   # the pitch kit — the live club shirt
    # A neutral 👕 placeholder if even the kit is missing (no team code) — never a crash.
    pic = f'<img src="{e(kit)}" alt="">' if kit else '<div class="noimg">👕</div>'
    if player["id"] == captain_id:
        pic += '<span class="c-badge" title="Captain">C</span>'
    elif player["id"] == vice_captain_id:
        # `elif`: a player cannot be both, and if a stale squad says so the captain wins — the badge that
        # changes the score should never be the one that gets hidden.
        pic += '<span class="v-badge" title="Vice-captain — plays if your captain does not">V</span>'
    if sub_role:
        pic += (f'<span class="s-badge" title="{e(sub_role)} sub">'
                f'{e(_SUB_BADGE.get(sub_role, sub_role))}</span>')
    xp = round(xp_by_id.get(player["id"], 0), 1)
    opp = next_opp.get(player["team"])
    opp_str = f'{e(opp["opponent"])} ({e(opp["venue"])})' if opp else "—"
    meta = f'£{player["price"]:.1f}m · {opp_str}'
    # ADR-178 — **set-piece glyphs only, and no words**. The pitch used to carry `crowd_flags` too, which put
    # up to six labelled flags under a 104px name and wrapped them over three lines. Two reasons they went:
    # every player carries at least one (the ownership tier always fires, so the pitch was never clean), and
    # the market flags are a **third copy** of things already on the page *by name* — the price line under the
    # pitch, the Flagged availability line, and the Trending / Signals pages. The shirt was the only copy that
    # could not say *why*. Set pieces stay because they describe the player's **role**, not the market.
    #
    # The meaning rides as a `title` (a desktop hover), and `render_pitch` prints the key underneath for phones.
    # ADR-179 — `market=True` adds the crowd glyphs (the Lab). My Squad stays role-only: the flags left it
    # because it is read on a phone minutes before a deadline, and none of that is true of a page you sit with
    # while choosing players. Same rule — glyphs plus a key — different set, because the pages differ in
    # purpose. (ADR-178 generalised that justification into a rule about widget type, one level too high.)
    glyphs = (crowd_glyphs(player) if market else []) + set_piece_glyphs(player)
    flags_html = ""
    if glyphs:
        spans = "".join(f'<span title="{e(meaning)}">{glyph}</span>' for glyph, meaning in glyphs)
        flags_html = f'<div class="flags">{spans}</div>'

    # ADR-179 — up to three per-gameweek figures under the chip, where the caller asks for them (the Lab).
    # **Three because the card is 104px wide** and a fourth wraps — the table alongside carries five, since a
    # table scrolls. One cap per surface, each from that surface's real limit rather than one number for both.
    weeks_html = ""
    if per_gw_xp:
        weeks = [per_gw_xp.get(gw) for gw in sorted(per_gw_xp)][:_SHIRT_WEEKS]
        shown = " · ".join("—" if v is None else f"{v:.1f}" for v in weeks)
        weeks_html = f'<div class="weeks" title="Projected points, gameweek by gameweek">{e(shown)}</div>'

    # On hover: a compact player card (US-344). Reuses the card renderer (CSS is on the page once). ADR-109: when a
    # per-GW `fixtures_by_id` is supplied, the popover carries the **per-GW row** (xP over fixture, up to 3 GWs) —
    # the tester's card-under-the-shirt. `card_body` html-escapes its own values.
    pid = player["id"]
    pop = card_body(player, team_name=(team_names or {}).get(player["team"], player["team"]),
                    photo_url=photo or None, fixtures=(fixtures_by_id or {}).get(pid),
                    projected_xp=xp_by_id.get(pid), compact=True)
    # ADR-139 rev — the compact card is back on a tappable pitch, shown for the **selected** player (owner,
    # 2026-08-26: *"previously we had a hover that showed a smaller, condensed version on the pitch under the
    # player — I would like it back when you click, as well as the detailed version in the panel below"*).
    #
    # The distinction that makes this safe, and that ADR-139 got wrong by removing it outright: **what was
    # broken was the trigger, not the card.** On *hover* the popover followed the cursor across every shirt
    # independently of the selection, so one player's stats appeared beside another player's selection. Bound
    # to the selection instead, **exactly one is ever open**, it is always the player you chose, and it costs
    # no extra round-trip because the selection already happened.
    #
    # Three states, one condition:
    #   not clickable            → hover, unchanged (Squad Lab's preview, and the ADR-133 fallback)
    #   clickable + selected     → shown in place, under that shirt
    #   clickable + not selected → nothing, so neighbours cannot collide with it
    pop_html = f'<div class="kit-pop">{pop}</div>' if pop and (not clickable or selected) else ""
    body = (f'<div class="pic">{pic}</div>'
            f'<div class="name">{e(player["web_name"])}</div>'
            f'<div class="xp">{xp}</div>{weeks_html}'
            f'<div class="meta">{meta}</div>{flags_html}{pop_html}')
    if not clickable:
        return f'<div class="kit">{body}</div>'

    # ADR-133/135: a tappable card is an anchor over the body (`sel:`), and — only when this card is the
    # **selected** one — a row of action anchors beside it. They must be SIBLINGS: HTML forbids <a> inside <a>,
    # so wrapping the whole card and nesting the actions would silently break the outer anchor.
    #
    # Actions appear on the selected card alone. Putting them on all fifteen would trade page height for pitch
    # noise, which is the opposite of the point (ADR-135).
    # ADR-135 REVERTED (2026-08-25): the action menu is gone. Tapping selects (ADR-133) and the actions live in
    # the panel below, where a click costs the same round-trip without a floating menu, hover collisions, or a
    # two-tap flow costing two of them. The selected **outline** stays — it is purely visual, tells you which
    # card the picker refers to, and was the one part of ADR-135 nothing went wrong with.
    sel_cls = " selected" if selected else ""
    return f'<div class="kit{sel_cls}"><a href="#" id="sel:{pid}" class="kit-a">{body}</a></div>'


def pitch_html(xi, bench, *, captain_id, xp_by_id, photos, next_opp, team_names=None, bench_roles=None,
               vice_captain_id=None, market=False, per_gw_by_id=None,
               fixtures_by_id=None, kits=None, clickable=False, selected_id=None) -> str:
    """Build the pitch markup (ADR-084) — see `render_pitch` for the arguments.

    Split out from the renderer (ADR-133) because a tappable pitch has to *hand the HTML to a component* rather
    than write it to the page, and there was previously no way to get at it. `clickable` wraps each kit card in
    an anchor carrying the player id.

    `selected_id` outlines one card, so it is visible which player the picker below refers to.
    """
    kw = dict(captain_id=captain_id, vice_captain_id=vice_captain_id, market=market,
              xp_by_id=xp_by_id, photos=photos, next_opp=next_opp, team_names=team_names,
              fixtures_by_id=fixtures_by_id, kits=kits, clickable=clickable)

    def _kit(p, **extra):
        return _kit_html(p, selected=(selected_id is not None and p["id"] == selected_id),
                         per_gw_xp=(per_gw_by_id or {}).get(p["id"]), **kw, **extra)
    parts = [_PITCH_CSS, CARD_CSS, '<div class="fpl-pitch">']    # the card CSS once, for the per-kit hover popovers
    if clickable:
        # Behind everything, so it only receives taps that missed a shirt (US-444 rev).
        parts.append('<a href="#" id="sel:clear" class="pitch-bg" aria-label="Close the player card"></a>')

    for pos in _ROWS:
        line = [p for p in xi if p["position"] == pos]
        if not line:
            continue
        cells = "".join(_kit(p) for p in line)
        parts.append(f'<div class="row">{cells}</div>')

    if bench:
        if bench_roles:
            ordered = sorted(bench, key=lambda p: _ROLE_ORDER.get(bench_roles.get(p["id"]), 9))
        else:
            ordered = sorted(bench, key=lambda p: _ORDER.get(p["position"], 9))
        cells = "".join(_kit(p, sub_role=(bench_roles or {}).get(p["id"])) for p in ordered)
        parts.append(f'<div class="bench-label">Bench</div><div class="row bench">{cells}</div>')

    parts.append("</div>")
    if clickable:
        parts.insert(0, _TAP_CSS)
    return "".join(parts)


def set_piece_key(players) -> str:
    """The legend for the glyphs on the shirts — or `""` when no shirt carries one (ADR-178).

    Owner: *"have a key at the bottom of the pitch to remind users what they mean, for both My Squad and the
    Lab."* It lives here rather than in each caller so both pages get it from one place and cannot drift, and
    it is built from `SET_PIECES` — the same table the glyphs come from, so the key cannot teach a mapping the
    table contradicts.

    **Empty when nothing is flagged**, because the sentence ends *"blank = not on set pieces"*, which says
    nothing on a pitch where every shirt is blank — a legend explaining an absent thing is noise.

    Returned rather than rendered so the condition is testable: as an `if` inside the render call, a guard
    could only assert the source text, and a mutation to `if False` sailed through exactly that.
    """
    if not any(set_piece_glyphs(p) for p in players or []):
        return ""
    return ("Set pieces: "
            + " · ".join(f"{glyph} {long}" for _field, glyph, _short, long in SET_PIECES)
            + " — shown for the **first-choice** taker (blank = not on set pieces).")


def pitch_key(players, *, market=False) -> str:
    """The key beneath a pitch — the set-piece line, plus the market lines when the pitch shows them.

    ADR-179 splits the *set* by page while keeping the *rule* the same: both pitches render bare glyphs and
    explain them underneath. My Squad gets the role line; the Lab gets ownership and momentum as well.

    ⚠️ **Ownership is written as an ordered scale — `💎 → ⭐ → 🟦 → 👑` — and that is the point.** ADR-178
    argued against these as glyphs precisely because four tiers drawn as four unrelated pictures teach
    nothing; as a scale the key teaches the ranking, which is the part that could not be learned. It is why
    the Lab can afford twelve symbols where My Squad could not afford seven.
    """
    role = set_piece_key(players)
    if not market:
        return role
    # The market lines are unconditional on a market pitch: unlike set pieces, every player carries an
    # ownership tier, so there is no "nobody is flagged" case for them to be noise in.
    return f"{CROWD_KEY}  \n{role}" if role else CROWD_KEY


def render_pitch(xi, bench, *, captain_id, xp_by_id, photos, next_opp, team_names=None, bench_roles=None,
                 vice_captain_id=None, market=False, per_gw_by_id=None,
                 fixtures_by_id=None, kits=None) -> None:
    """Lay out the XI by formation rows + a bench strip, each player a kit card (ADR-084).

    ⚠️ **`vice_captain_id` is threaded here deliberately (ADR-179).** `_kit_html` has drawn the V badge since
    it was added, and `pitch_html` forwarded it — but *this* function, the plain renderer between them, never
    took the argument. Two things followed. Every surface drawing through `render_pitch` silently lost the
    badge (the owner found it in the Lab). And ADR-133's degrade path, which falls back to
    `render_pitch(**kw)` when the click-detector component is absent, passed `vice_captain_id` into a function
    that did not accept it — so My Squad **raised** instead of degrading, on exactly the path whose purpose is
    that *"a missing component never takes the page down"*.

    `xi` / `bench` are player rows; `next_opp` maps a team short_name → its next fixture cell
    (`{opponent, venue, ...}`) or None. `bench_roles` (US-246) maps id → sub role ("1st"/"2nd"/"3rd"/"GK");
    when given, the bench is ordered by that priority. `kits` (id → club-shirt URL, `shirt_url_by_id`) draws the
    **live club kit** on the pitch (transfer-proof); the hover card keeps the mugshot (`photos`). Emits one
    self-contained HTML/CSS block (no JS) — display-only; the edit controls live on the page.
    """
    st.markdown(pitch_html(xi, bench, captain_id=captain_id, vice_captain_id=vice_captain_id,
                           market=market, per_gw_by_id=per_gw_by_id,
                           xp_by_id=xp_by_id, photos=photos,
                           next_opp=next_opp, team_names=team_names, bench_roles=bench_roles,
                           fixtures_by_id=fixtures_by_id, kits=kits), unsafe_allow_html=True)
    if key := pitch_key(list(xi) + list(bench), market=market):
        st.caption(key)
