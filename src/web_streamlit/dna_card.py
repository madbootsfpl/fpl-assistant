"""The Player DNA radar — a self-contained SVG rendering of the percentile fingerprint (Sprint 168, ADR-118).

Server-built **SVG**, not canvas+JS: `st.markdown(..., unsafe_allow_html=True)` does **not** execute `<script>`,
so the geometry (the polygon vertices, spokes and labels) is computed here in Python and emitted as static markup —
which is also pure and testable. Dark card styling to sit under the player card (ADR-084). Display-only: it draws
what `analytics.player_dna` computed and changes nothing.
"""

import math

import streamlit as st

from src.web_streamlit import brand

# Percentile bands → a (background, text) pair for the vertex dots + chips (dark text on a bright fill = legible;
# the approved preview's palette). ≥85 elite (green) · 60–84 strong (teal) · <60 below par (amber) · None muted.
_BAND = {
    "hi": ("#01fc7a", "#08331f"),
    "mid": (brand.ACCENT_TEAL, "#08403a"),
    "lo": ("#ffb020", "#3d2a00"),
    "na": ("#3a4150", "#c7ceda"),
}

_POS_LABEL = {"GK": "goalkeepers", "DEF": "defenders", "MID": "midfielders", "FWD": "forwards"}

DNA_CSS = """
<style>
.dna-card{background:linear-gradient(180deg,#111821,#0c121a);border:1px solid rgba(255,255,255,.09);
border-radius:18px;color:#f2f6fb;margin:.5rem 0;padding:16px 18px 18px;
box-shadow:0 18px 40px -22px rgba(0,0,0,.7);
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}
.dna-card .dna-band{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:6px;}
.dna-card .dna-ttl{font-weight:800;font-size:.72rem;letter-spacing:.08em;color:#aab6c6;text-transform:uppercase;}
.dna-card .dna-cap{color:#7c8899;font-size:.78rem;font-weight:600;}
.dna-card .dna-svg{display:block;width:100%;max-width:420px;height:auto;margin:2px auto 4px;}
.dna-card .dna-note{color:#f6a13a;font-size:.74rem;font-weight:600;margin:2px 2px 8px;}
.dna-card .dna-chips{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:6px;}
.dna-unranked{border:1px dashed rgba(255,255,255,.16);border-radius:12px;padding:20px 16px;text-align:center;
color:#8c93a3;font-size:.85rem;line-height:1.5;}
.dna-card .dna-chip{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);
border-radius:10px;padding:7px 9px;min-width:0;}
.dna-card .dna-cl{font-size:.7rem;color:#aab6c6;line-height:1.15;}
.dna-card .dna-cs{color:#7c8899;font-size:.62rem;}
.dna-card .dna-cv{display:flex;align-items:center;gap:6px;margin-top:4px;}
.dna-card .dna-pct{font-size:.72rem;font-weight:800;border-radius:6px;padding:1px 6px;
font-variant-numeric:tabular-nums;}
.dna-card .dna-raw{color:#aab6c6;font-size:.7rem;font-weight:600;font-variant-numeric:tabular-nums;}
@media(max-width:520px){.dna-card .dna-chips{grid-template-columns:repeat(2,1fr);}}
</style>
"""


def _band(pct) -> tuple[str, str]:
    if pct is None:
        return _BAND["na"]
    if pct >= 85:
        return _BAND["hi"]
    if pct >= 60:
        return _BAND["mid"]
    return _BAND["lo"]


def _pt(cx, cy, r, theta):
    return cx + math.cos(theta) * r, cy + math.sin(theta) * r


