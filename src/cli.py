"""Command-line interface — the interaction layer.

This is the only place that decides *what the user asked for*. It parses the
command line and dispatches to a handler; each handler then calls the existing
layers (client, storage, display). The CLI itself contains no FPL logic — keeping
it thin is what makes the app easy to extend (add a command) and easy to test.

See ADR-003 for why this is argparse + subcommands.
"""

import argparse
import shutil
from datetime import UTC, datetime

from src import ask, chat_context, config, ingest
from src.analytics import (
    DEFAULT_BUDGET,
    FULL_BUDGET,
    SQUAD_15,
    WEEKLY_BENCH_WEIGHT,
    XI_FLEX,
    analyse_squad,
    archetype_bands,
    available_players,
    baseline_rate,
    best_legal_xi,
    captain_picks,
    chip_advisor,
    decision_xp,
    defcon_reliability,
    defensive_solidity,
    elo_difficulty_bands,
    explain_captain,
    explain_chips,
    is_unavailable,
    minutes_weight_from_history,
    objective_scores,
    over_under,
    player_history,
    player_xp,
    rank_players,
    replace_dead,
    resolve_players,
    select_squad,
    suggest_transfer_plan,
    suggest_transfers,
    team_fdr,
    team_schedule,
)
from src.api.client import FplApiError
from src.squads import SquadStore
from src.storage import Storage
from src.ui.analyse import render_squad_analysis
from src.ui.ask import render_ask
from src.ui.captain import render_captain_picks
from src.ui.chips import render_chip_advice
from src.ui.cleansheet import render_cleansheet
from src.ui.defcon import render_defcon
from src.ui.fdr import render_fdr_table
from src.ui.fixtures import render_team_fixtures
from src.ui.history import render_player_history
from src.ui.overperf import render_overperf
from src.ui.squad import render_loaded_squad, render_squad
from src.ui.table import render_player_table
from src.ui.transfer import render_dead_slots, render_transfer_plan, render_transfers
from src.ui.xg import render_xg_table
from src.ui.xp import render_xp_table


def cmd_table(args) -> None:
    """Show the players currently stored in the local database."""
    store = Storage()
    rows = store.get_players()
    if not rows:
        print("No data yet — run `refresh` first.")
    else:
        ranked = rank_players(rows, sort_by=args.sort)
        print(render_player_table(ranked, limit=args.limit))
    store.close()


def cmd_refresh(args) -> None:
    """Fetch the latest FPL data and store it locally."""
    store = Storage()
    try:
        n_players, n_teams, n_fixtures, n_elo = ingest.refresh(store)
        print(
            f"Refreshed {n_players} players, {n_teams} teams, {n_fixtures} fixtures "
            f"and {n_elo} Elo ratings into {config.DB_PATH}."
        )
    except FplApiError as exc:
        print(f"Could not refresh FPL data: {exc}")
    finally:
        store.close()


def cmd_reseed(args) -> None:
    """Refresh the live cache, then copy it to the committed seed so the deployed app can be updated.

    The one-command version of the documented deploy workflow (ADR-053): `refresh` into the live
    cache (fpl.db), then copy fpl.db → seed.db. The **cloud** serves the committed seed, so updating
    the live app is: `reseed` → commit → push → reboot. A **local** run never needs this — the sidebar
    🔄 button (or a restart after `refresh`) reads fpl.db directly.
    """
    store = Storage(db_path=config.LIVE_DB_PATH)
    try:
        n_players, n_teams, n_fixtures, n_elo = ingest.refresh(store)
    except FplApiError as exc:
        print(f"Could not refresh FPL data: {exc}")
        return
    finally:
        store.close()   # flush + unlock before copying the file

    # ClubElo is best-effort (ADR-010) — report whether it refreshed or kept the last-known Elo (US-293:
    # `reseed` used to look silent on Elo because it dropped this count).
    elo_note = f"{n_elo} Elo ratings (ClubElo)" if n_elo else "0 Elo ratings (ClubElo kept last-known)"
    shutil.copyfile(config.LIVE_DB_PATH, config.SEED_DB_PATH)
    print(
        f"Refreshed {n_players} players, {n_teams} teams, {n_fixtures} fixtures and {elo_note} into "
        f"{config.LIVE_DB_PATH} and copied it to {config.SEED_DB_PATH}.\n"
        "To update the live app: commit + push (Community Cloud auto-redeploys, or Reboot it)."
    )


def _resolve_player(players, name: str):
    """A stored player matching `name` (an exact web_name wins, else a unique substring), or None with a
    printed nudge when there's no match or it's ambiguous (US-295)."""
    q = name.strip().lower()
    exact = [p for p in players if (p["web_name"] or "").lower() == q]
    if exact:
        return exact[0]
    contains = [p for p in players if q and q in (p["web_name"] or "").lower()]
    if len(contains) == 1:
        return contains[0]
    if not contains:
        print(f"No player matching '{name}'. Try a surname, e.g. `history Haaland`.")
    else:
        names = ", ".join(sorted({p["web_name"] for p in contains})[:8])
        print(f"Several players match '{name}': {names}. Be more specific.")
    return None


def cmd_history(args) -> None:
    """A player's season history (`history <player>`) — or backfill it (`history --backfill`, ADR-027/060).

    `history <player>` shows the past-season record (real now) + this-season per-GW trend (fills at GW1).
    `--backfill` is the throttled, resumable ingest (one `element-summary` call per player); `--limit N` slices.
    """
    if getattr(args, "player", None):                            # the view (US-295)
        store = Storage()
        try:
            players = store.get_players()
            if not players:
                print("No players stored yet — run `refresh` first.")
                return
            target = _resolve_player(players, args.player)
            if target is None:
                return
            hist = player_history(target, store.get_history_past(target["code"]),
                                  store.get_history(target["code"]))
            print(render_player_history(hist))
        finally:
            store.close()
        return

    if not args.backfill:
        print(
            "Nothing to do. Try `history <player>` for a player's record, or `history --backfill` "
            "to fetch past-season data (a few minutes for all players; add --limit N for a slice)."
        )
        return

    store = Storage()
    try:
        ids = store.get_player_ids()
        if not ids:
            print("No players stored yet — run `refresh` first.")
            return
        if args.limit:
            ids = ids[: args.limit]

        def progress(i, total):
            if i % 50 == 0 or i == total:
                print(f"  … {i}/{total} players")

        print(f"Backfilling past-season + per-GW history for {len(ids)} player(s)…")
        processed, seasons, gameweeks, failures = ingest.backfill_history(
            store, ids=ids, progress=progress
        )
        note = f" ({failures} failed and were skipped)" if failures else ""
        # Per-GW (ADR-060) is empty preseason (0) and fills at GW1 — reported for visibility.
        print(
            f"Stored {seasons} season rows + {gameweeks} per-GW rows across {processed} "
            f"player(s){note}. Now cached in {config.DB_PATH}."
        )
    finally:
        store.close()


