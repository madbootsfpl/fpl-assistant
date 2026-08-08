"""Explainability — turn a decision's signals into a visible Why / Risk / Confidence (Sprint 104, ADR-089).

Pure: a recommendation + its signal rows → an `Explanation` (✓ reasons, ⚠ risks, a confidence score + band).
Every line and the number are **computed from the data** — never invented by the LLM (which stays a narrator,
verified, ADR-037). Empty-safe: a zero/absent signal produces no line. The confidence is a **transparent
heuristic** (documented in ADR-089), not a calibrated probability.
"""

from dataclasses import dataclass, field

from src.analytics.crowd import DIFFERENTIAL_OWN, FORM_MIN, TEMPLATE_OWN

_START_MINUTES = 0.7   # xMins weight ≥ this → "expected to start"; below → a rotation risk
_CLEAR_LEAD = 0.8      # an xP lead of this over the runner-up reads as a "clear" pick


@dataclass
class Explanation:
    """Grounded reasons *for* (✓) and *against* (⚠) a pick, plus a heuristic confidence (0–99) + its band."""
    reasons: list = field(default_factory=list)
    risks: list = field(default_factory=list)
    confidence: int = 0
    band: str = "Low"


def confidence_band(score: int) -> str:
    """A word for a 0–99 confidence score: High (≥75) · Medium (≥55) · Low."""
    return "High" if score >= 75 else "Medium" if score >= 55 else "Low"


def captain_confidence(minutes_weight, xp_gap, *, penalty, venue, difficulty, doubtful, chance) -> int:
    """A transparent confidence heuristic for a captain pick (ADR-089), 1–99 — **not** a probability.

    Blends how likely they play (xMins), how clear the pick is (the xP lead over the runner-up) and the
    fixture, with a penalty bonus; a *doubtful* captain is capped by their chance of playing."""
    plays = min(1.0, max(0.0, minutes_weight if minutes_weight is not None else 1.0))
    clearness = min(1.0, max(0.0, (xp_gap or 0.0)) / _CLEAR_LEAD)
    diff = difficulty if difficulty is not None else 3
    fixture = 1.0 if (venue == "H" or diff <= 2) else (0.6 if venue == "A" else 0.8)
    score = 100 * (0.45 * plays + 0.40 * clearness + 0.15 * fixture) + (4 if penalty else 0)
    if doubtful:
        score = min(score, (chance if chance is not None else 50) * 0.8)
    return max(1, min(99, round(score)))


def _get(row, key):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def explain_captain(picks, players_by_id) -> Explanation | None:
    """Explain the top captain pick (ADR-089): grounded ✓ reasons + ⚠ risks + a confidence. `picks` is the
    ranked `captain_picks` list (the runner-up sharpens the 'narrow lead' risk); `players_by_id` gives the
    ownership / set-piece / form / status the pick row doesn't carry. None if there are no picks."""
    if not picks:
        return None
    top = picks[0]
    row = players_by_id.get(_get(top, "id"), {})
    xp = top.get("xp")
    venue, difficulty = top.get("venue"), top.get("difficulty")
    mins = top.get("minutes_weight")
    runner = picks[1] if len(picks) > 1 else None
    gap = round((xp or 0) - (runner["xp"] or 0), 1) if runner else None

    reasons, risks = [], []
    # ✓ Why — phrasing aligned to the Captain Pick card (US-277); the projected xP lives on the card's
    # "Projected" line, so the reason drops the redundant number.
    if xp is not None:
        reasons.append("Highest projected points")
    if top.get("penalty_taker"):
        reasons.append("Penalty taker")
    if _get(row, "freekicks_order") == 1 or _get(row, "corners_order") == 1:
        reasons.append("Set-piece involvement")
    if mins is not None and mins >= _START_MINUTES:
        reasons.append(f"Expected ~{round(mins * 90)} mins")
    own = _get(row, "selected_by")
    if own is not None and own >= TEMPLATE_OWN:
        reasons.append(f"Template pick ({own:.0f}% owned)")
    if difficulty is not None and (difficulty <= 2 or venue == "H"):
        reasons.append(f"Strong fixture vs {top.get('opponent') or 'TBC'}")
    form = _get(row, "form")
    if form is not None and form >= FORM_MIN:
        reasons.append(f"In form ({form})")

    # ⚠ Risk
    if venue == "A":
        risks.append("Away fixture")
    if top.get("doubtful"):
        chance = top.get("chance")
        risks.append("Doubtful" + (f" ({chance}% chance)" if chance is not None else ""))
    if mins is not None and mins < _START_MINUTES:
        risks.append(f"Rotation risk (~{round(mins * 90)} mins)")
    if difficulty is not None and difficulty >= 4:
        risks.append(f"Tough fixture vs {top.get('opponent') or 'TBC'}")
    if runner is not None and gap is not None and gap < 0.5:
        risks.append(f"Only +{gap} pts ahead of {runner['web_name']}")
    if own is not None and 0 < own <= DIFFERENTIAL_OWN:
        risks.append(f"Big differential ({own:.0f}% owned)")

    score = captain_confidence(
        mins, gap, penalty=top.get("penalty_taker"), venue=venue, difficulty=difficulty,
        doubtful=top.get("doubtful"), chance=top.get("chance"),
    )
    return Explanation(reasons=reasons, risks=risks, confidence=score, band=confidence_band(score))


