"""Tests for the CLI argument parser (the interaction layer's wiring).

These check that commands and options are parsed into the right shape and routed
to the right handler — no database or network involved.
"""

from src.cli import build_parser, cmd_filter, cmd_search, cmd_table


def test_table_command_defaults_to_limit_20():
    args = build_parser().parse_args(["table"])
    assert args.command == "table"
    assert args.limit == 20
    assert args.handler is cmd_table


def test_table_limit_option_is_parsed():
    args = build_parser().parse_args(["table", "--limit", "5"])
    assert args.limit == 5


def test_search_takes_a_name():
    args = build_parser().parse_args(["search", "haaland"])
    assert args.command == "search"
    assert args.name == "haaland"
    assert args.handler is cmd_search


def test_filter_options_are_parsed():
    args = build_parser().parse_args(["filter", "--pos", "MID", "--max-price", "8"])
    assert args.pos == "MID"
    assert args.max_price == 8.0
    assert args.handler is cmd_filter


def test_no_command_leaves_no_handler():
    # main() prints help in this case; here we just confirm the parsed shape.
    args = build_parser().parse_args([])
    assert getattr(args, "handler", None) is None
