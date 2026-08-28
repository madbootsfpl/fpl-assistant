"""Shared presentational primitives — the stat strip and the banner (ADR-163).

Both exist because the same thing was being decided per page, and per-page decisions drift. The owner found
the drift from the outside: *"On iPhone the xP for XI, Captain and Bench wraps… same with transfer flow and
head to head on Leagues"*, and *"should the blue banner be more like the other MADBOOTS banners"*.

**Why a stat strip is HTML and not `st.metric` in `st.columns`.** Streamlit columns are laid out server-side
with a fixed ratio, so a 3- or 4-across row keeps its shape at any width: on a phone each column narrows until
the *label* wraps, and a strip meant to be scanned in one glance becomes a tall ragged block. Nothing on the
Python side can fix that, because nothing on the Python side knows the viewport. CSS does — `flex-wrap` lets
the items reflow and `clamp()` lets the numbers shrink — so the strip has to be rendered, not composed.

This has been worked around before rather than fixed: US-404 cut a 5-metric row to 3 because it *"slivered on
mobile"*. That made the symptom smaller and left the mechanism in place, which is why it came back the moment
two more strips were added (ADR-161's head-to-head and ADR-162's transfer flow).

**The tradeoff, stated.** `st.metric(help=…)` renders a tappable "?" that this cannot reproduce; help here is
a `title` attribute — a hover tooltip on desktop, nothing on touch. Accepted because the help text on these
strips explains a number that is *already* labelled, whereas the wrapping made the number itself hard to read.
Anything a reader genuinely needs goes in the caption beneath, not in a tooltip.
"""

import html as _html

# Matches the existing dark-card idiom (`.yt-strip`, `.tr-card`) rather than inventing a third look: same
# gradient ground, same purple border, same uppercase micro-label.
_CSS = """
<style>
.mb-strip{display:flex;flex-wrap:wrap;gap:10px;background:linear-gradient(180deg,#141b28,#0e141f);
border:1px solid rgba(139,47,201,.45);border-radius:14px;padding:12px 14px;margin:.4rem 0;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
/* flex-basis is the whole point: each item asks for ~150px and wraps when it can't have it, so three across
   on a laptop becomes two-and-one, then one, as the screen narrows — without a media query per breakpoint. */
.mb-strip .mb-item{flex:1 1 150px;min-width:0;display:flex;flex-direction:column;gap:3px;}
.mb-strip .mb-l{color:#8b98a9;font-size:.66rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.mb-strip .mb-l[title]{cursor:help;border-bottom:1px dotted rgba(139,152,169,.5);align-self:flex-start;}
/* clamp() is the second half: the value shrinks with the viewport instead of wrapping onto a second line. */
.mb-strip .mb-v{color:#f2f6fb;font-weight:800;font-variant-numeric:tabular-nums;line-height:1.15;
font-size:clamp(1.05rem,4.2vw,1.55rem);}
.mb-strip .mb-v.up{color:#5eead4;} .mb-strip .mb-v.down{color:#f98a8a;} .mb-strip .mb-v.mute{color:#8b98a9;}
.mb-strip .mb-s{color:#7c8899;font-size:.68rem;font-weight:600;}

.mb-banner{display:flex;gap:10px;align-items:flex-start;background:linear-gradient(180deg,#141b28,#0e141f);
border:1px solid rgba(139,47,201,.45);border-left-width:4px;border-radius:12px;padding:11px 14px;margin:.4rem 0;
color:#e8eef6;font-size:.9rem;line-height:1.5;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.mb-banner .mb-ico{font-size:1.05rem;line-height:1.35;}
.mb-banner.signal{border-left-color:#B45CF0;} .mb-banner.good{border-left-color:#5eead4;}
.mb-banner.warn{border-left-color:#FF6A00;} .mb-banner.bad{border-left-color:#f98a8a;}
.mb-banner b{color:#fff;}
</style>
"""

_TONES = ("up", "down", "mute")
_KINDS = ("signal", "good", "warn", "bad")


def stat_strip_html(items) -> str:
    """A responsive row of label/value stats — `[{"label", "value", "help"?, "tone"?, "sub"?}]`.

    Wraps and shrinks instead of slivering, which is the whole reason it exists. `tone` colours the value
    (`up` / `down` / `mute`); `sub` adds a small line beneath it. Returns `""` for no items, so a caller can
    hand it a list it did not check.
    """
    if not items:
        return ""
    cells = []
    for it in items:
        label = _html.escape(str(it.get("label", "")))
        value = _html.escape(str(it.get("value", "—")))
        tone = it.get("tone") if it.get("tone") in _TONES else ""
        help_text = it.get("help")
        title = f' title="{_html.escape(str(help_text))}"' if help_text else ""
        sub = f'<span class="mb-s">{_html.escape(str(it["sub"]))}</span>' if it.get("sub") else ""
        cells.append(f'<div class="mb-item"><span class="mb-l"{title}>{label}</span>'
                     f'<span class="mb-v {tone}">{value}</span>{sub}</div>')
    return _CSS + f'<div class="mb-strip">{"".join(cells)}</div>'


def banner_html(text, *, kind: str = "signal", icon: str = "") -> str:
    """One MADBOOTS-styled banner — the house alternative to `st.info`'s stock blue box.

    `text` is **trusted markup**, not escaped: every caller composes it from our own strings and the callers
    that matter carry `<b>` emphasis. Never pass user input through here.

    Deliberately *not* applied app-wide. Sixty-odd `st.info`/`st.warning` calls exist, and converting them all
    on a styling preference would be a large blind change to error and empty states — the owner asked for this
    *"for discussion"*, so it lands where they pointed (Signals) and the rest waits for a look at it.
    """
    if not text:
        return ""
    kind = kind if kind in _KINDS else "signal"
    ico = f'<span class="mb-ico">{_html.escape(icon)}</span>' if icon else ""
    return _CSS + f'<div class="mb-banner {kind}">{ico}<div>{text}</div></div>'


def render_stat_strip(items) -> None:
    """`stat_strip_html` straight to the page — the common case."""
    import streamlit as st
    markup = stat_strip_html(items)
    if markup:
        st.markdown(markup, unsafe_allow_html=True)


def render_banner(text, *, kind: str = "signal", icon: str = "") -> None:
    import streamlit as st
    markup = banner_html(text, kind=kind, icon=icon)
    if markup:
        st.markdown(markup, unsafe_allow_html=True)
