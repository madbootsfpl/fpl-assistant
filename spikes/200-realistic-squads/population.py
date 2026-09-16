"""A squad population that is not random (ADR-199's gate) — importable by any spike that needs one.

**Why this exists.** Three separate measurements were blocked on the same thing: `_CLEAR_GAIN`,
`_CLEAR_REBUILD` (ADR-199) and joint transfer planning (ADR-191 §2). Each had been measured over **random
legal squads**, and spike 191 had already found why that is wrong — a random squad is so bad that any
improvement to it looks enormous:

    best transfer, random squad   +3.5      the owner's real squad   +1.8
    wildcard gain / projection     1.30     the owner's real squad    0.40

⭐ **But "realistic" is not one population, and that is the finding, not an obstacle.** A careful manager's
squad and a casual's differ more than either differs from random. So this does not produce *the* realistic
squad — it produces a **quality dial**, and lets a measurement report its answer as a function of that dial.
A threshold can then be set for the population the app's users actually occupy, and the choice is visible.

Three generators:

* `optimal(...)`     — what the optimiser builds with the whole budget. The ceiling; nobody's real squad.
* `template(...)`    — the most-owned legal 15. The closest single proxy to a median FPL manager, and a
                       genuinely defined population rather than an invented one.
* `perturbed(...)`   — an optimal squad with `k` legal swaps applied. `k=0` is optimal, `k≈12` approaches
                       random. **This is the dial.**

⚠️ Every generator returns a **legal** 15 — 2/5/5/3, ≤3 per club, ≤£100m — or None. A measurement run over
illegal squads would answer a question about nothing.
"""
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics.optimizer import SQUAD_15, is_unavailable, select_squad   # noqa: E402

BUDGET, MAX_PER_CLUB = 100.0, 3


def _legal(squad) -> bool:
    if len(squad) != 15 or sum(p["price"] for p in squad) > BUDGET + 1e-9:
        return False
    if Counter(p["position"] for p in squad) != Counter(SQUAD_15):
        return False
    return max(Counter(p["team"] for p in squad).values()) <= MAX_PER_CLUB


def optimal(players, xp, *, budget: float = BUDGET):
    """The optimiser's own 15 — the ceiling. Real squads sit below it; random ones far below."""
    res = select_squad(players, budget=budget, formation=SQUAD_15, size=15, scores=xp)
    sel = res.get("selected") or []
    return sel if len(sel) == 15 else None


def template(players, *, budget: float = BUDGET):
    """The most-owned squad the money actually buys — **the closest thing to a median FPL manager that can be
    defined**, and the one population here that is *observed* rather than constructed.

    ⚠️ **Greedy by ownership does not work, and the reason is worth keeping.** Taking the most-owned player at
    each position in turn overspends: the template is full of premiums, and the fifteen most-owned players do
    not fit in £100m together. Nobody's real squad is the top of that list — everybody's real squad is that
    list *subject to a budget*, which is a knapsack, so it is handed to the optimiser with **ownership as the
    objective** instead of xP.
    """
    own = {p["id"]: (p["selected_by"] or 0.0) for p in players if not is_unavailable(p)}
    res = select_squad([p for p in players if p["id"] in own],
                       budget=budget, formation=SQUAD_15, size=15, scores=own)
    sel = res.get("selected") or []
    return sel if _legal(sel) else None


def perturbed(base, players, k, rng):
    """`base` with `k` legal random swaps — the quality dial.

    Each swap replaces a random player with a random same-position one the squad can afford and the club cap
    allows. ⚠️ **Swaps are not required to be worse**, only random: forcing them downward would build a
    *deliberately bad* squad, which is a different population again and not one anyone has.
    """
    squad = list(base)
    by_pos = {}
    for p in players:
        if not is_unavailable(p):
            by_pos.setdefault(p["position"], []).append(p)
    for _ in range(k):
        for _attempt in range(25):
            out = rng.choice(squad)
            owned = {q["id"] for q in squad}
            clubs = Counter(q["team"] for q in squad if q["id"] != out["id"])
            spare = BUDGET - sum(q["price"] for q in squad) + out["price"]
            cands = [c for c in by_pos.get(out["position"], [])
                     if c["id"] not in owned and c["price"] <= spare
                     and clubs[c["team"]] < MAX_PER_CLUB]
            if cands:
                squad = [q for q in squad if q["id"] != out["id"]] + [rng.choice(cands)]
                break
    return squad if _legal(squad) else None


def ladder(players, xp, *, seed: int, steps=(0, 2, 4, 6, 9, 12), per_step: int = 20):
    """`{k: [squad, …]}` across the quality dial, plus the template squad at `k="template"`.

    One optimiser solve, then cheap perturbation — so a measurement can sweep quality without paying for a
    solve per squad.
    """
    base = optimal(players, xp)
    if base is None:
        return {}
    rng = random.Random(seed)
    out = {k: [s for s in (perturbed(base, players, k, rng) for _ in range(per_step)) if s] for k in steps}
    if (t := template(players)):
        out["template"] = [t]
    return out
