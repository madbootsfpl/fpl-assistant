"""Command-line interface — the interaction layer.

This is the only place that decides *what the user asked for*. It parses the
command line and dispatches to a handler; each handler then calls the existing
layers (client, storage, display). The CLI itself contains no FPL logic — keeping
it thin is what makes the app easy to extend (add a command) and easy to test.

See ADR-003 for why this is argparse + subcommands.
"""

import argparse

from src import config, ingest
from src.analytics import rank_players, team_fdr
from src.api.client import FplApiError
from src.storage import Storage
from src.ui.fdr import render_fdr_table
from src.ui.table import render_player_table


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
        n_players, n_teams, n_fixtures = ingest.refresh(store)
        print(
            f"Refreshed {n_players} players, {n_teams} teams and "
            f"{n_fixtures} fixtures into {config.DB_PATH}."
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


def cmd_fdr(args) -> None:
    """Rank teams by how easy their upcoming fixtures are."""
    store = Storage()
    upcoming = store.get_upcoming_fixtures()
    if not upcoming:
        print("No upcoming fixtures — run `refresh` first.")
    else:
        ranked = team_fdr(upcoming, next_n=args.next)
        print(render_fdr_table(ranked, next_n=args.next))
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
    )
    sub = parser.add_subparsers(dest="command")

    p_refresh = sub.add_parser("refresh", help="Re-fetch FPL data and store it locally")
    p_refresh.set_defaults(handler=cmd_refresh)

    p_table = sub.add_parser("table", help="Show stored players as a table")
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

    p_fdr = sub.add_parser("fdr", help="Rank teams by upcoming fixture difficulty")
    p_fdr.add_argument(
        "--next", type=int, default=5,
        help="How many upcoming fixtures to average (default 5)",
    )
    p_fdr.set_defaults(handler=cmd_fdr)

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