def cmd_search(args) -> None:
    """Find players whose name contains the given text."""
    store = Storage()
    rows = store.get_players(name=args.name)
    if not rows:
        print(f"No players match '{args.name}'.")
    else:
        print(render_player_table(rank_players(rows)))
    store.close()


def resolve_squad_budget(budget, full: bool) -> float:
    """The budget to use: the given value, else the mode default (£100m full / £80m XI).

    argparse can't tell "user typed --budget 80" from "default 80", and the default
    differs by mode — so `--budget` defaults to None and the choice is made here.
    """
    if budget is not None:
        return budget
    return FULL_BUDGET if full else DEFAULT_BUDGET


BENCH_MAX = 4   # a 15-man squad has 15 − 11 = 4 bench slots

# FPL status codes → a human word for availability messages (ADR-023).
_STATUS_WORD = {"i": "injured", "s": "suspended", "u": "unavailable", "n": "unavailable"}


def validate_bench(bench_ids, include_ids, exclude_ids) -> list:
    """Errors for an invalid declared bench (ADR-013): too many, or a double role.

    Pure (ids in, messages out) so it's testable without a database.
    """
    errors = []
    if len(bench_ids) > BENCH_MAX:
        errors.append(
            f"You can bench at most {BENCH_MAX} players "
            f"(a 15-man squad has {BENCH_MAX} bench slots)."
        )
    if set(bench_ids) & set(include_ids):
        errors.append("A player can't be both --include and --bench.")
    if set(bench_ids) & set(exclude_ids):
        errors.append("A player can't be both --bench and --exclude.")
    return errors


# Legal XI ranges (GK is always 1): DEF 3–5, MID 2–5, FWD 1–3, outfield sums to 10.
_FORMATION_RANGES = {"DEF": (3, 5), "MID": (2, 5), "FWD": (1, 3)}


def parse_formation(spec: str):
    """Parse a `D-M-F` formation string to an exact `{GK,DEF,MID,FWD}` dict (ADR-014).

    Pure: returns `(formation, None)` on success or `(None, message)` on any error —
    three integers, each within its legal range, summing to 10 outfield (GK implicit).
    """
    parts = spec.split("-")
    if len(parts) != 3 or not all(x.strip().lstrip("-").isdigit() for x in parts):
        return None, f"Formation '{spec}' must be three numbers like 3-5-2 (DEF-MID-FWD)."
    d, m, f = (int(x) for x in parts)
    for pos, val in (("DEF", d), ("MID", m), ("FWD", f)):
        lo, hi = _FORMATION_RANGES[pos]
        if not lo <= val <= hi:
            return None, f"Formation '{spec}': {pos} must be {lo}-{hi} (got {val})."
    if d + m + f != 10:
        return None, f"Formation '{spec}': outfield players must total 10 (got {d + m + f})."
    return {"GK": 1, "DEF": d, "MID": m, "FWD": f}, None


_POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}


def _load_squad(name: str, players) -> None:
    """Reconstruct a saved squad against current data (ADR-024): re-price, availability, departed."""
    squads = SquadStore()
    saved = squads.load(name)
    if saved is None:
        names = squads.names()
        hint = f" Saved: {', '.join(names)}." if names else " None saved yet."
        print(f"No saved squad '{name}'.{hint}")
        return

    by_id = {p["id"]: p for p in players}
    bench = set(saved["bench_ids"])
    loaded = []
    for pid in saved["player_ids"]:
        if pid in by_id:
            row = dict(by_id[pid])
            row["bench"] = pid in bench
            loaded.append(row)

    # A saved player no longer in the game — shown by the name we stored at save time.
    name_by_id = dict(zip(saved["player_ids"], saved.get("player_names", [])))
    departed = [name_by_id.get(pid, str(pid))
                for pid in saved["player_ids"] if pid not in by_id]

    # Starters (by position, points) first; bench last — matching the squad display.
    loaded.sort(key=lambda p: (p["bench"], _POS_ORDER.get(p["position"], 9), -p["total_points"]))
    now_cost = round(sum(p["price"] for p in loaded), 1)
    print(render_loaded_squad(name, saved, loaded, now_cost, departed))


