"""Analytics layer — metrics the project derives from stored data.

Unlike the layers below it, analytics *creates* numbers rather than moving them.
It reads player data (via the caller, from storage), computes, and hands results
up to the display. It never touches the API or the screen.
"""

from src.analytics.analyse import analyse_squad
from src.analytics.captain import captain_picks
from src.analytics.chips import CHIP_NAMES, chip_advisor
from src.analytics.cleansheet import defensive_solidity
from src.analytics.crowd import (
    AVAILABILITY_LEGEND,
    CROWD_LEGEND,
    DIFFERENTIAL_OWN,
    SET_PIECE_LEGEND,
    TREND_BYS,
    availability_flag,
    crowd_flags,
    net_transfers,
    set_piece_flags,
    trending,
)
from src.analytics.deadline import next_deadline
from src.analytics.defcon import defcon_reliability
from src.analytics.fdr import elo_difficulty_bands, fixture_ticker, team_fdr, team_schedule
from src.analytics.form import blend_form, form_rate
from src.analytics.gameweek import gameweek_plan
from src.analytics.minutes import (
    availability_weight,
    chance_factor,
    expected_minutes,
    minutes_share,
    minutes_weight_from_history,
)
from src.analytics.optimizer import (
    DEFAULT_BUDGET,
    FULL_BUDGET,
    SQUAD_15,
    WEEKLY_BENCH_WEIGHT,
    XI_FLEX,
    archetype_bands,
    available_players,
    bench_order,
    best_legal_xi,
    best_xi_points,
    is_unavailable,
    legal_xi_issues,
    objective_scores,
    resolve_players,
    select_squad,
    squad_15_issues,
)
from src.analytics.overperf import over_under
from src.analytics.transfer import suggest_transfer_plan, suggest_transfers
from src.analytics.value import points_per_million, rank_players
from src.analytics.xp import baseline_rate, decision_xp, fallback_rate, player_xp

__all__ = [
    "DEFAULT_BUDGET",
    "FULL_BUDGET",
    "SQUAD_15",
    "WEEKLY_BENCH_WEIGHT",
    "XI_FLEX",
    "analyse_squad",
    "archetype_bands",
    "availability_weight",
    "available_players",
    "bench_order",
    "best_legal_xi",
    "best_xi_points",
    "captain_picks",
    "chip_advisor",
    "CHIP_NAMES",
    "next_deadline",
    "gameweek_plan",
    "chance_factor",
    "AVAILABILITY_LEGEND",
    "SET_PIECE_LEGEND",
    "CROWD_LEGEND",
    "availability_flag",
    "crowd_flags",
    "set_piece_flags",
    "net_transfers",
    "trending",
    "TREND_BYS",
    "DIFFERENTIAL_OWN",
    "decision_xp",
    "blend_form",
    "form_rate",
    "expected_minutes",
    "fallback_rate",
    "minutes_share",
    "minutes_weight_from_history",
    "is_unavailable",
    "defcon_reliability",
    "defensive_solidity",
    "elo_difficulty_bands",
    "legal_xi_issues",
    "squad_15_issues",
    "objective_scores",
    "over_under",
    "baseline_rate",
    "player_xp",
    "points_per_million",
    "rank_players",
    "resolve_players",
    "select_squad",
    "suggest_transfer_plan",
    "suggest_transfers",
    "team_fdr",
    "team_schedule",
    "fixture_ticker",
]
