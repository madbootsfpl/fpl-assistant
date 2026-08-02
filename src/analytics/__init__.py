"""Analytics layer — metrics the project derives from stored data.

Unlike the layers below it, analytics *creates* numbers rather than moving them.
It reads player data (via the caller, from storage), computes, and hands results
up to the display. It never touches the API or the screen.
"""

from src.analytics.fdr import team_fdr, team_schedule
from src.analytics.optimizer import select_squad
from src.analytics.value import points_per_million, rank_players
from src.analytics.xp import player_xp

__all__ = [
    "player_xp",
    "points_per_million",
    "rank_players",
    "select_squad",
    "team_fdr",
    "team_schedule",
]
