"""Analytics layer — metrics the project derives from stored data.

Unlike the layers below it, analytics *creates* numbers rather than moving them.
It reads player data (via the caller, from storage), computes, and hands results
up to the display. It never touches the API or the screen.
"""

from src.analytics.fdr import elo_difficulty_bands, team_fdr, team_schedule
from src.analytics.optimizer import (
    DEFAULT_BUDGET,
    FULL_BUDGET,
    SQUAD_15,
    XI_FLEX,
    objective_scores,
    resolve_players,
    select_squad,
)
from src.analytics.defcon import defcon_reliability
from src.analytics.overperf import over_under
from src.analytics.value import points_per_million, rank_players
from src.analytics.xp import player_xp

__all__ = [
    "DEFAULT_BUDGET",
    "FULL_BUDGET",
    "SQUAD_15",
    "XI_FLEX",
    "defcon_reliability",
    "elo_difficulty_bands",
    "objective_scores",
    "over_under",
    "player_xp",
    "points_per_million",
    "rank_players",
    "resolve_players",
    "select_squad",
    "team_fdr",
    "team_schedule",
]
