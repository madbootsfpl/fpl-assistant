"""Import a manager's FPL team by their public manager-ID (Sprint 064, ADR-058).

Two parts: a **pure mapper** (`picks_to_squad`) — a picks payload → a `SquadStore`-shaped dict — and a
thin **orchestrator** (`fetch_manager_team`) that fetches the public entry + picks via the FPL client and
**degrades gracefully** (a clear message, never a raise). The result is a squad dict the web edge sets as
the session active squad (no server writes) — a third way alongside build/upload.

Picks are **public only after a gameweek's deadline** (404 before) — so preseason this returns a clear
"available after the GW1 deadline" message; it goes live at GW1 (2026-08-21).
"""

from src.api.client import FplApiError, FplClient

# FPL squad positions: 1–11 are the starting XI, 12–15 the bench (in the picks payload).
_BENCH_FROM = 12


def _money(tenths) -> float | None:
    """FPL counts money in tenths of a million — `13` is £1.3m. None when absent, never 0.0.

    ⭐ **None and zero are different facts.** An empty bank is a real position a manager can be in; *"we do
    not know your bank"* is not, and defaulting the second to the first would silently tell the affordability
    maths that every transfer is unaffordable.
    """
    return None if tenths is None else round(tenths / 10, 1)


def picks_to_squad(picks_payload: dict, players, *, name: str) -> dict | None:
    """Map a `/entry/{id}/event/{gw}/picks/` payload → a `SquadStore`-shaped squad dict, or None if the
    picks can't be resolved against the current players (a stale/mismatched cache). Pure + empty-safe."""
    by_id = {p["id"]: p for p in players}
    history = picks_payload.get("entry_history") or {}
    picks = sorted(picks_payload.get("picks") or [], key=lambda pk: pk.get("position", 0))
    ids = [pk["element"] for pk in picks]
    if not ids or any(i not in by_id for i in ids):
        return None
    bench_ids = [pk["element"] for pk in picks if pk.get("position", 0) >= _BENCH_FROM]
    captain_id = next((pk["element"] for pk in picks if pk.get("is_captain")), None)
    # FPL sends `is_vice_captain` beside `is_captain` in the same pick, and it was being discarded — so an
    # imported team lost a decision its owner had actually made, and the pitch could not show a (V).
    vice_captain_id = next((pk["element"] for pk in picks if pk.get("is_vice_captain")), None)
    return {
        "name": name,
        "player_ids": ids,
        "player_names": [by_id[i]["web_name"] for i in ids],
        "bench_ids": bench_ids,
        "captain_id": captain_id,
        "vice_captain_id": vice_captain_id,
        "cost": round(sum(by_id[i]["price"] for i in ids), 1),
        # ⭐ **Read from `entry_history`, which was being thrown away** (ADR-223). ADR-191 found the app
        # advising a position the manager was not in because `bank` was hard-coded to £0.0m while the
        # Transfer tab collected it by hand three tabs away — and FPL had been sending it all along, in the
        # same payload as the picks.
        #
        # ⚠️ **FPL counts money in tenths.** `bank: 13` is £1.3m, not £13m. A missing `/ 10` here would
        # hand a manager ten times his money and every affordability answer downstream would be wrong while
        # looking entirely reasonable.
        "bank": _money(history.get("bank")),
        # ⚠️ **`value` INCLUDES the bank** — verified by arithmetic rather than assumed: FPL reported
        # value 995 and bank 13 for a squad this function prices at £98.2m, and 98.2 + 1.3 = 99.5.
        "value": _money(history.get("value")),
        # The chip in play this gameweek (`bboost`, `3xc`, `freehit`, `wildcard`) or None.
        "active_chip": picks_payload.get("active_chip"),
    }


def fetch_manager_team(entry_id: int, players, *, client=None) -> tuple[dict | None, str]:
    """Fetch a manager's team by id → `(squad_dict | None, message)`. Degrades on any failure (ADR-058):
    a bad id / down API / not-yet-public picks → `(None, a clear message)`, never a raise."""
    client = client or FplClient()
    try:
        entry = client.get_entry(entry_id)
    except FplApiError:
        return None, f"Couldn't reach FPL for manager #{entry_id} — check the ID, or try again later."

    name = entry.get("name") or f"Manager {entry_id}"
    gameweek = entry.get("current_event")
    if not gameweek:
        return None, ("That team isn't public yet — a manager's squad becomes available after the "
                      "**GW1 deadline (2026-08-21)**.")

    try:
        picks = client.get_entry_picks(entry_id, gameweek)
    except FplApiError:
        return None, "That team isn't available yet — it locks in at the **GW1 deadline (2026-08-21)**."

    squad = picks_to_squad(picks, players, name=name)
    if squad is None:
        return None, "Couldn't match that team to the current players — run a data refresh and retry."
    return squad, f"Imported **{name}** — GW{gameweek} squad."
