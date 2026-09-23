"""The contract layer — what a client asks for, and what it gets back.

⭐⭐ **One contract, two transports** (ADR-219). The mobile audit §4.2 proposed that Streamlit migrate onto
the HTTP API so the contract would have a real consumer before Flutter exists — *"a contract with one
consumer is a guess."* The principle is right and the mechanism would have made the web app slower, trading
in-process calls for a round trip on the app a whole day was spent speeding up.

So the contract lives here as **plain functions over plain dicts**. FastAPI is a thin HTTP wrapper over
these; Streamlit imports them directly. Both consumers exercise the same shapes, and only one pays for a
network. What that costs is a test: the HTTP body must equal the in-process answer serialised.

⚠️ **Nothing here computes football.** Every function assembles inputs, calls the same engine the CLI calls,
and shapes the answer — ADR-181's rule, on a new surface. A number that appears here and nowhere else is a
second implementation.
"""

from src.service.answers import (
    analysis,
    build,
    captain,
    chips,
    compare,
    feedback,
    gameweek,
    my_team,
    player,
    player_dna,
    players,
    replacements,
    route,
    signals,
    team_dna,
    ticker,
    transfers,
    trending,
)
from src.service.requests import (
    DEFAULT_HORIZON,
    BuildRequest,
    CaptainRequest,
    ChipsRequest,
    CompareRequest,
    FeedbackRequest,
    GameweekRequest,
    MyTeamRequest,
    PlayerDnaRequest,
    PlayerRequest,
    PlayersRequest,
    ReplacementsRequest,
    RouteRequest,
    SignalsRequest,
    SquadRequest,
    TeamDnaRequest,
    TickerRequest,
    TransfersRequest,
    TrendingRequest,
)

__all__ = [
    "DEFAULT_HORIZON",
    "BuildRequest",
    "CaptainRequest",
    "ChipsRequest",
    "CompareRequest",
    "FeedbackRequest",
    "GameweekRequest",
    "MyTeamRequest",
    "PlayerRequest",
    "PlayersRequest",
    "ReplacementsRequest",
    "RouteRequest",
    "SignalsRequest",
    "PlayerDnaRequest",
    "TeamDnaRequest",
    "TickerRequest",
    "ticker",
    "TrendingRequest",
    "trending",
    "SquadRequest",
    "TransfersRequest",
    "analysis",
    "build",
    "captain",
    "chips",
    "compare",
    "feedback",
    "gameweek",
    "my_team",
    "player",
    "players",
    "replacements",
    "route",
    "signals",
    "player_dna",
    "team_dna",
    "transfers",
]