_CLEAR_GAIN = 3.0   # an XI-xP gain of this over the horizon reads as a "clear" upgrade


def transfer_confidence(gain, *, doubtful_in=False, chance_in=None) -> int:
    """A transparent confidence heuristic for a single swap (ADR-089), 1–99 — how clearly it's an upgrade
    (the XI-xP gain) tempered by a doubtful buy. Not a probability."""
    clearness = min(1.0, max(0.0, gain or 0.0) / _CLEAR_GAIN)
    score = 40 + 55 * clearness                      # a tiny positive gain ≈ 40; a ≥3 gain ≈ 95
    if doubtful_in:
        score = min(score, (chance_in if chance_in is not None else 50) * 0.8)
    return max(1, min(99, round(score)))


def explain_transfer(move, in_row, horizon: int = 5) -> Explanation | None:
    """Explain a single transfer (ADR-089): grounded ✓ reasons + ⚠ risks + a confidence. `move` is a
    `suggest_transfers` dict (`out`/`in` summaries + `gain`, the XI improvement); `in_row` is the buy's full
    player row (ownership / set-pieces / status the summary doesn't carry). None if there's no move."""
    if not move:
        return None
    buy, sell = move["in"], move["out"]
    gain = move.get("gain")
    price_delta = round((buy.get("price") or 0) - (sell.get("price") or 0), 1)
    status = _get(in_row, "status")
    doubtful = status == "d"

    reasons, risks = [], []
    # ✓ Why
    if gain is not None:
        reasons.append(f"+{gain} to your starting XI over {horizon} GW")
    if (buy.get("xp") or 0) > (sell.get("xp") or 0):
        reasons.append(f"Higher projected points ({buy['xp']} vs {sell['xp']})")
    if _get(in_row, "penalties_order") == 1:
        reasons.append("Penalty taker")                        # phrasing aligned across the family (US-278)
    if _get(in_row, "freekicks_order") == 1 or _get(in_row, "corners_order") == 1:
        reasons.append("Set-piece involvement")
    if price_delta < 0:
        reasons.append(f"Frees £{-price_delta:.1f}m")
    own = _get(in_row, "selected_by")
    if own is not None and own >= TEMPLATE_OWN:
        reasons.append(f"Template pick ({own:.0f}% owned)")
    form = _get(in_row, "form")
    if form is not None and form >= FORM_MIN:
        reasons.append(f"In form ({form})")

    # ⚠ Risk
    if price_delta > 0:
        risks.append(f"Costs £{price_delta:.1f}m from your bank")
    risks.append(f"Selling {sell['web_name']} ({sell.get('xp')} xP)")
    if doubtful:
        chance = _get(in_row, "chance")
        risks.append("Doubtful buy" + (f" ({chance}% chance)" if chance is not None else ""))
    if own is not None and 0 < own <= DIFFERENTIAL_OWN:
        risks.append(f"Big differential ({own:.0f}% owned)")
    if gain is not None and gain < 1.0:
        risks.append(f"Marginal gain (+{gain})")

    score = transfer_confidence(gain, doubtful_in=doubtful, chance_in=_get(in_row, "chance"))
    return Explanation(reasons=reasons, risks=risks, confidence=score, band=confidence_band(score))