def radar_svg(axes, *, label: str = "", size: int = 360) -> str:
    """A standalone `<svg>` radar for a list of `Axis`es (Player **or** Team DNA — same builder) — octagon rings,
    spokes, labelled axes, the percentile polygon (brand purple→teal), and a band-coloured dot at each vertex.
    Pure geometry; no script."""
    # An unranked axis (percentile None) used to plot at `(ax.percentile or 0)` — the centre — so a pool too
    # small to rank anyone drew a fingerprint collapsed to a spike through whichever axis *could* be ranked.
    # A shape built mostly from missing data is a lie; say there is nothing to draw instead (ADR-118/126).
    if sum(1 for a in axes if a.percentile is not None) < 3:
        return ('<div class="dna-unranked">Not enough games played to rank this player yet — the fingerprint '
                'needs a pool of peers to compare against.</div>')
    n = len(axes)
    cx = cy = size / 2
    R = size / 2 - 74                      # leave a margin for the axis labels
    parts = [
        f'<svg class="dna-svg" viewBox="0 0 {size} {size}" role="img" '
        f'aria-label="percentile radar for {_esc(label)}">',
        '<defs><linearGradient id="dnaFill" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{brand.PURPLE}" stop-opacity="0.55"/>'
        f'<stop offset="1" stop-color="{brand.ACCENT_TEAL}" stop-opacity="0.38"/></linearGradient></defs>',
    ]

    def ring(frac):
        pts = " ".join(f"{x:.1f},{y:.1f}" for i in range(n)
                       for x, y in [_pt(cx, cy, R * frac, -math.pi / 2 + i * 2 * math.pi / n)])
        return f'<polygon points="{pts}" fill="none" stroke="rgba(255,255,255,.10)" stroke-width="1"/>'

    parts += [ring(f) for f in (0.25, 0.5, 0.75, 1.0)]

    # spokes + axis labels
    for i, ax in enumerate(axes):
        theta = -math.pi / 2 + i * 2 * math.pi / n
        ex, ey = _pt(cx, cy, R, theta)
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                     'stroke="rgba(255,255,255,.10)" stroke-width="1"/>')
        lx, ly = _pt(cx, cy, R + 20, theta)
        cos, sin = math.cos(theta), math.sin(theta)
        anchor = "middle" if abs(cos) < 0.3 else ("start" if cos > 0 else "end")
        dy = 4 if abs(sin) < 0.3 else (14 if sin > 0 else -6)
        parts.append(f'<text x="{lx:.1f}" y="{ly + dy:.1f}" text-anchor="{anchor}" '
                     f'fill="#cdd6e2" font-size="11" font-weight="700" '
                     f'font-family="sans-serif">{_esc(ax.label)}</text>')
        parts.append(f'<text x="{lx:.1f}" y="{ly + dy + 12:.1f}" text-anchor="{anchor}" '
                     f'fill="#7c8899" font-size="9" font-family="sans-serif">{_esc(ax.sublabel)}</text>')

    # the data polygon (percentile → radius) + vertices
    poly = []
    for i, ax in enumerate(axes):
        theta = -math.pi / 2 + i * 2 * math.pi / n
        # A still-unranked axis sits on the ring rather than at the centre: absent evidence is not a zero
        # score. The vertex dot below renders it hollow so it reads as "unknown", not "average".
        frac = 0.5 if ax.percentile is None else ax.percentile / 100.0
        poly.append(_pt(cx, cy, R * frac, theta))
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)
    parts.append(f'<polygon points="{pts}" fill="url(#dnaFill)" '
                 f'stroke="{brand.PURPLE_LT}" stroke-width="2" stroke-linejoin="round"/>')
    for (x, y), ax in zip(poly, axes):
        if ax.percentile is None:                     # hollow = unranked, distinct from a genuine low score
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="none" '
                         'stroke="#7c8899" stroke-width="1.5" stroke-dasharray="2 2"/>')
            continue
        bg, _fg = _band(ax.percentile)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{bg}" '
                     'stroke="#0c121a" stroke-width="1.5"/>')

    parts.append("</svg>")
    return "".join(parts)


def _esc(s) -> str:
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _chip(ax) -> str:
    bg, fg = _band(ax.percentile)
    pct = "—" if ax.percentile is None else f"{ax.percentile}"
    raw = ax.value
    raw_str = f"{raw:,.0f}" if abs(raw) >= 100 else f"{raw:g}"
    return (f'<div class="dna-chip"><div class="dna-cl">{_esc(ax.label)}'
            f'<br><span class="dna-cs">{_esc(ax.sublabel)}</span></div>'
            f'<div class="dna-cv"><span class="dna-pct" style="background:{bg};color:{fg}">{pct}</span>'
            f'<span class="dna-raw">{raw_str}</span></div></div>')


def dna_card_html(dna) -> str:
    """The full DNA card: the radar + a caption + a chip per axis (label · sublabel · percentile · raw)."""
    pos = _POS_LABEL.get(dna.position, "players")
    cap = f"Percentile rank among {pos} · vs {dna.pool_size} with real minutes"
    note = ('<div class="dna-note">⚠ Limited minutes — read the shape with care.</div>'
            if dna.low_minutes else "")
    chips = "".join(_chip(a) for a in dna.axes)
    return (DNA_CSS + '<div class="dna-card">'
            '<div class="dna-band"><span class="dna-ttl">🧬 Player DNA</span>'
            f'<span class="dna-cap">{_esc(cap)}</span></div>'
            f'{radar_svg(dna.axes, label=dna.name)}{note}<div class="dna-chips">{chips}</div></div>')


