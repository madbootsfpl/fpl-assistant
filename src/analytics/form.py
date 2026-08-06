"""In-season form as a rolling points-per-90 (ADR-060) — the Data-Hardening form term.

Two pure pieces, dormant until GW1:

  form_rate(gw_history) — a recency- and minutes-weighted points-per-90 over the last N
                          gameweeks, mirroring `baseline_rate` (ADR-028) but *within* the
                          current season. Returns (form_pp90, confidence); (None, 0.0) when
                          the window holds no minutes (preseason, or a fully-benched run).
  blend_form(base, …)   — folds that form rate into the one xP rate: rate = (1−w)·base + w·form,
                          w = weight × confidence. weight 0 (dormant) or form None ⇒ base
                          unchanged — the invariant that keeps xP (ADR-041) stable until GW1.

Fed by `Storage.get_gw_history_by_code()`. No config import — the tunable weight/window are read
by `decision_xp` and passed in, so this stays a pure, standalone-testable unit.
"""

_FORM_GAMEWEEKS = 5     # default rolling window (the last N gameweeks); config may override
_FORM_MIN_MINUTES = 270  # minutes in the window for full confidence (~3 full matches)


def _field(row, key):
    """Read `key` from a sqlite Row or a dict, returning None if absent (mirrors xp._get)."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def form_rate(gw_history, k_gameweeks: int = _FORM_GAMEWEEKS, min_minutes: int = _FORM_MIN_MINUTES):
    """A recency- and minutes-weighted points-per-90 over the last `k_gameweeks` GWs (ADR-060).

    Only gameweeks with minutes > 0 count (a benched/absent GW carries no rate). Newer,
    higher-minutes gameweeks weigh more (as `baseline_rate` weights seasons). Returns
    `(form_pp90, confidence)` — `confidence = min(1, window_minutes / min_minutes)` scales the
    rate in by evidence so a cameo can't swing it. `(None, 0.0)` when the window has no minutes.
    """
    recent = [h for h in gw_history[-k_gameweeks:] if (_field(h, "minutes") or 0) > 0]
    if not recent:
        return None, 0.0
    num = den = 0.0
    window_minutes = 0
    for rank, h in enumerate(recent, start=1):    # oldest → 1 … newest → n (recency)
        mins = _field(h, "minutes") or 0
        pp90 = (_field(h, "total_points") or 0) * 90.0 / mins
        weight = rank * mins                      # newer + higher-minutes GWs weigh more
        num += weight * pp90
        den += weight
        window_minutes += mins
    return num / den, min(1.0, window_minutes / min_minutes)


def blend_form(base_rate: float, form_pp90, confidence: float, weight: float) -> float:
    """Blend the in-season form rate into the base xP rate (ADR-060).

        w    = weight × confidence
        rate = (1 − w) × base_rate + w × form_pp90

    `weight` 0 (dormant) or `form_pp90` None ⇒ `base_rate` returned unchanged — the invariant
    that keeps the one xP metric (ADR-041) stable until the GW1 flip.
    """
    if not weight or form_pp90 is None:
        return base_rate
    w = weight * confidence
    return (1.0 - w) * base_rate + w * form_pp90
