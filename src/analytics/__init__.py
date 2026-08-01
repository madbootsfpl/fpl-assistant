"""Analytics layer — metrics the project derives from stored data.

Unlike the layers below it, analytics *creates* numbers rather than moving them.
It reads player data (via the caller, from storage), computes, and hands results
up to the display. It never touches the API or the screen.
"""

from src.analytics.value import points_per_million, rank_players

__all__ = ["points_per_million", "rank_players"]