def render_dna_card(dna) -> None:
    """Render a `PlayerDNA` as the radar card (no-op if `dna` is None)."""
    if dna is None:
        return
    st.markdown(dna_card_html(dna), unsafe_allow_html=True)


# ── Compare: two fingerprints on one radar (ADR-197) ─────────────────────────────────────────────────
#
# Owner: *"could we do a compare DNA for both Team & a Player. For Player it's an extension of Boot Battle and
# should include Performance trend too."*
#
# ⚠️ **Two polygons, one octagon — not two radars side by side.** The whole value of a fingerprint comparison
# is the *shape difference*, and two separate charts make the reader do the overlay in their head, which is
# exactly the work Boot Battle already does for them stat by stat.
#
# ⚠️ **And deliberately NO verdict** (owner-agreed). Each player has one on their own DNA page; putting two
# side by side would read as a ranking the model has not earned — the same overclaim ADR-194 had just removed
# from the lineup. The shapes compare; the reader concludes.
_A_STROKE, _B_STROKE = brand.PURPLE_LT, brand.ACCENT_TEAL


def _poly_points(axes, cx, cy, R, n):
    out = []
    for i, ax in enumerate(axes):
        theta = -math.pi / 2 + i * 2 * math.pi / n
        frac = 0.5 if ax.percentile is None else ax.percentile / 100.0
        out.append(_pt(cx, cy, R * frac, theta))
    return out


def radar_compare_svg(a_axes, b_axes, *, a_label: str, b_label: str, size: int = 360) -> str:
    """Two percentile fingerprints overlaid on one octagon, with a legend. Player **or** Team — same builder as
    `radar_svg`, same axis order, same unranked rule.

    ⚠️ **An axis either side may be unranked, and they need not be the same axis.** A single radar sits an
    unranked axis on the mid ring with a hollow dot (*absent evidence is not a zero*); with two shapes that
    would silently imply they were level there. Each unranked vertex is instead drawn hollow **in its own
    colour**, so a reader can see which of the two is missing evidence — the case that does not arise on a
    single radar and would otherwise be discovered on screen.
    """
    if min(sum(1 for a in ax if a.percentile is not None) for ax in (a_axes, b_axes)) < 3:
        return ('<div class="dna-unranked">Not enough games played to compare these two yet — a fingerprint '
                'needs a pool of peers on both sides.</div>')
    n = len(a_axes)
    cx = cy = size / 2
    R = size / 2 - 74                      # ⚠️ identical to `radar_svg` — owner: *"same size and thickness as
                                           # the original single club radar"*. Two charts of the same thing at
                                           # different scales read as two different charts.
    parts = [f'<svg class="dna-svg" viewBox="0 0 {size} {size}" role="img" '
             f'aria-label="percentile radar comparing {_esc(a_label)} and {_esc(b_label)}">']

    def ring(frac):
        pts = " ".join(f"{x:.1f},{y:.1f}" for i in range(n)
                       for x, y in [_pt(cx, cy, R * frac, -math.pi / 2 + i * 2 * math.pi / n)])
        return f'<polygon points="{pts}" fill="none" stroke="rgba(255,255,255,.10)" stroke-width="1"/>'

    parts += [ring(f) for f in (0.25, 0.5, 0.75, 1.0)]
    for i, ax in enumerate(a_axes):
        theta = -math.pi / 2 + i * 2 * math.pi / n
        ex, ey = _pt(cx, cy, R, theta)
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                     'stroke="rgba(255,255,255,.10)" stroke-width="1"/>')
        lx, ly = _pt(cx, cy, R + 20, theta)
        cos, sin = math.cos(theta), math.sin(theta)
        anchor = "middle" if abs(cos) < 0.3 else ("start" if cos > 0 else "end")
        dy = 4 if abs(sin) < 0.3 else (14 if sin > 0 else -6)
        parts.append(f'<text x="{lx:.1f}" y="{ly + dy:.1f}" text-anchor="{anchor}" fill="#cdd6e2" '
                     f'font-size="11" font-weight="700" font-family="sans-serif">{_esc(ax.label)}</text>')
        parts.append(f'<text x="{lx:.1f}" y="{ly + dy + 12:.1f}" text-anchor="{anchor}" fill="#7c8899" '
                     f'font-size="9" font-family="sans-serif">{_esc(ax.sublabel)}</text>')

    for axes, stroke in ((a_axes, _A_STROKE), (b_axes, _B_STROKE)):
        poly = _poly_points(axes, cx, cy, R, n)
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)
        parts.append(f'<polygon points="{pts}" fill="{stroke}" fill-opacity="0.16" stroke="{stroke}" '
                     'stroke-width="2" stroke-linejoin="round"/>')
        for (x, y), ax in zip(poly, axes):
            if ax.percentile is None:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="none" stroke="{stroke}" '
                             'stroke-width="1.5" stroke-dasharray="2 2"/>')
            else:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{stroke}" '
                             'stroke="#0c121a" stroke-width="1.5"/>')
    parts.append("</svg>")
    return "".join(parts)


