"""A one-gameweek plan for a squad (ADR-070) — captain · lineup · a transfer · flags.

An **assembler**, not new analytics: it orchestrates the existing decision primitives so the weekly
answer can't diverge from the standalone tools. Captain uses its own next-GW xP (`captain_picks`,
horizon 1); the lineup and the transfer use the caller's multi-GW `xp_by_id` (`best_legal_xi`,
`suggest_transfers`) — the horizon each decision actually wants. Pure given its inputs (no I/O), so
it's unit-tested with a fake squad offline. The `ask` layer humanises + verifies it (ADR-034/037).
"""

from src.analytics.captain import captain_picks
from src.analytics.optimizer import best_legal_xi, is_unavailable
from src.analytics.transfer import suggest_transfers

# FPL status codes → a human word for a flag (mirrors the CLI's availability messages, ADR-023).
# "d" (doubtful) is handled separately — it's a warning, not an unavailability.
_STATUS_WORD = {"i": "injured", "s": "suspended", "u": "unavailable", "n": "unavailable"}


def gameweek_plan(owned, market, upcoming, xp_by_id, *,
                  baseline_by_code=None, minutes_weight=None, history_by_code=None,
                  bench_ids=(), bank: float = 0.0) -> dict:
    """Assemble this gameweek's plan for a squad from the existing primitives.

    `owned` are the squad's player rows; `market` is the whole player pool (for the transfer);
    `upcoming` the fixtures; `xp_by_id` the multi-GW xP the caller already computed (id → xP). The
    captain hooks (`baseline_by_code`/`minutes_weight`/`history_by_code`) feed `captain_picks` its
    own next-GW xP. `bench_ids` is the squad's declared bench (drives the lineup change); `bank` the
    money available for the transfer.

    Returns ``{captain, lineup, transfer, flags}``:
    - **captain** — the top next-GW pick (a `captain_picks` dict), or None if none is eligible.
    - **lineup** — ``{start, bench, bring_in, drop, has_declared_bench}``: the best legal XI (rows)
      and its bench, plus who to bring in / drop vs the declared XI (empty when already optimal).
    - **transfer** — the single best positive-gain upgrade (a `suggest_transfers` dict), or None.
    - **flags** — owned players who can't (or might not) play: ``{web_name, team, reason, chance}``.
    """
    # Captain — the next-GW pick from the owned, XI-eligible players (ADR-029). `limit=3` so the runner-up is
    # available for the captain explanation's lead-margin (ADR-089); the pick is still picks[0].
    picks = captain_picks(owned, upcoming, baseline_by_code=baseline_by_code, limit=3,
                          minutes_weight=minutes_weight, history_by_code=history_by_code)
    captain = picks[0] if picks else None

    # Lineup — the best legal XI on the horizon xP vs the declared bench (ADR-039/040).
    optimal = best_legal_xi(owned, xp_by_id)
    declared_bench = set(bench_ids)
    declared_xi = ({p["id"] for p in owned if p["id"] not in declared_bench}
                   if declared_bench else optimal)
    by_id = {p["id"]: p for p in owned}
    lineup = {
        "start": [by_id[i] for i in optimal if i in by_id],
        "bench": [p for p in owned if p["id"] not in optimal],
        "bring_in": [by_id[i] for i in optimal - declared_xi if i in by_id],
        "drop": [by_id[i] for i in declared_xi - optimal if i in by_id],
        "has_declared_bench": bool(declared_bench),
    }

    # Transfer — the single best positive-gain, self-funding upgrade (ADR-030/046).
    moves = suggest_transfers(owned, market, xp_by_id, bench_ids=bench_ids, bank=bank, limit=1)
    transfer = moves[0] if moves else None

    # Flags — owned players who are unavailable, or doubtful (a warning, kept in the XI). ADR-023.
    flags = []
    for p in owned:
        if is_unavailable(p):
            reason = _STATUS_WORD.get(p["status"], "unavailable")
        elif p["status"] == "d":
            reason = "doubtful"
        else:
            continue
        flags.append({"web_name": p["web_name"], "team": p["team"],
                      "reason": reason, "chance": p["chance"]})

    return {"captain": captain, "captain_ranked": picks, "lineup": lineup,
            "transfer": transfer, "flags": flags}