def cmd_squad(args) -> None:
    """Pick the optimal squad — the starting XI, or the full 15 with `--full`."""
    store = Storage()
    players = store.get_players()

    # --load is a distinct display-only mode: reconstruct a saved squad (ADR-024).
    if args.load:
        if args.save:
            print("Use --save or --load, not both.")
            store.close()
            return
        _load_squad(args.load, players)
        store.close()
        return

    include_ids, errors = resolve_players(players, args.include)
    exclude_ids, exclude_errors = resolve_players(players, args.exclude)
    bench_ids, bench_errors = resolve_players(players, args.bench)
    errors += exclude_errors + bench_errors

    # A player can't be both forced in and forced out.
    conflict = set(include_ids) & set(exclude_ids)
    if conflict:
        names = ", ".join(p["web_name"] for p in players if p["id"] in conflict)
        errors.append(f"Cannot both include and exclude: {names}.")
    errors += validate_bench(bench_ids, include_ids, exclude_ids)

    # A declared bench, --weekly or --bench-boost all imply the full squad (ADR-013/045).
    full = args.full or bool(args.bench) or args.weekly or args.bench_boost
    budget = resolve_squad_budget(args.budget, full)
    # Bench-aware objective (ADR-045): --weekly maximises the XI (cheap playing bench). --bench-boost is the
    # default max-15 build with an "all 15 score" note — it cannot be a distinct build, because maximising the
    # XI plus a full-weight bench IS maximising all 15 (measured; ADR-137).
    # Both imply --full and are incompatible with a declared bench (which pins the split itself).
    bench_weight = WEEKLY_BENCH_WEIGHT if args.weekly else None
    if (args.weekly or args.bench_boost) and args.bench:
        errors.append("--weekly/--bench-boost can't be combined with --bench (it declares the bench).")

    # Choose the formation (ADR-014): the full squad is a fixed 2/5/5/3; the XI is a
    # pinned shape (--formation) or, by default, flexible (the solver picks the best).
    formation, size = (SQUAD_15, 15) if full else (XI_FLEX, 11)
    if args.formation is not None:
        if full:
            errors.append(
                "--formation applies to the starting XI, not the 15-man squad "
                "(--full/--bench). In the full squad your bench sets the shape."
            )
        else:
            formation, ferror = parse_formation(args.formation)
            if ferror:
                errors.append(ferror)

    if errors:
        for message in errors:
            print(message)
    else:
        # Availability (ADR-023): don't optimise over players who can't play, unless the
        # manager opts in — but keep anyone they forced in (include/bench), warned below.
        forced = set(include_ids) | set(bench_ids)
        if args.include_unavailable:
            pool, excluded = players, []
        else:
            pool, excluded = available_players(players, keep_ids=forced)

        # The xp objective uses the shared decision-xP (ADR-041) — the SAME xP transfer/analyse
        # use, so an xp-optimal squad has no free transfers. Other objectives are unchanged.
        weight_by_id = {}
        if args.objective == "xp":
            ranked = decision_xp(
                players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                minutes_weighted=not args.no_xmins,
                gw_history_by_code=store.get_gw_history_by_code(),   # in-season form (ADR-060; dormant now)
            )
            scores = {r["id"]: r["xp"] for r in ranked}
            weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}
        else:
            scores = objective_scores(players, args.objective)
        # Archetype constraints (ADR-043/044): ≥N low-cost / ≥M premium / ≥K differential, if asked.
        bands = archetype_bands(cheap=args.cheap, premium=args.premium)
        result = select_squad(
            pool, budget=budget, formation=formation, size=size,
            include_ids=include_ids, exclude_ids=exclude_ids, bench_ids=bench_ids,
            scores=scores, band_minimums=bands, min_differentials=args.differential,
            bench_weight=bench_weight,
        )
        if result["status"] != "Optimal" and (bands or args.differential):
            print(
                f"No squad fits those archetypes within £{budget:.1f}m "
                f"(cheap≥{args.cheap or 0}, premium≥{args.premium or 0}, "
                f"differential≥{args.differential or 0}) — relax the constraints or raise the budget."
            )
            return
        xi_ids = None
        if args.objective == "xp":   # US-121: show what we optimised — attach xP + xMins for the table
            for p in result["selected"]:
                p["xp"] = scores.get(p["id"], 0)
                p["minutes_weight"] = weight_by_id.get(p["id"], 1.0)
            # US-131: with no declared bench (and not bench-aware, which designates its own bench),
            # auto-derive the best XI for the breakout — display-only, the saved bench is unaffected.
            if full and not bench_ids and bench_weight is None:
                xi_ids = best_legal_xi(result["selected"], scores)
        print(render_squad(result, budget=budget, objective=args.objective, full=full,
                           xi_ids=xi_ids, bench_boost=args.bench_boost))

        # Save the computed squad (ADR-024) — the picks (ids + names) + bench, to reload later.
        if args.save and result["status"] == "Optimal":
            picked = result["selected"]
            bench_ids = [p["id"] for p in picked if p.get("bench")]
            SquadStore().save(
                args.save, [p["id"] for p in picked],
                player_names=[p["web_name"] for p in picked],
                bench_ids=bench_ids, cost=result["total_cost"],
            )
            print(f"Saved as '{args.save}' "
                  f"({len(picked)} players, £{result['total_cost']:.1f}m).")

        # Warn on any unavailable player the manager forced in, and report the rest.
        for p in players:
            if p["id"] in forced and is_unavailable(p):
                chance = f" ({p['chance']}%)" if p["chance"] is not None else ""
                print(f"⚠ {p['web_name']} is {_STATUS_WORD.get(p['status'], 'unavailable')}"
                      f"{chance} — forced in.")
        if excluded:
            worst = sorted(excluded, key=lambda p: -p["total_points"])[:3]
            listed = ", ".join(f"{p['web_name']} ({p['status']})" for p in worst)
            more = "…" if len(excluded) > 3 else ""
            print(f"({len(excluded)} unavailable excluded: {listed}{more} — "
                  "use --include-unavailable to keep them.)")
    store.close()


def cmd_cleansheet(args) -> None:
    """Rank DEF/GK by clean-sheet prospect — expected goals conceded per 90 (lowest best)."""
    store = Storage()
    players = store.get_players(position=args.pos.upper() if args.pos else None)
    rows = defensive_solidity(players, min_minutes=args.min_minutes)
    print(render_cleansheet(rows, limit=args.limit, min_minutes=args.min_minutes))
    store.close()


def cmd_defcon(args) -> None:
    """Rank players by Defensive Contribution reliability (per-90 vs threshold)."""
    store = Storage()
    players = store.get_players(position=args.pos.upper() if args.pos else None)
    rows = defcon_reliability(players, min_minutes=args.min_minutes)
    print(render_defcon(rows, limit=args.limit, min_minutes=args.min_minutes))
    store.close()


def cmd_overperf(args) -> None:
    """Show over/under-performers: actual vs expected attacking points (minutes-gated)."""
    store = Storage()
    players = store.get_players(position=args.pos.upper() if args.pos else None)
    rows = over_under(players, min_minutes=args.min_minutes)
    print(render_overperf(rows, limit=args.limit, min_minutes=args.min_minutes))
    store.close()


def cmd_xg(args) -> None:
    """Rank players by expected goal involvement (xGI = xG + xA)."""
    store = Storage()
    players = store.get_players(position=args.pos.upper() if args.pos else None)
    # get_players orders by points; the xg view ranks by xGI (None → 0.0).
    players = sorted(players, key=lambda p: (p["xgi"] or 0.0), reverse=True)
    if not players:
        print("No players to rank — run `refresh` first.")
    else:
        print(render_xg_table(players, limit=args.limit, pos=args.pos))
    store.close()