COMPARE_CSS = (
    "<style>.dna-card .dna-legend{display:flex;gap:18px;justify-content:center;margin:-2px 0 8px;"
    "font-size:.8rem;color:#cdd6e2;font-weight:700;}"
    ".dna-card .dna-legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;"
    "vertical-align:-1px;}"
    # Two percentiles per chip, in the two shape colours, sharing one axis label — the single card's chip with
    # a second value rather than a table beside the chart (owner, 2026-09-16).
    ".dna-card .dna-cv2{display:flex;align-items:center;gap:10px;margin-top:4px;}"
    ".dna-card .dna-p2{font-size:.72rem;font-weight:800;border-radius:6px;padding:1px 7px;"
    "font-variant-numeric:tabular-nums;color:#0c121a;}</style>")


def _compare_chip(ax_a, ax_b) -> str:
    """One axis, both clubs — the single card's chip carrying two values instead of one.

    ⚠️ **This replaced a markdown table beside the radar** (owner: *"rather than a table could we use the
    legend as used in single club with the comparing club data alongside it"*). The table was a second reading
    order for the same eight facts the chart already showed, and on a phone it wrapped every cell onto three
    lines. The chip grid is the layout this page already uses, so a compare now looks like the thing it
    compares.

    The values are tinted by **shape colour, not by band** — in a comparison the question is *whose is this*,
    and the radar answers *how good* with position on the ring.
    """
    a = "—" if ax_a.percentile is None else f"{ax_a.percentile}"
    b = "—" if ax_b.percentile is None else f"{ax_b.percentile}"
    return (f'<div class="dna-chip"><div class="dna-cl">{_esc(ax_a.label)}'
            f'<br><span class="dna-cs">{_esc(ax_a.sublabel)}</span></div>'
            f'<div class="dna-cv2">'
            f'<span class="dna-p2" style="background:{_A_STROKE}">{a}</span>'
            f'<span class="dna-p2" style="background:{_B_STROKE}">{b}</span></div></div>')


def compare_card_html(a_axes, b_axes, *, a_label: str, b_label: str, title: str, caption: str) -> str:
    """The whole compare, inside the **same dark card** the single radar uses.

    ⚠️ **This is the phone bug, and it was a real one.** The radar's furniture is hard-coded for a dark ground
    — `rgba(255,255,255,.10)` rings, `#cdd6e2` labels, `#0c121a` dot outlines. The single card supplies that
    ground itself (`.dna-card`); the compare rendered the bare `<svg>`, so on a light-themed phone it sat on
    white with near-invisible labels while everything around it stayed dark (owner's screenshot, 2026-09-16).
    ⭐ *A component that hard-codes one theme's colours is not portable to a container that does not supply it.*
    """
    body = radar_compare_svg(a_axes, b_axes, a_label=a_label, b_label=b_label)
    if "dna-unranked" in body:                       # too thin to draw — the message carries the card itself
        return DNA_CSS + COMPARE_CSS + f'<div class="dna-card">{body}</div>'
    legend = (f'<div class="dna-legend">'
              f'<span><i style="background:{_A_STROKE}"></i>{_esc(a_label)}</span>'
              f'<span><i style="background:{_B_STROKE}"></i>{_esc(b_label)}</span></div>')
    chips = "".join(_compare_chip(x, y) for x, y in zip(a_axes, b_axes))
    return (DNA_CSS + COMPARE_CSS + '<div class="dna-card">'
            f'<div class="dna-band"><span class="dna-ttl">{_esc(title)}</span>'
            f'<span class="dna-cap">{_esc(caption)}</span></div>'
            f'{body}{legend}<div class="dna-chips">{chips}</div></div>')
