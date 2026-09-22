"""Comparing two players on their season stats — the engine behind **Boot Battle** (ADR-110/236).

⭐⭐ **Here rather than in `web_streamlit/player_card.py`, because the API needs it and that module imports
Streamlit.** The comparison is arithmetic over stored fields: which of two numbers is better, in the order
that matters for a position. None of that is a rendering concern, and the API cannot pull a web framework
into itself to ask the question.

⚠️ **Moved verbatim, not retyped.** ADR-222 reproduced a URL template from memory and dropped a `-66`
suffix — a value that was wrong and looked entirely plausible. ⭐ *A rule copied is a rule that can differ*,
and the whole point of this module is that there is one.

⚠️ **Lower is better for some stats** (`xgc`, goals conceded) — `_BETTER` is what knows that, and a naive
`max()` would confidently crown the worse defence.
"""

def _i(v):
    return f"{int(v):,}" if v is not None else None


def _f(v, dp):
    return f"{v:.{dp}f}" if v is not None else None


# The position-adaptive stat order (ADR-084); shared by the single card + the two-player compare (ADR-110).
_ORDER = {
    "FWD": ["pts", "ppg", "goals", "xgi", "xg", "own", "assists", "value", "xa", "ict", "mins", "def90"],
    "MID": ["pts", "ppg", "goals", "xgi", "assists", "own", "xa", "value", "def90", "ict", "mins", "recov"],
    "DEF": ["pts", "ppg", "xgc", "def90", "cbi", "own", "tackles", "value", "goals", "assists", "mins", "recov"],
    "GK": ["pts", "ppg", "xgc", "def90", "cbi", "own", "recov", "value", "mins"],
}
_ORDER_FALLBACK = ["pts", "ppg", "goals", "assists", "xgi", "own", "value", "mins"]

# Per-stat compare direction (ADR-110): "hi" = higher is better · "lo" = lower is better · None = neutral
# (ownership — differential vs template is a preference, not "better"; so it's never highlighted a winner).
_BETTER = {
    "pts": "hi", "ppg": "hi", "mins": "hi", "value": "hi", "own": None, "goals": "hi", "assists": "hi",
    "xg": "hi", "xa": "hi", "xgi": "hi", "xgc": "lo", "def90": "hi", "cbi": "hi", "tackles": "hi",
    "recov": "hi", "ict": "hi",
}


def _stat_catalog(player):
    """`{key: (label, raw, formatted)}` for every card stat — the **raw** numeric (for comparison) + the
    **formatted** string (for display, None when missing). Position-agnostic; the caller picks the order (ADR-110)."""
    p = dict(player)
    price = p.get("price") or 0
    pts = p.get("total_points")
    own = p.get("selected_by")
    value_raw = (pts / price) if (pts is not None and price) else None
    return {
        "pts": ("FPL Points", pts, _i(pts)),
        "ppg": ("Points / game", p.get("points_per_game"), _f(p.get("points_per_game"), 1)),
        "mins": ("Minutes", p.get("minutes"), _i(p.get("minutes"))),
        "value": ("Value", value_raw, f"{value_raw:.1f} pts/£m" if value_raw is not None else None),
        "own": ("Ownership", own, f"{own:.1f}%" if own is not None else None),
        "goals": ("Goals", p.get("goals_scored"), _i(p.get("goals_scored"))),
        "assists": ("Assists", p.get("assists"), _i(p.get("assists"))),
        "xg": ("Expected Goals", p.get("xg"), _f(p.get("xg"), 2)),
        "xa": ("Expected Assists", p.get("xa"), _f(p.get("xa"), 2)),
        "xgi": ("xG Involvement", p.get("xgi"), _f(p.get("xgi"), 2)),
        "xgc": ("Expected GC", p.get("xgc"), _f(p.get("xgc"), 2)),
        "def90": ("DefCon / 90", p.get("defcon_per90"), _f(p.get("defcon_per90"), 2)),
        "cbi": ("Clr + Blk + Int", p.get("cbi"), _i(p.get("cbi"))),
        "tackles": ("Tackles", p.get("tackles"), _i(p.get("tackles"))),
        "recov": ("Recoveries", p.get("recoveries"), _i(p.get("recoveries"))),
        "ict": ("ICT Index", p.get("ict_index"), _f(p.get("ict_index"), 1)),
    }


def _order_for(pos):
    return _ORDER.get((pos or "").upper(), _ORDER_FALLBACK)


def _stat_rows(player, *, compact=False):
    """(label, value) rows adapted to the player's **position** (ADR-084). Pure; skips missing values. Compact
    keeps the header-relevant few for the pitch popover."""
    cat = _stat_catalog(player)
    order = _order_for(player.get("position"))
    if compact:
        order = order[:4]                                    # fewer stats so the hover popover fits (US-346)
    return [(cat[k][0], cat[k][2]) for k in order if cat[k][2] is not None]


#: ⭐ Public name for the same function. `_stat_rows` stays as the card module's existing import, because
#: renaming it there would be churn in a file this change has no other business touching.
stat_rows = _stat_rows


def _winner(key, ra, rb):
    """"a"/"b"/None — which raw value wins for stat `key` (ADR-110 `_BETTER` direction). None on tie/missing/neutral."""
    d = _BETTER.get(key)
    if d is None or ra is None or rb is None or ra == rb:
        return None
    if d == "hi":
        return "a" if ra > rb else "b"
    return "a" if ra < rb else "b"                           # "lo" — lower is better (e.g. Expected GC)


def compare_rows(a, b):
    """Aligned same-position comparison rows (ADR-110): `[(label, a_formatted, b_formatted, winner)]` per stat in the
    shared position's order — `winner ∈ {"a","b",None}`; a missing side shows "—" with no winner. Assumes `a` and `b`
    share a position (the picker is scoped same-position)."""
    a, b = dict(a), dict(b)                                  # accept sqlite3.Row too (like card_body)
    ca, cb = _stat_catalog(a), _stat_catalog(b)
    rows = []
    for k in _order_for(a.get("position")):
        label, ra, fa = ca[k]
        _, rb, fb = cb[k]
        if fa is None and fb is None:
            continue
        rows.append((label, fa or "—", fb or "—", _winner(k, ra, rb)))
    return rows
