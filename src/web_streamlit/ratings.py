"""A relative quality rating for the stat boards (ADR-071) — display-only.

Casual users asked what a raw stat means ("is xGC/90 0.52 good, or just relative?"). The honest answer:
these are absolute season values, but *good* is judged **against peers** — and a fixed absolute band
copied from a generic scale mislabels almost every FPL player (real xGC/90 clusters ~1.1–1.5). So we rate
**relative to the players currently shown**: a value's rank in that pool picks a quintile colour, and the
percentile ("top N%") anchors it. Self-calibrating (no thresholds to maintain; correct at GW1 too).

Web-side on purpose — this is presentation policy (pool-relative, a vocabulary), so the analytics core
stays pure. `higher_is_better` flips the direction (xGI: higher good; xGC/90: lower good).
"""

# Quintile → (upper fraction-beaten edge, emoji, word). Best 20% first; the last edge (>1) catches the rest.
_BANDS = [(0.2, "🟢", "excellent"), (0.4, "🟢", "good"), (0.6, "🟡", "average"),
          (0.8, "🟠", "poor"), (1.01, "🔴", "very poor")]

LEGEND = "Rating is **relative to the players shown** — 🟢 best 20% · 🟡 middle · 🔴 worst 20%."


def quality_band(value, pool, *, higher_is_better: bool) -> dict:
    """Rate `value` within `pool` (the metric's values currently shown).

    Returns ``{emoji, label, percentile}``. `percentile` reads "top N%" — the share of the field this
    value beats *is not* the point; N is the share that beats it (so the best reads "top 1%"). Ties share
    a band (equal 'strictly better' counts). An empty pool yields blanks.
    """
    n = len(pool)
    if n == 0:
        return {"emoji": "", "label": "", "percentile": ""}
    if higher_is_better:
        better = sum(1 for v in pool if v > value)
    else:
        better = sum(1 for v in pool if v < value)
    frac = better / n
    emoji, label = _BANDS[-1][1], _BANDS[-1][2]
    for edge, e, lab in _BANDS:
        if frac < edge:
            emoji, label = e, lab
            break
    return {"emoji": emoji, "label": label, "percentile": f"top {max(1, round(frac * 100))}%"}


def rating_cell(value, pool, *, higher_is_better: bool) -> str:
    """A dataframe cell: '🟢 excellent (top 8%)' — the colour band + the inline percentile (ADR-071)."""
    b = quality_band(value, pool, higher_is_better=higher_is_better)
    return f"{b['emoji']} {b['label']} ({b['percentile']})" if b["emoji"] else ""