# ── Squad build (US-271, extends ADR-089) ─────────────────────────────────────

def squad_confidence(xi_reliability, spent_fraction) -> int:
    """A transparent confidence heuristic for a built 15 (ADR-089), 1–99 — how solid the build is: the XI's
    average expected-minutes **reliability** + how well it **used the budget**. Not a probability."""
    reliability = min(1.0, max(0.0, xi_reliability if xi_reliability is not None else 1.0))
    spent = min(1.0, max(0.0, spent_fraction if spent_fraction is not None else 1.0))
    return max(1, min(99, round(100 * (0.7 * reliability + 0.3 * spent))))


def explain_squad(selected, xp_by_id, weight_by_id, *, budget, xi_ids, horizon=5) -> Explanation | None:
    """Explain a built squad (ADR-089): grounded ✓ reasons + ⚠ risks + a confidence. `selected` are the 15
    picked player rows (each with `price`/`position`; ownership/status read off the row); `xi_ids` the starting
    XI; `xp_by_id`/`weight_by_id` the projection + xMins. None if there's nothing selected."""
    if not selected:
        return None
    cost = round(sum(p["price"] for p in selected), 1)
    xi = [p for p in selected if p["id"] in set(xi_ids)]
    bench = [p for p in selected if p["id"] not in set(xi_ids)]
    xi_xp = round(sum(xp_by_id.get(p["id"], 0) for p in xi), 1)
    bench_xp = round(sum(xp_by_id.get(p["id"], 0) for p in bench), 1)
    unspent = round((budget or 0) - cost, 1)
    reliability = (sum(weight_by_id.get(p["id"], 1.0) for p in xi) / len(xi)) if xi else 1.0
    top = sorted(selected, key=lambda p: -xp_by_id.get(p["id"], 0))[:3]

    reasons, risks = [], []
    # ✓ Why
    reasons.append("Optimised on projected points (xP)")
    reasons.append(f"Starting XI projects {xi_xp} over {horizon} GW")
    if budget:
        reasons.append(f"Spent £{cost:.1f}m of £{budget:.1f}m")
    reasons.append("Top picks: " + ", ".join(f"{p['web_name']} ({p['position']})" for p in top))
    if bench_xp > 0:
        reasons.append(f"Bench projects {bench_xp} (rotation cover)")

    # ⚠ Risk
    if unspent >= 0.5:
        risks.append(f"£{unspent:.1f}m unspent")
    rotation = [p for p in xi if (weight_by_id.get(p["id"], 1.0)) < _START_MINUTES]
    if rotation:
        risks.append(f"{len(rotation)} rotation-risk starter{'s' if len(rotation) != 1 else ''}"
                     " (low expected minutes)")
    doubtful = [p for p in selected if _get(p, "status") == "d"]
    if doubtful:
        risks.append(f"{len(doubtful)} doubtful in the 15")
    diffs = [p for p in selected if 0 < (_get(p, "selected_by") or 100) <= DIFFERENTIAL_OWN]
    if len(diffs) >= 4:
        risks.append(f"Differential-heavy ({len(diffs)} ≤{DIFFERENTIAL_OWN:.0f}% owned — higher variance)")
    if bench and bench_xp < 4.0:
        risks.append(f"Weak bench (projects {bench_xp})")

    score = squad_confidence(reliability, (cost / budget) if budget else 1.0)
    return Explanation(reasons=reasons, risks=risks, confidence=score, band=confidence_band(score))


# ── Chips (US-272, extends ADR-089) ───────────────────────────────────────────

_CLEAR_CHIP_MARGIN = 0.15   # a recommended chip GW that beats the next-best by ≥15% (relative) is "clear"

# chip → the field holding the recommended gameweek's headline value (to normalise the margin against).
_CHIP_VALUE_KEY = {
    "triple_captain": "player_xp", "bench_boost": "squad_total",
    "free_hit": "xi_total", "wildcard": "avg_xi",
}


