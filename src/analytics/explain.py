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
    row = players_by_id.get(top["id"], {})
    xp = top.get("xp")
    venue, difficulty = top.get("venue"), top.get("difficulty")
    mins = top.get("minutes_weight")
    runner = picks[1] if len(picks) > 1 else None
    gap = round((xp or 0) - (runner["xp"] or 0), 1) if runner else None

    reasons, risks = [], []
    # ✓ Why
    if xp is not None:
        reasons.append(f"Highest projected points ({xp})")
    if top.get("penalty_taker"):
        reasons.append("On penalties")
    if _get(row, "freekicks_order") == 1 or _get(row, "corners_order") == 1:
        reasons.append("Takes set-pieces")
    if mins is not None and mins >= _START_MINUTES:
        reasons.append(f"Expected to start (~{round(mins * 90)} mins)")
    own = _get(row, "selected_by")
    if own is not None and own >= TEMPLATE_OWN:
        reasons.append(f"Template pick ({own:.0f}% owned)")
    if difficulty is not None and (difficulty <= 2 or venue == "H"):
        reasons.append(f"Favourable fixture ({top.get('opponent') or 'TBC'})")
    form = _get(row, "form")
    if form is not None and form >= FORM_MIN:
        reasons.append(f"In form ({form})")

    # ⚠ Risk
    if venue == "A":
        risks.append(f"Away fixture ({top.get('opponent') or 'TBC'})")
    if top.get("doubtful"):
        chance = top.get("chance")
        risks.append("Doubtful" + (f" ({chance}% chance)" if chance is not None else ""))
    if mins is not None and mins < _START_MINUTES:
        risks.append(f"Rotation risk (~{round(mins * 90)} mins)")
    if difficulty is not None and difficulty >= 4:
        risks.append(f"Tough fixture ({top.get('opponent') or 'TBC'})")
    if runner is not None and gap is not None and gap < 0.5:
        risks.append(f"Narrow lead over {runner['web_name']} (+{gap})")
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
        reasons.append("On penalties")
    if _get(in_row, "freekicks_order") == 1 or _get(in_row, "corners_order") == 1:
        reasons.append("Takes set-pieces")
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
