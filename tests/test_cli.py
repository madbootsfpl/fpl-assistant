"""Tests for the CLI argument parser (the interaction layer's wiring).

These check that commands and options are parsed into the right shape and routed
to the right handler — no database or network involved.
"""

import pytest

from src.cli import (
    build_parser,
    cmd_fdr,
    cmd_filter,
    cmd_fixtures,
    cmd_search,
    cmd_squad,
    cmd_table,
    cmd_xp,
    resolve_squad_budget,
    validate_bench,
)


def test_table_command_defaults_to_limit_20():
    args = build_parser().parse_args(["table"])
    assert args.command == "table"
    assert args.limit == 20
    assert args.handler is cmd_table


def test_table_defaults_to_sort_by_points():
    args = build_parser().parse_args(["table"])
    assert args.sort == "points"


def test_table_sort_value_is_parsed():
    args = build_parser().parse_args(["table", "--sort", "value"])
    assert args.sort == "value"


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


def test_fdr_defaults_to_next_5():
    args = build_parser().parse_args(["fdr"])
    assert args.command == "fdr"
    assert args.next == 5
    assert args.handler is cmd_fdr


def test_fdr_next_option_is_parsed():
    args = build_parser().parse_args(["fdr", "--next", "3"])
    assert args.next == 3


def test_fdr_defaults_to_type_fpl():
    args = build_parser().parse_args(["fdr"])
    assert args.type == "fpl"


def test_fdr_type_custom_is_parsed():
    args = build_parser().parse_args(["fdr", "--type", "custom"])
    assert args.type == "custom"


def test_fdr_type_elo_is_parsed():
    args = build_parser().parse_args(["fdr", "--type", "elo"])
    assert args.type == "elo"


def test_fixtures_requires_a_team():
    # --team is required, so parsing without it exits (argparse error).
    with pytest.raises(SystemExit):
        build_parser().parse_args(["fixtures"])


def test_fixtures_team_is_parsed():
    args = build_parser().parse_args(["fixtures", "--team", "ARS"])
    assert args.command == "fixtures"
    assert args.team == "ARS"
    assert args.handler is cmd_fixtures


def test_fixtures_defaults_to_type_fpl():
    args = build_parser().parse_args(["fixtures", "--team", "ARS"])
    assert args.type == "fpl"


def test_fixtures_type_custom_is_parsed():
    args = build_parser().parse_args(["fixtures", "--team", "ARS", "--type", "custom"])
    assert args.type == "custom"


def test_xp_defaults():
    args = build_parser().parse_args(["xp"])
    assert args.command == "xp"
    assert args.type == "fpl"
    assert args.limit == 20
    assert args.next == 1          # single-gameweek by default
    assert args.handler is cmd_xp


def test_squad_budget_defaults_to_none_and_is_not_full():
    # The mode-dependent default (80 XI / 100 full) is resolved in the handler, so the
    # parser leaves --budget as None.
    args = build_parser().parse_args(["squad"])
    assert args.command == "squad"
    assert args.budget is None
    assert args.full is False
    assert args.handler is cmd_squad


def test_squad_full_flag_is_parsed():
    args = build_parser().parse_args(["squad", "--full"])
    assert args.full is True
    assert args.budget is None


def test_squad_budget_is_parsed():
    args = build_parser().parse_args(["squad", "--budget", "75"])
    assert args.budget == 75.0


def test_resolve_squad_budget_defaults_by_mode():
    assert resolve_squad_budget(None, full=False) == 80.0    # the XI default
    assert resolve_squad_budget(None, full=True) == 100.0    # the 15-man default


def test_resolve_squad_budget_honours_an_explicit_value():
    assert resolve_squad_budget(90.0, full=False) == 90.0
    assert resolve_squad_budget(90.0, full=True) == 90.0     # explicit wins in both modes


def test_squad_bench_is_parsed_as_a_list():
    args = build_parser().parse_args(["squad", "--bench", "Dubravka", "Diop"])
    assert args.bench == ["Dubravka", "Diop"]


def test_squad_bench_defaults_empty():
    args = build_parser().parse_args(["squad"])
    assert args.bench == []


def test_validate_bench_accepts_a_clean_bench():
    assert validate_bench([1, 2], include_ids=[3], exclude_ids=[4]) == []


def test_validate_bench_caps_at_four():
    errors = validate_bench([1, 2, 3, 4, 5], include_ids=[], exclude_ids=[])
    assert len(errors) == 1 and "at most 4" in errors[0]


def test_validate_bench_rejects_include_and_bench():
    errors = validate_bench([1], include_ids=[1], exclude_ids=[])
    assert any("--include and --bench" in e for e in errors)


def test_validate_bench_rejects_bench_and_exclude():
    errors = validate_bench([1], include_ids=[], exclude_ids=[1])
    assert any("--bench and --exclude" in e for e in errors)


def test_squad_include_exclude_are_parsed_as_lists():
    args = build_parser().parse_args(
        ["squad", "--include", "Haaland", "Gabriel", "--exclude", "Salah"]
    )
    assert args.include == ["Haaland", "Gabriel"]
    assert args.exclude == ["Salah"]


def test_squad_include_exclude_default_empty():
    args = build_parser().parse_args(["squad"])
    assert args.include == []
    assert args.exclude == []


def test_squad_defaults_to_objective_points():
    args = build_parser().parse_args(["squad"])
    assert args.objective == "points"


def test_squad_objective_is_parsed():
    args = build_parser().parse_args(["squad", "--objective", "value"])
    assert args.objective == "value"


def test_xp_options_are_parsed():
    args = build_parser().parse_args(
        ["xp", "--type", "custom", "--pos", "MID", "--limit", "5", "--next", "6"]
    )
    assert args.type == "custom"
    assert args.pos == "MID"
    assert args.limit == 5
    assert args.next == 6


def test_no_command_leaves_no_handler():
    # main() prints help in this case; here we just confirm the parsed shape.
    args = build_parser().parse_args([])
    assert getattr(args, "handler", None) is None