def chip_confidence(margin, value) -> int:
    """A transparent confidence for a chip recommendation (ADR-089), 1–99 — how clearly the recommended
    gameweek/window beats the next-best, **relative** to its own scale. Small margin → Low (preseason the
    gameweeks are near-uniform, so this honestly reads Low/Medium and sharpens in-season). Not a probability."""
    rel = (abs(margin or 0.0) / value) if value else 0.0
    clear = min(1.0, rel / _CLEAR_CHIP_MARGIN)
    return max(1, min(99, round(40 + 55 * clear)))


def explain_chips(advice) -> dict | None:
    """Per-chip confidence for a `chip_advisor` result (ADR-089): `{chip: {confidence, band}}`, from each
    chip's `margin` (best vs next-best gameweek) relative to its value. None if there's no advice."""
    if not advice:
        return None
    out = {}
    for chip, value_key in _CHIP_VALUE_KEY.items():
        rec = advice.get(chip) or {}
        conf = chip_confidence(rec.get("margin"), rec.get(value_key))
        out[chip] = {"confidence": conf, "band": confidence_band(conf)}
    return out


# ── Gameweek plan (US-273/274, extends ADR-089) ───────────────────────────────

def _lineup_reasons(lineup, xp_by_id) -> list:
    """Short grounded 'why' for each start/bench change — 'start {in} over {out} (higher projected xP)'."""
    reasons = []
    for bring, drop in zip(lineup.get("bring_in", []), lineup.get("drop", [])):
        reasons.append(f"Start {bring['web_name']} over {drop['web_name']} (higher projected xP: "
                       f"{round(xp_by_id.get(bring['id'], 0), 1)} vs {round(xp_by_id.get(drop['id'], 0), 1)})")
    return reasons


def gameweek_confidence(captain_confidence_score, n_flags: int) -> int:
    """A plan-level confidence (ADR-089), 1–99 — the week is driven by the captain (its biggest single lever),
    tempered by flagged (doubtful/unavailable) players. Documented, not a probability."""
    return max(1, min(99, round((captain_confidence_score or 50) - 8 * max(0, n_flags))))


def explain_gameweek(plan, players_by_id, xp_by_id, *, horizon=5) -> dict | None:
    """Explain a gameweek plan (ADR-089): reuse the captain + transfer explanations, add a lineup rationale,
    and give the week an overall Confidence · Why · Risk. Returns `{captain, transfer, lineup, overall}` (each
    an `Explanation` / list), or None if there's no plan."""
    if not plan:
        return None
    cap_ex = explain_captain(plan.get("captain_ranked") or ([plan["captain"]] if plan.get("captain") else []),
                             players_by_id)
    move = plan.get("transfer")
    tr_ex = explain_transfer(move, players_by_id.get((move.get("in") or {}).get("id"), {}), horizon) \
        if move else None
    lineup = _lineup_reasons(plan.get("lineup") or {}, xp_by_id)

    # Overall — captain-driven, flagged players are the week's risk.
    flags = plan.get("flags") or []
    reasons, risks = [], []
    if plan.get("captain"):
        reasons.append(f"Clear captain: {plan['captain']['web_name']}"
                       + (f" ({cap_ex.confidence}/100 · {cap_ex.band})" if cap_ex else ""))
    if move:
        reasons.append(f"A positive-gain upgrade available (+{move['gain']} XI xP)")
    elif not lineup:
        reasons.append("No changes needed — your XI is already optimal")
    if lineup:
        reasons.append(f"{len(lineup)} lineup tweak{'s' if len(lineup) != 1 else ''} to bank more points")
    if flags:
        risks.append(", ".join(f"{f['web_name']} ({f['reason']}"
                               + (f", {f['chance']}%" if f.get("chance") is not None else "") + ")"
                               for f in flags))
    else:
        risks.append("none — all your players are available")

    score = gameweek_confidence(cap_ex.confidence if cap_ex else None, len(flags))
    overall = Explanation(reasons=reasons, risks=risks, confidence=score, band=confidence_band(score))
    return {"captain": cap_ex, "transfer": tr_ex, "lineup": lineup, "overall": overall}