def cmd_xp(args) -> None:
    """Rank players by expected points (multi-season baseline rate; ADR-028)."""
    store = Storage()
    players = store.get_players(position=args.pos.upper() if args.pos else None)
    upcoming = store.get_upcoming_fixtures()
    if not players:
        print("No players to rank — run `refresh` first.")
    else:
        # Historical baseline rate per player (empty until `history --backfill` is run).
        baseline_by_code = {
            code: baseline_rate(rows)
            for code, rows in store.get_history_by_code().items()
        }
        ranked = player_xp(
            players, upcoming, source=args.type, horizon=args.next,
            baseline_by_code=baseline_by_code,
        )
        print(render_xp_table(
            ranked, limit=args.limit, source=args.type, horizon=args.next,
            by_gameweek=args.by_gameweek,
        ))
    store.close()


def cmd_captain(args) -> None:
    """Recommend the top captain picks for the next gameweek (ADR-029).

    With `--squad <name>`, candidates are drawn from a saved squad (ADR-024) — the real
    weekly question ("who do I captain from *my* team?"); otherwise from all players.
    """
    store = Storage()
    try:
        players = store.get_players()
        upcoming = store.get_upcoming_fixtures()
        if not players:
            print("No players — run `refresh` first.")
            return

        squad_name = None
        if args.squad:
            squad = SquadStore().load(args.squad)
            if squad is None:
                names = SquadStore().names()
                hint = f" Saved: {', '.join(names)}." if names else " None saved yet."
                print(f"No saved squad '{args.squad}'.{hint}")
                return
            squad_name = args.squad
            ids = set(squad["player_ids"])            # departed ids simply won't match
            players = [p for p in players if p["id"] in ids]
            if not players:
                print(f"Squad '{args.squad}' has no current players to captain.")
                return

        history_by_code = store.get_history_by_code()
        baseline_by_code = {code: baseline_rate(rows) for code, rows in history_by_code.items()}
        # xMins v0 (ADR-038): weight xP by expected minutes unless --no-xmins.
        minutes_weight = None if args.no_xmins else minutes_weight_from_history(history_by_code)
        picks = captain_picks(
            players, upcoming, baseline_by_code=baseline_by_code,
            source=args.type, limit=args.limit, minutes_weight=minutes_weight,
            history_by_code=history_by_code,
        )
        explanation = explain_captain(picks, {p["id"]: p for p in players})   # Why/Risk/Confidence (ADR-089)
        team_names = {t["short_name"]: t["name"] for t in store.get_teams()}  # "MUN" → "Man Utd" (US-278)
        print(render_captain_picks(picks, squad_name=squad_name, explanation=explanation,
                                   team_names=team_names))
    finally:
        store.close()


def cmd_ask(args) -> None:
    """Answer a natural-language question, grounded in the analytics (ADR-034).

    The analytics decide; a local LLM only narrates. Works without the LLM (degrades to the
    decision + facts). The last turn is remembered across runs (ADR-091), so a follow-up
    ("why?", "and the next?") works even as a separate `ask` command; `--forget` (or asking
    "forget"/"reset") clears it.
    """
    if getattr(args, "forget", False) or ask.is_reset(args.question):
        chat_context.clear_context()
        print("Okay — I've forgotten the last turn." if ask.is_reset(args.question)
              else "Conversation memory cleared.")
        if ask.is_reset(args.question):
            return
    store = Storage()
    try:
        result, new_ctx = ask.converse(args.question, chat_context.load_context(), store=store)
    finally:
        store.close()
    chat_context.save_context(new_ctx)          # local, single-user (ADR-091); the web never persists
    print(render_ask(result))


def _prompt_lines(prompt: str = "\n> "):
    """Yield lines typed at the REPL prompt, stopping cleanly on EOF (Ctrl-D) / interrupt."""
    while True:
        try:
            yield input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            return


def cmd_chat(args) -> None:
    """An interactive `ask` — follow-ups build on the last answer (ADR-047).

    Same discipline as `ask` (analytics decide, the LLM only narrates, every turn verified); the
    only new thing is memory of the last turn, so "why?" / "and the second best?" / "what about
    defenders?" build on it. Degrades without the LLM, exactly like `ask`.
    """
    store = Storage()
    resumed = chat_context.load_context()       # resume the last turn across runs (ADR-091)
    print('Chat with your FPL assistant. Ask a question, then follow up — "why?", "and the second '
          'best?", "what about defenders?". Type "forget" to start over, "quit" (or Ctrl-D) to exit.'
          + ("  (Resuming your last conversation.)" if resumed else ""))
    try:
        for result, ctx in ask.chat_transcript(_prompt_lines(), store=store, context=resumed):
            print(render_ask(result))
            chat_context.save_context(ctx)      # persist each turn (None after a "forget" → clears)
    finally:
        store.close()


def cmd_analyse(args) -> None:
    """Grade a saved squad's health over the next N gameweeks (ADR-031)."""
    store = Storage()
    try:
        squad = SquadStore().load(args.squad)
        if squad is None:
            names = SquadStore().names()
            hint = f" Saved: {', '.join(names)}." if names else " None saved yet."
            print(f"No saved squad '{args.squad}'.{hint}")
            return

        players = store.get_players()
        upcoming = store.get_upcoming_fixtures()
        if not players:
            print("No players — run `refresh` first.")
            return

        owned_ids = set(squad["player_ids"])
        owned = [p for p in players if p["id"] in owned_ids]   # departed ids drop out
        if not owned:
            print(f"Squad '{args.squad}' has no current players to analyse.")
            return

        # The shared decision-xP recipe (ADR-041) — the same xP squad/transfer/ask use.
        ranked = decision_xp(
            players, upcoming, store.get_history_by_code(),
            source=args.type, horizon=args.next, minutes_weighted=not args.no_xmins,
            gw_history_by_code=store.get_gw_history_by_code(),   # in-season form (ADR-060; dormant now)
        )
        xp_by_id = {r["id"]: r["xp"] for r in ranked}
        by_gameweek_by_id = {r["id"]: r["by_gameweek"] for r in ranked}
        weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}
        gameweeks = ranked[0]["gameweeks"] if ranked else []

        # The XI: the declared bench's complement, else the best legal XI (ADR-031; shared with
        # start/bench via best_legal_xi so they can't diverge, ADR-040).
        bench_ids = set(squad.get("bench_ids") or [])
        xi_ids = ({p["id"] for p in owned if p["id"] not in bench_ids} if bench_ids
                  else best_legal_xi(owned, xp_by_id))

        analysis = analyse_squad(
            owned, xi_ids, xp_by_id, horizon=args.next, sort=args.sort,
            by_gameweek_by_id=by_gameweek_by_id, gameweeks=gameweeks, weight_by_id=weight_by_id,
        )
        print(render_squad_analysis(analysis, args.squad, show_xmins=not args.no_xmins))
    finally:
        store.close()


