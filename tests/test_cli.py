"""Tests for the CLI argument parser (the interaction layer's wiring).

These check that commands and options are parsed into the right shape and routed
to the right handler — no database or network involved.
"""

import pytest

from src.cli import (
    build_parser,
    cmd_analyse,
    cmd_captain,
    cmd_fdr,
    cmd_filter,
    cmd_fixtures,
    cmd_search,
    cmd_squad,
    cmd_table,
    cmd_transfer,
    cmd_xp,
    parse_formation,
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


def test_squad_formation_defaults_to_none_and_is_parsed():
    assert build_parser().parse_args(["squad"]).formation is None
    assert build_parser().parse_args(["squad", "--formation", "3-5-2"]).formation == "3-5-2"


def test_parse_formation_accepts_a_legal_shape():
    formation, error = parse_formation("3-5-2")
    assert error is None
    assert formation == {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2}


def test_parse_formation_rejects_out_of_range():
    _, error = parse_formation("6-3-1")          # DEF 6 > 5
    assert error is not None and "DEF" in error


def test_parse_formation_rejects_wrong_outfield_total():
    _, error = parse_formation("3-5-3")          # sums to 11, not 10
    assert error is not None and "10" in error


def test_parse_formation_rejects_non_numeric():
    _, error = parse_formation("foo")
    assert error is not None and "three numbers" in error


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


def test_squad_archetype_flags_are_parsed():
    # ADR-043/044: --cheap / --premium / --differential add archetype constraints; absent → None.
    args = build_parser().parse_args(
        ["squad", "--full", "--cheap", "3", "--premium", "1", "--differential", "2"])
    assert args.cheap == 3 and args.premium == 1 and args.differential == 2
    plain = build_parser().parse_args(["squad"])
    assert plain.cheap is None and plain.premium is None and plain.differential is None


def test_squad_bench_mode_flags_are_parsed_and_mutually_exclusive():
    # ADR-045: --weekly / --bench-boost are bench-aware modes and can't be used together.
    assert build_parser().parse_args(["squad", "--full", "--weekly"]).weekly is True
    assert build_parser().parse_args(["squad", "--full", "--bench-boost"]).bench_boost is True
    with pytest.raises(SystemExit):
        build_parser().parse_args(["squad", "--full", "--weekly", "--bench-boost"])


def test_squad_defaults_to_objective_xp():
    # ADR-041: xp (forward-looking, the metric transfer/analyse use) is the default, so a squad
    # built by default is consistent with transfer; --objective points is the season-total view.
    args = build_parser().parse_args(["squad"])
    assert args.objective == "xp"
    assert build_parser().parse_args(["squad", "--objective", "points"]).objective == "points"


def test_squad_objective_is_parsed():
    args = build_parser().parse_args(["squad", "--objective", "value"])
    assert args.objective == "value"


def test_squad_objective_accepts_xgi():
    args = build_parser().parse_args(["squad", "--objective", "xgi"])
    assert args.objective == "xgi"


def test_squad_include_unavailable_flag_parses():
    assert build_parser().parse_args(["squad"]).include_unavailable is False
    args = build_parser().parse_args(["squad", "--include-unavailable"])
    assert args.include_unavailable is True


def test_squad_save_flag_parses():
    assert build_parser().parse_args(["squad"]).save is None
    args = build_parser().parse_args(["squad", "--save", "my-team"])
    assert args.save == "my-team"


def test_squad_load_flag_parses():
    assert build_parser().parse_args(["squad"]).load is None
    args = build_parser().parse_args(["squad", "--load", "my-team"])
    assert args.load == "my-team"


def test_xg_command_parses_pos_and_limit():
    args = build_parser().parse_args(["xg", "--pos", "FWD", "--limit", "5"])
    assert args.command == "xg"
    assert args.pos == "FWD"
    assert args.limit == 5


def test_overperf_command_parses_options():
    args = build_parser().parse_args(
        ["overperf", "--pos", "MID", "--limit", "5", "--min-minutes", "1200"]
    )
    assert args.command == "overperf"
    assert args.pos == "MID"
    assert args.limit == 5
    assert args.min_minutes == 1200


def test_overperf_min_minutes_defaults_to_900():
    args = build_parser().parse_args(["overperf"])
    assert args.min_minutes == 900
    assert args.limit == 10


def test_defcon_command_parses_options():
    args = build_parser().parse_args(
        ["defcon", "--pos", "DEF", "--limit", "15", "--min-minutes", "600"]
    )
    assert args.command == "defcon"
    assert args.pos == "DEF"
    assert args.limit == 15
    assert args.min_minutes == 600


def test_defcon_defaults():
    args = build_parser().parse_args(["defcon"])
    assert args.min_minutes == 900
    assert args.limit == 20


def test_cleansheet_command_parses_options():
    args = build_parser().parse_args(
        ["cleansheet", "--pos", "GK", "--limit", "5", "--min-minutes", "1200"]
    )
    assert args.command == "cleansheet"
    assert args.pos == "GK"
    assert args.limit == 5
    assert args.min_minutes == 1200


def test_cleansheet_defaults():
    args = build_parser().parse_args(["cleansheet"])
    assert args.min_minutes == 900
    assert args.limit == 20


def test_xp_options_are_parsed():
    args = build_parser().parse_args(
        ["xp", "--type", "custom", "--pos", "MID", "--limit", "5", "--next", "6"]
    )
    assert args.type == "custom"
    assert args.pos == "MID"
    assert args.limit == 5
    assert args.next == 6


def test_captain_command_defaults():
    args = build_parser().parse_args(["captain"])
    assert args.command == "captain"
    assert args.limit == 5          # top-5 candidates by default
    assert args.type == "fpl"
    assert args.squad is None       # global unless --squad is given
    assert args.handler is cmd_captain


def test_captain_squad_and_limit_are_parsed():
    args = build_parser().parse_args(["captain", "--squad", "my-team", "--limit", "3"])
    assert args.squad == "my-team"
    assert args.limit == 3


def test_transfer_command_defaults():
    args = build_parser().parse_args(["transfer", "--squad", "TS"])
    assert args.command == "transfer"
    assert args.squad == "TS"
    assert args.bank == 0.0        # self-funding by default
    assert args.next == 5          # multi-week horizon
    assert args.limit == 5
    assert args.handler is cmd_transfer


def test_transfer_requires_a_squad():
    with pytest.raises(SystemExit):        # argparse errors without the required --squad
        build_parser().parse_args(["transfer"])


def test_transfer_bank_and_next_are_parsed():
    args = build_parser().parse_args(["transfer", "--squad", "TS", "--bank", "2.5", "--next", "3"])
    assert args.bank == 2.5 and args.next == 3


def test_analyse_command_defaults():
    args = build_parser().parse_args(["analyse", "--squad", "TS"])
    assert args.command == "analyse"
    assert args.squad == "TS"
    assert args.next == 5           # multi-week horizon
    assert args.type == "fpl"
    assert args.handler is cmd_analyse


def test_analyse_requires_a_squad():
    with pytest.raises(SystemExit):        # --squad is required
        build_parser().parse_args(["analyse"])


def test_analyse_sort_option_parses():
    assert build_parser().parse_args(["analyse", "--squad", "TS"]).sort == "position"
    assert build_parser().parse_args(["analyse", "--squad", "TS", "--sort", "xp"]).sort == "xp"


def test_xp_by_gameweek_flag_parses():
    assert build_parser().parse_args(["xp"]).by_gameweek is False
    assert build_parser().parse_args(["xp", "--by-gameweek"]).by_gameweek is True


def test_no_command_leaves_no_handler():
    # main() prints help in this case; here we just confirm the parsed shape.
    args = build_parser().parse_args([])
    assert getattr(args, "handler", None) is None


@pytest.mark.parametrize("command", ["captain", "transfer", "analyse"])
def test_no_xmins_flag_defaults_off_and_parses(command):
    # xMins v0 (ADR-038): weighting is default-on; --no-xmins opts out.
    base = [command] + ([] if command == "captain" else ["--squad", "TS"])
    assert build_parser().parse_args(base).no_xmins is False
    assert build_parser().parse_args(base + ["--no-xmins"]).no_xmins is True
