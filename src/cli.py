"""Command-line interface — the interaction layer.

This is the only place that decides *what the user asked for*. It parses the
command line and dispatches to a handler; each handler then calls the existing
layers (client, storage, display). The CLI itself contains no FPL logic — keeping
it thin is what makes the app easy to extend (add a command) and easy to test.

See ADR-003 for why this is argparse + subcommands.
"""

import argparse

from src import config, ingest
from src.analytics import (
    DEFAULT_BUDGET,
    FULL_BUDGET,
    SQUAD_15,
    XI_FLEX,
    elo_difficulty_bands,
    objective_scores,
    player_xp,
    rank_players,
    resolve_players,
    select_squad,
    team_fdr,
    team_schedule,
)
from src.api.client import FplApiError
from src.storage import Storage
from src.ui.fdr import render_fdr_table
from src.ui.fixtures import render_team_fixtures
from src.ui.squad import render_squad
from src.ui.table import render_player_table
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


def cmd_squad(args) -> None:
    """Pick the optimal squad — the starting XI, or the full 15 with `--full`."""
    store = Storage()
    players = store.get_players()

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

    # A declared bench implies the full squad — an XI has no bench (ADR-013).
    full = args.full or bool(args.bench)
    budget = resolve_squad_budget(args.budget, full)

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
        upcoming = store.get_upcoming_fixtures() if args.objective == "xp" else None
        scores = objective_scores(players, args.objective, upcoming)
        result = select_squad(
            players, budget=budget, formation=formation, size=size,
            include_ids=include_ids, exclude_ids=exclude_ids, bench_ids=bench_ids,
            scores=scores,
        )
        print(render_squad(result, budget=budget, objective=args.objective, full=full))
    store.close()


def cmd_xp(args) -> None:
    """Rank players by expected points for their team's next fixture."""
    store = Storage()
    players = store.get_players(position=args.pos.upper() if args.pos else None)
    upcoming = store.get_upcoming_fixtures()
    if not players:
        print("No players to rank — run `refresh` first.")
    else:
        ranked = player_xp(players, upcoming, source=args.type, horizon=args.next)
        print(render_xp_table(ranked, limit=args.limit, source=args.type, horizon=args.next))
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fpl-assistant",
        description="A personal Fantasy Premier League analytics assistant.",
        epilog=(
            "Examples:\n"
            "  python app.py refresh\n"
            "  python app.py table --sort value          rank players by value (points per £m)\n"
            "  python app.py search haaland\n"
            "  python app.py filter --pos DEF --max-price 6\n"
            "  python app.py fdr --next 5                teams with the easiest upcoming fixtures\n"
            "  python app.py fixtures --team ARS\n"
            "  python app.py xp --type custom --next 5   players by expected points over the next N gameweeks\n"
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
    p_xp.set_defaults(handler=cmd_xp)

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
        "--objective", choices=["points", "value", "xp"], default="points",
        help="What to maximise: last-season points (default), value (£m), or xP",
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

    return parser


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)

    # No command given → show help rather than doing nothing silently.
    if not getattr(args, "handler", None):
        build_parser().print_help()
        return

    args.handler(args)