def cmd_chips(args) -> None:
    """Advise when to play each chip for a saved squad (ADR-082) — the CLI edge over `chip_advisor`."""
    store = Storage()
    try:
        squad = SquadStore().load(args.squad)
        if squad is None:
            names = SquadStore().names()
            hint = f" Saved: {', '.join(names)}." if names else " None saved yet."
            print(f"No saved squad '{args.squad}'.{hint}")
            return

        players = store.get_players()
        upcoming = store.get_upcoming_fixtures()
        if not players:
            print("No players — run `refresh` first.")
            return

        owned = [p for p in players if p["id"] in set(squad["player_ids"])]   # departed ids drop out
        if not owned:
            print(f"Squad '{args.squad}' has no current players.")
            return

        # The shared decision-xP recipe (ADR-041) — so the CLI chip advice matches ask/web by construction.
        ranked = decision_xp(
            players, upcoming, store.get_history_by_code(),
            source=args.type, horizon=args.next, minutes_weighted=not args.no_xmins,
            gw_history_by_code=store.get_gw_history_by_code(),
        )
        by_gameweek_by_id = {r["id"]: r["by_gameweek"] for r in ranked}
        gameweeks = ranked[0]["gameweeks"] if ranked else []

        advice = chip_advisor(owned, by_gameweek_by_id, gameweeks)
        if advice is None:
            print("Not enough data to advise on chips yet — try after `refresh`.")
            return
        print(render_chip_advice(advice, args.squad, horizon=args.next, confidences=explain_chips(advice)))
    finally:
        store.close()


def cmd_transfer(args) -> None:
    """Suggest the best single transfers for a saved squad (ADR-030)."""
    store = Storage()
    try:
        squad = SquadStore().load(args.squad)
        if squad is None:
            names = SquadStore().names()
            hint = f" Saved: {', '.join(names)}." if names else " None saved yet."
            print(f"No saved squad '{args.squad}'.{hint}")
            return

        players = store.get_players()
        upcoming = store.get_upcoming_fixtures()
        if not players:
            print("No players — run `refresh` first.")
            return

        owned_ids = set(squad["player_ids"])
        owned = [p for p in players if p["id"] in owned_ids]   # departed ids drop out
        if not owned:
            print(f"Squad '{args.squad}' has no current players to improve.")
            return

        # The shared decision-xP recipe (ADR-041) — the same xP squad/analyse/ask use.
        show_xmins = not args.no_xmins
        ranked = decision_xp(
            players, upcoming, store.get_history_by_code(),
            source=args.type, horizon=args.next, minutes_weighted=show_xmins,
            gw_history_by_code=store.get_gw_history_by_code(),   # in-season form (ADR-060; dormant now)
        )
        xp_by_id = {r["id"]: r["xp"] for r in ranked}
        bench_ids = squad.get("bench_ids", [])
        xi_aware = not args.raw   # XI-gain ranking by default; --raw for the old raw-player-gain (ADR-046)

        # ADR-136 — a slot that cannot score is invisible to an XI-gain ranking, so it is asked for
        # separately and printed first. Silent (empty string) when the 15 are all able to play.
        banner = render_dead_slots(
            replace_dead(owned, players, xp_by_id, upcoming, bench_ids=bench_ids, bank=args.bank,
                         horizon=args.next, today=datetime.now(UTC).date()),
            horizon=args.next,
        )
        if banner:
            print(banner)

        if args.count:
            # Plan mode: a coordinated set of `count` transfers (ADR-035), with the incoming
            # players' per-gameweek xP shown (ADR-036).
            plan = suggest_transfer_plan(
                owned, players, xp_by_id, bench_ids=bench_ids, bank=args.bank, count=args.count,
                xi_aware=xi_aware,
            )
            print(render_transfer_plan(
                plan, args.squad, bank=args.bank, horizon=args.next,
                by_gameweek_by_id={r["id"]: r["by_gameweek"] for r in ranked},
                gameweeks=ranked[0]["gameweeks"] if ranked else [], show_xmins=show_xmins,
                xi_aware=xi_aware, has_dead=bool(banner),
            ))
        else:
            suggestions = suggest_transfers(
                owned, players, xp_by_id, bench_ids=bench_ids, bank=args.bank, limit=args.limit,
                xi_aware=xi_aware,
            )
            print(render_transfers(
                suggestions, args.squad, bank=args.bank, horizon=args.next, show_xmins=show_xmins,
                xi_aware=xi_aware, has_dead=bool(banner),
            ))
    finally:
        store.close()


def cmd_fdr(args) -> None:
    """Rank teams by how easy their upcoming fixtures are."""
    store = Storage()
    upcoming = store.get_upcoming_fixtures()
    if not upcoming:
        print("No upcoming fixtures — run `refresh` first.")
    else:
        elo_bands = elo_difficulty_bands(store.get_teams()) if args.type == "elo" else None
        ranked = team_fdr(upcoming, next_n=args.next, source=args.type, elo_bands=elo_bands)
        print(render_fdr_table(ranked, next_n=args.next, source=args.type))
    store.close()


def cmd_fixtures(args) -> None:
    """List a single team's upcoming fixtures."""
    team = args.team.upper()
    store = Storage()
    upcoming = store.get_upcoming_fixtures(team=team)
    schedule = team_schedule(upcoming, team, source=args.type)
    if args.next is not None:
        schedule = schedule[: args.next]
    print(render_team_fixtures(schedule, team, source=args.type))
    store.close()


def cmd_filter(args) -> None:
    """Show players matching the given position / team / max price."""
    store = Storage()
    rows = store.get_players(
        position=args.pos.upper() if args.pos else None,
        team=args.team.upper() if args.team else None,
        max_price=args.max_price,
    )
    if not rows:
        print("No players match those filters.")
    else:
        print(render_player_table(rank_players(rows)))
    store.close()


