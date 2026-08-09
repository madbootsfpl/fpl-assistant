"""Walk-forward backtest harness for calibrating the dormant weights (ADR-101).

Measures how well the model predicts real returns, so a weight (`FORM_WEIGHT` first, then set-piece / DefCon) is
set on **evidence**, not a guess. **Pure + read-only** — no engine change, no writes, and the *predictor* is
**injected** (decision_xp-backed in the CLI; synthetic in tests), so this module imports no analytics/config.

Method (ADR-101): for each gameweek **N**, predict using **only data before N** (walk-forward — no leakage) and
pair the predicted xP with the actual `total_points`; score the **rank correlation** (Spearman) per GW, averaged —
with **MAE** and a **top-N hit-rate** as sanity checks. It measures a *ranking* (who to pick), a decision aid, not
a probability; it needs ≥K gameweeks to mean anything (empty preseason → "not enough data yet").
"""

MIN_GWS = 4        # don't trust a recommendation below this many gameweeks of returns (ADR-101 guard)
_FLAT_EPS = 0.005  # "near-flat": within this of the best ρ, prefer the smaller weight (less overfit)


def rounds_with_actuals(gw_history_by_code) -> list[int]:
    """The gameweek rounds that have any actual `total_points` (sorted). Empty preseason."""
    rounds = {r["round"] for rows in gw_history_by_code.values() for r in rows
              if r.get("total_points") is not None}
    return sorted(rounds)


def pairs(gw_history_by_code, predict) -> list[tuple]:
    """Walk-forward `(predicted, actual, round)` triples. For each round N with actuals, call
    `predict(history_before_N, N) → {code: predicted_xp}` using **only rounds < N** (no leakage), and pair each
    prediction with that player's actual `total_points` at N. `predict` is injected (decision_xp in the CLI)."""
    out = []
    for n in rounds_with_actuals(gw_history_by_code):
        before = {code: [r for r in rows if r["round"] < n] for code, rows in gw_history_by_code.items()}
        preds = predict(before, n) or {}
        for code, rows in gw_history_by_code.items():
            actual = next((r["total_points"] for r in rows
                           if r["round"] == n and r.get("total_points") is not None), None)
            if actual is not None and code in preds:
                out.append((preds[code], actual, n))
    return out


# --- metrics (stdlib only) -----------------------------------------------------------

def _rank(values) -> list:
    """1-based average ranks (ties share the mean of their positions)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1        # mean of the 1-based positions i..j
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / (sxx ** 0.5 * syy ** 0.5)


def spearman(preds, actuals):
    """Spearman rank correlation of two aligned sequences, or None if it's undefined (< 2 points / no spread)."""
    if len(preds) < 2:
        return None
    return _pearson(_rank(list(preds)), _rank(list(actuals)))


def _by_gw(triples) -> dict:
    out = {}
    for pred, actual, gw in triples:
        out.setdefault(gw, ([], []))[0].append(pred)
        out[gw][1].append(actual)
    return out


def mean_gw_spearman(triples):
    """The **primary** metric (ADR-101): Spearman per gameweek, averaged. None if no GW has ≥2 comparable pairs."""
    rhos = [spearman(preds, actuals) for preds, actuals in _by_gw(triples).values()]
    rhos = [r for r in rhos if r is not None]
    return sum(rhos) / len(rhos) if rhos else None


def mae(triples):
    """Mean absolute error (predicted xP vs actual points) — a secondary sanity check. None if empty."""
    if not triples:
        return None
    return sum(abs(pred - actual) for pred, actual, _ in triples) / len(triples)


def hit_rate(triples, n: int = 20):
    """Per gameweek: the fraction of the top-`n` predicted players that are in the actual top-`n`, averaged over
    the gameweeks with at least `n` players. A secondary sanity check. None if no GW qualifies."""
    rates = []
    for preds, actuals in _by_gw(triples).values():
        if len(preds) < n:
            continue
        idx = range(len(preds))
        top_pred = set(sorted(idx, key=lambda i: preds[i], reverse=True)[:n])
        top_actual = set(sorted(idx, key=lambda i: actuals[i], reverse=True)[:n])
        rates.append(len(top_pred & top_actual) / n)
    return sum(rates) / len(rates) if rates else None


# --- the sweep -----------------------------------------------------------------------

def sweep(gw_history_by_code, make_predict, values, *, top_n: int = 20, min_gws: int = MIN_GWS):
    """Score each weight `value` (via `make_predict(value) → a predict fn`) by mean-GW Spearman (+ MAE + hit-rate).

    Returns ``{"insufficient": bool, "gws": int, "rows": [...], "best": value|None}``. When fewer than `min_gws`
    gameweeks have actuals → ``insufficient`` (there's not enough data to trust a recommendation). `best` is the
    value with the highest Spearman, but the **smallest** such value within `_FLAT_EPS` of it — the overfitting
    guard (ADR-101): on a near-flat curve, prefer less reliance on a noisy signal.
    """
    gws = len(rounds_with_actuals(gw_history_by_code))
    if gws < min_gws:
        return {"insufficient": True, "gws": gws, "min_gws": min_gws, "rows": [], "best": None}
    rows = []
    for value in values:
        triples = pairs(gw_history_by_code, make_predict(value))
        rows.append({"weight": value, "spearman": mean_gw_spearman(triples),
                     "mae": mae(triples), "hit_rate": hit_rate(triples, top_n)})
    scored = [r for r in rows if r["spearman"] is not None]
    best = None
    if scored:
        top = max(r["spearman"] for r in scored)
        best = min(r["weight"] for r in scored if r["spearman"] >= top - _FLAT_EPS)
    return {"insufficient": False, "gws": gws, "rows": rows, "best": best}
