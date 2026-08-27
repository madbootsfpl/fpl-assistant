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

# The two windows a manager actually asks about (ADR-159): "how is he doing *now*" and "…compared with his
# recent run". 3 and 6 are FPL's own vernacular, not a fitted pair — there is no per-gameweek data to fit
# them on (at the time of writing, one gameweek has been played), and inventing a calibrated-sounding number
# on zero evidence is the failure this project keeps naming.
_SHORT_WINDOW = 3
_LONG_WINDOW = 6


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


def _played_in(rows, k) -> int:
    """How many of the last `k` gameweeks the player actually played, by the same minutes test `form_rate` uses."""
    return sum(1 for h in rows[-k:] if (_field(h, "minutes") or 0) > 0)


def form_windows(gw_history, *, short: int = _SHORT_WINDOW, long: int = _LONG_WINDOW,
                 min_minutes: int = _FORM_MIN_MINUTES) -> dict:
    """A short and a long rolling points-per-90, and the gap between them (ADR-159).

    One window says how a player is scoring; **two say which way he is going**, which is the question a single
    number cannot answer however well it is tuned. Both reuse `form_rate`, so the recency and minutes weighting
    is identical and the two are comparable by construction — a second rate written alongside it would drift.

    Returns `{"short": …, "long": …, "delta": …, "direction": …}`, each window `{"gws", "pp90", "confidence"}`.

    **`direction` is None unless the long window actually covers more played gameweeks than the short one.**
    Early in a season it does not: with one gameweek played, a 3-GW and a 6-GW window are the *same rows* and
    their difference is exactly zero — a flat trend that looks measured and means nothing. Refusing to answer
    is the only honest output there, and it is the common case for the first month of a season.

    There is deliberately **no "meaningfully different" threshold**. Setting one needs a distribution of real
    gameweek-to-gameweek swings, which does not exist yet; the sign and the size are reported and the reader
    judges. If a cut-off is ever wanted, it is a GW4-6 calibration job like every other constant here.
    """
    rows = list(gw_history or [])
    s_pp90, s_conf = form_rate(rows, k_gameweeks=short, min_minutes=min_minutes)
    l_pp90, l_conf = form_rate(rows, k_gameweeks=long, min_minutes=min_minutes)
    s_gws, l_gws = _played_in(rows, short), _played_in(rows, long)

    delta = direction = None
    if s_pp90 is not None and l_pp90 is not None and l_gws > s_gws:
        delta = s_pp90 - l_pp90
        direction = "level" if delta == 0 else ("up" if delta > 0 else "down")
    return {
        "short": {"gws": s_gws, "pp90": s_pp90, "confidence": s_conf},
        "long": {"gws": l_gws, "pp90": l_pp90, "confidence": l_conf},
        "delta": delta,
        "direction": direction,
    }