# The dormant weights the calibration backtest can tune (ADR-101), mapped to their config attribute.
_CALIBRATE_WEIGHTS = {"form": "FORM_WEIGHT", "set_piece": "SET_PIECE_WEIGHT", "defcon": "DEFCON_MAGNIFIER_WEIGHT"}


def _parse_range(spec: str) -> list[float]:
    """`"start,stop,step"` → an inclusive list of weight values (e.g. `"0,0.5,0.05"`)."""
    start, stop, step = (float(x) for x in spec.split(","))
    values, v = [], start
    while v <= stop + 1e-9:
        values.append(round(v, 6))
        v += step
    return values


def cmd_calibrate(args) -> None:
    """Calibrate a dormant weight on **real returns** via a walk-forward backtest (ADR-101).

    Sweeps a weight (default `form`) and prints the rank correlation (+ MAE / hit-rate) per value plus a
    recommendation — or, until enough gameweeks have been played (~GW4+), that there isn't enough data yet.
    **Read-only:** it never changes the weight; the owner commits the recommended value (see docs/GW1_RUNBOOK.md).
    """
    from src.analytics import backtest
    from src.analytics.xp import decision_xp

    weight = args.weight
    attr = _CALIBRATE_WEIGHTS[weight]
    values = _parse_range(args.range) if args.range else _parse_range("0,0.5,0.05")

    store = Storage()
    try:
        gw_history = store.get_gw_history_by_code()
        played = backtest.rounds_with_actuals(gw_history)
        if len(played) < backtest.MIN_GWS:
            print(f"Not enough gameweeks yet — have {len(played)}, need ≥{backtest.MIN_GWS}. "
                  "Real calibration is ~GW4+ once returns accrue (see docs/GW1_RUNBOOK.md).")
            return

        players = store.get_players()
        history = store.get_history_by_code()
        code_by_id = store.get_player_codes()          # id → stable element_code (to key predictions like actuals)
        fixtures_cache: dict[int, list] = {}

        def make_predict(value):
            def predict(before, n):
                upcoming = fixtures_cache.setdefault(n, store.get_fixtures_by_event(n))
                old = getattr(config, attr)
                setattr(config, attr, value)               # sweep the weight for this decision_xp run (restored below)
                try:
                    ranked = decision_xp(players, upcoming, history, horizon=1, gw_history_by_code=before)
                finally:
                    setattr(config, attr, old)
                return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
            return predict

        result = backtest.sweep(gw_history, make_predict, values)
    finally:
        store.close()

    print(f"Calibrating {weight} ({attr}) over {result['gws']} gameweeks — walk-forward, rank correlation (ADR-101).\n")
    print(f"  {'weight':>7}  {'ρ (rank)':>9}  {'MAE':>6}  {'hit@20':>6}")
    for row in result["rows"]:
        rho = f"{row['spearman']:.3f}" if row["spearman"] is not None else "   —"
        mae = f"{row['mae']:.2f}" if row["mae"] is not None else "  —"
        hit = f"{row['hit_rate']:.2f}" if row["hit_rate"] is not None else "  —"
        print(f"  {row['weight']:>7.3f}  {rho:>9}  {mae:>6}  {hit:>6}")
    if result["best"] is not None:
        print(f"\nRecommended {attr} ≈ {result['best']:.3f} (highest rank correlation; the smaller value on a flat "
              f"curve). Set it in config.py + update the invariance test, then commit (docs/GW1_RUNBOOK.md).")
    else:
        print("\nNo clear signal yet — leave the weight at 0 and re-run as more gameweeks play.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="madboots",
        description="MADBOOTS — a personal Fantasy Premier League analytics assistant.",
        epilog=(
            "Examples:\n"
            "  python app.py refresh\n"
            "  python app.py reseed                       refresh + update the deployed app's seed\n"
            "  python app.py table --sort value          rank players by value (points per £m)\n"
            "  python app.py search haaland\n"
            "  python app.py filter --pos DEF --max-price 6\n"
            "  python app.py fdr --next 5                teams with the easiest upcoming fixtures\n"
            "  python app.py fixtures --team ARS\n"
            "  python app.py xp --type custom --next 5   players by expected points over the next N gameweeks\n"
            "  python app.py xg --pos FWD                players by expected goal involvement (xG + xA)\n"
            "  python app.py overperf                   over/under-performers (actual vs expected pts)\n"
            "  python app.py defcon                     reliable Defensive Contribution earners\n"
            "  python app.py cleansheet                 best clean-sheet prospects (DEF/GK by xGC/90)\n"
            "  python app.py squad --objective value     optimal XI (maximise points / value / xp)\n"
            "  python app.py squad --formation 3-5-2     pin the XI shape (default: best legal shape)\n"
            "  python app.py squad --full --bench Dubravka Diop  full 15-man squad; declare your bench\n"
            "\n"
            "Run 'python app.py <command> --help' for a command's options."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    p_refresh = sub.add_parser(
        "refresh",
        help="Fetch the latest FPL data (players, teams, fixtures) and store it locally",
    )
    p_refresh.set_defaults(handler=cmd_refresh)

    p_reseed = sub.add_parser(
        "reseed",
        help="Refresh the live cache and copy it to the committed seed (updates the deployed app)",
    )
    p_reseed.set_defaults(handler=cmd_reseed)

    p_history = sub.add_parser(
        "history", help="A player's season history (`history <player>`), or --backfill to fetch it"
    )
    p_history.add_argument(
        "player", nargs="?",
        help="Show this player's past-season record + this-season per-GW trend (e.g. `history Haaland`)",
    )
    p_history.add_argument(
        "--backfill", action="store_true",
        help="Fetch and store each player's past-season summaries (a few minutes)",
    )
    p_history.add_argument(
        "--limit", type=int,
        help="Only backfill the first N players (useful for a quick test run)",
    )
    p_history.set_defaults(handler=cmd_history)

    p_ask = sub.add_parser(
        "ask", help="Ask a natural-language question, grounded in the analytics (local LLM)"
    )
    p_ask.add_argument("question", help='e.g. "who should I captain from my-team?"')
    p_ask.add_argument("--forget", action="store_true",
                       help="Clear the remembered conversation before answering (ADR-091)")
    p_ask.set_defaults(handler=cmd_ask)

    p_chat = sub.add_parser(
        "chat", help='Interactive `ask` — follow-ups ("why?", "and the second best?") build on the last'
    )
    p_chat.set_defaults(handler=cmd_chat)

    p_table = sub.add_parser(
        "table", help="Show players, ranked by points or value (points per £m)"
    )
    p_table.add_argument(
        "--limit", type=int, default=20, help="How many players to show (default 20)"
    )
    p_table.add_argument(
        "--sort",
        choices=["points", "value"],
        default="points",
        help="Sort by total points (default) or value (points per £m)",
    )
    p_table.set_defaults(handler=cmd_table)

    p_search = sub.add_parser("search", help="Search players by name")
    p_search.add_argument("name", help="Name (or part of a name) to search for")
    p_search.set_defaults(handler=cmd_search)

    p_xp = sub.add_parser("xp", help="Rank players by expected points (next gameweek)")
    p_xp.add_argument(
        "--type", choices=["fpl", "custom"], default="fpl",
        help="Difficulty source used in the xP calc (default fpl)",
    )
    p_xp.add_argument("--pos", help="Filter to a position: GK, DEF, MID or FWD")
    p_xp.add_argument(
        "--next", type=int, default=1,
        help="Horizon: sum xP over the next N gameweeks (default 1)",
    )
    p_xp.add_argument(
        "--limit", type=int, default=20, help="How many players to show (default 20)",
    )
    p_xp.add_argument(
        "--by-gameweek", action="store_true",
        help="Show a per-gameweek xP breakdown (a GW column per gameweek in the horizon)",
    )
    p_xp.set_defaults(handler=cmd_xp)

    p_captain = sub.add_parser(
        "captain", help="Recommend captain picks for the next gameweek (by xP)"
    )
    p_captain.add_argument(
        "--type", choices=["fpl", "custom"], default="fpl",
        help="Difficulty source used in the xP calc (default fpl)",
    )
    p_captain.add_argument(
        "--limit", type=int, default=5, help="How many candidates to show (default 5)",
    )
    p_captain.add_argument(
        "--squad", help="Only consider players from a saved squad (see `squad --save`)",
    )
    p_captain.add_argument(
        "--no-xmins", action="store_true",
        help="Don't weight xP by expected minutes (xMins v0) — show the raw 'assumes 90' number",
    )
    p_captain.set_defaults(handler=cmd_captain)

    p_transfer = sub.add_parser(
        "transfer", help="Suggest the best single transfers for a saved squad"
    )
    p_transfer.add_argument(
        "--squad", required=True, help="The saved squad to improve (see `squad --save`)",
    )
    p_transfer.add_argument(
        "--bank", type=float, default=0.0,
        help="Money in the bank, £m — adds to each sale's budget (default 0, self-funding)",
    )
    p_transfer.add_argument(
        "--next", type=int, default=5,
        help="Horizon: compare xP over the next N gameweeks (default 5)",
    )
    p_transfer.add_argument(
        "--type", choices=["fpl", "custom"], default="fpl",
        help="Difficulty source used in the xP calc (default fpl)",
    )
    p_transfer.add_argument(
        "--limit", type=int, default=5, help="How many suggestions to show (default 5)",
    )
    p_transfer.add_argument(
        "--count", type=int,
        help="Plan a coordinated set of N transfers (shared bank) instead of a shortlist",
    )
    p_transfer.add_argument(
        "--raw", action="store_true",
        help="Rank by raw player xP gain (the old default) instead of the best-XI improvement",
    )
    p_transfer.add_argument(
        "--no-xmins", action="store_true",
        help="Don't weight xP by expected minutes (xMins v0) — show the raw 'assumes 90' number",
    )
    p_transfer.set_defaults(handler=cmd_transfer)

    p_analyse = sub.add_parser(
        "analyse", help="Grade a saved squad's health over the next N gameweeks"
    )
    p_analyse.add_argument(
        "--squad", required=True, help="The saved squad to analyse (see `squad --save`)",
    )
    p_analyse.add_argument(
        "--next", type=int, default=5,
        help="Horizon: project xP over the next N gameweeks (default 5)",
    )
    p_analyse.add_argument(
        "--type", choices=["fpl", "custom"], default="fpl",
        help="Difficulty source used in the xP calc (default fpl)",
    )
    p_analyse.add_argument(
        "--sort", choices=["position", "xp"], default="position",
        help="Order the XI by formation position (default) or by xP",
    )
    p_analyse.add_argument(
        "--no-xmins", action="store_true",
        help="Don't weight xP by expected minutes (xMins v0) — show the raw 'assumes 90' number",
    )
    p_analyse.set_defaults(handler=cmd_analyse)

    p_chips = sub.add_parser(
        "chips", help="Advise when to play each chip (Triple Captain · Bench Boost · Free Hit · Wildcard)"
    )
    p_chips.add_argument("--squad", required=True, help="The saved squad to advise on (see `squad --save`)")
    p_chips.add_argument("--next", type=int, default=8,
                         help="Horizon: look for the best chip gameweek over the next N (default 8)")
    p_chips.add_argument("--type", choices=["fpl", "custom"], default="fpl",
                         help="Difficulty source used in the xP calc (default fpl)")
    p_chips.add_argument("--no-xmins", action="store_true",
                         help="Don't weight xP by expected minutes (xMins v0)")
    p_chips.set_defaults(handler=cmd_chips)

    p_xg = sub.add_parser("xg", help="Rank players by expected goal involvement (xG + xA)")
    p_xg.add_argument("--pos", help="Filter to a position: GK, DEF, MID or FWD")
    p_xg.add_argument(
        "--limit", type=int, default=20, help="How many players to show (default 20)",
    )
    p_xg.set_defaults(handler=cmd_xg)

    p_op = sub.add_parser(
        "overperf", help="Over/under-performers: actual vs expected attacking points",
    )
    p_op.add_argument("--pos", help="Filter to a position: GK, DEF, MID or FWD")
    p_op.add_argument(
        "--limit", type=int, default=10, help="How many per end to show (default 10)",
    )
    p_op.add_argument(
        "--min-minutes", type=int, default=900, dest="min_minutes",
        help="Only rank players with at least this many minutes (default 900)",
    )
    p_op.set_defaults(handler=cmd_overperf)

    p_dc = sub.add_parser(
        "defcon", help="Rank players by Defensive Contribution reliability (per-90 vs threshold)",
    )
    p_dc.add_argument("--pos", help="Filter to a position: DEF, MID or FWD (GK not eligible)")
    p_dc.add_argument(
        "--limit", type=int, default=20, help="How many players to show (default 20)",
    )
    p_dc.add_argument(
        "--min-minutes", type=int, default=900, dest="min_minutes",
        help="Only rank players with at least this many minutes (default 900)",
    )
    p_dc.set_defaults(handler=cmd_defcon)

    p_cs = sub.add_parser(
        "cleansheet", help="Rank DEF/GK by clean-sheet prospect (expected goals conceded per 90)",
    )
    p_cs.add_argument("--pos", help="Filter to a position: DEF or GK")
    p_cs.add_argument(
        "--limit", type=int, default=20, help="How many players to show (default 20)",
    )
    p_cs.add_argument(
        "--min-minutes", type=int, default=900, dest="min_minutes",
        help="Only rank players with at least this many minutes (default 900)",
    )
    p_cs.set_defaults(handler=cmd_cleansheet)

    p_squad = sub.add_parser("squad", help="Pick the optimal squad (starting XI, or --full 15)")
    p_squad.add_argument(
        "--full", action="store_true",
        help="Pick the full 15-man squad (2/5/5/3, £100m) — choose the bench with --include",
    )
    p_squad.add_argument(
        "--budget", type=float, default=None,
        help="Budget in £m (default 80 for the XI, 100 for --full)",
    )
    p_squad.add_argument(
        "--include", nargs="*", default=[], metavar="NAME",
        help="Force these players in (web_name, or Name:TEAM; quote multi-word names)",
    )
    p_squad.add_argument(
        "--exclude", nargs="*", default=[], metavar="NAME",
        help="Keep these players out",
    )
    p_squad.add_argument(
        "--bench", nargs="*", default=[], metavar="NAME",
        help="Declare 1-4 players as your bench (marked **, shown last); implies --full",
    )
    p_squad.add_argument(
        "--formation", default=None, metavar="D-M-F",
        help="Pin the XI shape, e.g. 3-5-2 (DEF-MID-FWD); default picks the best legal shape",
    )
    p_squad.add_argument(
        "--objective", choices=["points", "value", "xp", "xgi"], default="xp",
        help="What to maximise: xP (default; expected points next 5 GW), points (last-season "
             "total), value (£m), or xGI (attacking)",
    )
    p_squad.add_argument(
        "--no-xmins", action="store_true",
        help="With --objective xp: don't weight by expected minutes (xMins v0) — the raw view",
    )
    p_squad.add_argument(
        "--cheap", type=int, metavar="N",
        help="Require at least N low-cost (≤£4.5m) players — bench enablers (ADR-043)",
    )
    p_squad.add_argument(
        "--premium", type=int, metavar="N",
        help="Require at least N premium (≥£9.0m) players",
    )
    p_squad.add_argument(
        "--differential", type=int, metavar="N",
        help="Require at least N differential (≤5%% owned) players — off-template picks (ADR-044)",
    )
    p_bench_mode = p_squad.add_mutually_exclusive_group()
    p_bench_mode.add_argument(
        "--weekly", action="store_true",
        help="Bench-aware build: maximise the starting XI with a cheap, still-playing bench (ADR-045)",
    )
    p_bench_mode.add_argument(
        # ADR-137: this does NOT change the build and never did — the default already maximises all 15, and
        # "maximise Σ score·start + 1·score·bench" is the same objective. The flag adds the chip note.
        "--bench-boost", action="store_true", dest="bench_boost",
        help="Add the 'all 15 score this week' note for a Bench Boost week (the default build already "
             "maximises all 15 — this changes the wording, not the squad)",
    )
    p_squad.add_argument(
        "--include-unavailable", action="store_true", dest="include_unavailable",
        help="Also consider injured/suspended players (excluded by default)",
    )
    p_squad.add_argument(
        "--save", metavar="NAME", default=None,
        help="Save the computed squad under a name (reload it later with --load)",
    )
    p_squad.add_argument(
        "--load", metavar="NAME", default=None,
        help="Reload a saved squad — re-priced, with current availability and any departures",
    )
    p_squad.set_defaults(handler=cmd_squad)

    p_fdr = sub.add_parser("fdr", help="Rank teams by upcoming fixture difficulty")
    p_fdr.add_argument(
        "--next", type=int, default=5,
        help="How many upcoming fixtures to average (default 5)",
    )
    p_fdr.add_argument(
        "--type", choices=["fpl", "custom", "elo"], default="fpl",
        help="Difficulty source: FPL's rating (default), our custom one, or ClubElo",
    )
    p_fdr.set_defaults(handler=cmd_fdr)

    p_fixtures = sub.add_parser("fixtures", help="List a team's upcoming fixtures")
    p_fixtures.add_argument("--team", required=True, help="Team short name, e.g. ARS")
    p_fixtures.add_argument(
        "--next", type=int, default=None, help="Limit to the next N fixtures",
    )
    p_fixtures.add_argument(
        "--type", choices=["fpl", "custom"], default="fpl",
        help="Difficulty source: FPL's rating (default) or our custom one",
    )
    p_fixtures.set_defaults(handler=cmd_fixtures)

    p_filter = sub.add_parser(
        "filter", help="Filter players by position, team or max price"
    )
    p_filter.add_argument("--pos", help="Position: GK, DEF, MID or FWD")
    p_filter.add_argument("--team", help="Team short name, e.g. ARS")
    p_filter.add_argument("--max-price", type=float, help="Maximum price in £m")
    p_filter.set_defaults(handler=cmd_filter)

    p_cal = sub.add_parser(
        "calibrate", help="Backtest a dormant weight on real returns + recommend a value (ADR-101; ~GW4+)")
    p_cal.add_argument("--weight", choices=list(_CALIBRATE_WEIGHTS), default="form",
                       help="Which dormant weight to calibrate (default form)")
    p_cal.add_argument("--range", help="Sweep as 'start,stop,step' (default '0,0.5,0.05')")
    p_cal.set_defaults(handler=cmd_calibrate)

    return parser


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)

    # No command given → show help rather than doing nothing silently.
    if not getattr(args, "handler", None):
        build_parser().print_help()
        return

    args.handler(args)
