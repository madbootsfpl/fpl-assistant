"""The answers, grouped by what they are about (ADR-324).

This was one 2,368-line module. ⭐ **It split along a seam it already had**: one function per endpoint, and
every private helper used by exactly one family of them. Nothing here was rewritten — the functions moved
verbatim, which is why the suite is the proof.

    squad     analysis · transfers · captain · gameweek · route · build · my_team · replacements · chips
    league    leagues · league · gameweek_result · head_to_head
    player    player · players · compare · player_dna · team_dna
    market    trending · ticker · signals
    language  ask_question · chatter
    meta      feedback
    common    the three helpers more than one family needs

⚠️ **`src/service/__init__.py` is still the contract layer** (ADR-219) and is what `app.py` and Streamlit
import. This file exists so that `from src.service.answers import x` keeps meaning what it meant — every
name the single module exposed is re-exported below, so the split is invisible to callers.

⭐ A barrel here costs a few milliseconds and buys a stable surface. ⚠️ *Not the mistake ADR-323 found:*
that was a barrel putting a 36 MB external solver on every import path. These are pure-Python siblings in
the same package, and anything importing one of them was going to load the others anyway.
"""

# ⚠️ **Re-exported because the single module re-exported them incidentally, and tests import them from
# here.** `RUN`/`SWIPE` come from `src.service.inputs` and `fetch_manager_team` from `src.manager`; nothing
# in this package defines them. ⭐ *An incidental re-export that something depends on is part of the
# surface whether it was meant to be or not* — so it is written down rather than discovered by a failure.
from src.manager import fetch_manager_team
from src.service.answers.common import _chip_status, _entry_history, plain
from src.service.answers.language import (
    _CHATTER,
    CHATTER_TTL_SECONDS,
    _next_gameweek,
    ask_question,
    chatter,
)
from src.service.answers.market import (
    GLOBAL_OWNERSHIP_PERCENTILE,
    _market_subjects,
    _worth_a_look,
    _worth_noticing,
    signals,
    ticker,
    trending,
)
from src.service.answers.meta import feedback
from src.service.answers.mini_leagues import (
    _award_of,
    _awards,
    _manager_rows,
    _picks_for,
    gameweek_result,
    head_to_head,
    league,
    leagues,
)
from src.service.answers.profiles import (
    DNA_RUN,
    RECENT,
    _badges,
    _recent_rows,
    compare,
    player,
    player_dna,
    players,
    team_dna,
)
from src.service.answers.squad import (
    _age_minutes,
    _data_freshness,
    _deadline_parts,
    _explained,
    _legal_swaps,
    _suggested_lineup,
    analysis,
    build,
    captain,
    chips,
    gameweek,
    my_team,
    replacements,
    route,
    transfers,
)
from src.service.inputs import RUN, SWIPE, WIDE

# ⭐ The request classes, re-exported for the same reason — the single module imported all of them, so
# `answers.TickerRequest` worked and `tests/test_service_endpoints.py` uses it. These at least *belong* to
# the contract: `src/service/__init__.py` already publishes them beside the handlers (ADR-219).
from src.service.requests import (
    DEFAULT_HORIZON,
    MAX_HORIZON,
    AskRequest,
    BuildRequest,
    CaptainRequest,
    ChatterRequest,
    ChipsRequest,
    CompareRequest,
    FeedbackRequest,
    GameweekRequest,
    GameweekResultRequest,
    HeadToHeadRequest,
    LeagueRequest,
    LeaguesRequest,
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
    # the contract — one name per endpoint, the list `src/service/__init__.py` re-exports
    "analysis", "transfers", "captain", "gameweek", "route", "build", "my_team", "replacements",
    "chips", "leagues", "league", "gameweek_result", "head_to_head", "player", "players",
    "compare", "player_dna", "team_dna", "trending", "ticker", "signals", "ask_question",
    "chatter", "feedback",
    # constants callers and tests read
    "CHATTER_TTL_SECONDS", "_CHATTER", "DNA_RUN", "GLOBAL_OWNERSHIP_PERCENTILE", "RECENT",
    "RUN", "SWIPE", "WIDE", "fetch_manager_team", "plain",
    # the request classes — the contract's input half (ADR-219), re-exported as the single module did
    "DEFAULT_HORIZON", "MAX_HORIZON", "AskRequest", "BuildRequest", "CaptainRequest",
    "ChatterRequest", "ChipsRequest", "CompareRequest", "FeedbackRequest", "GameweekRequest",
    "GameweekResultRequest", "HeadToHeadRequest", "LeagueRequest", "LeaguesRequest",
    "MyTeamRequest", "PlayerDnaRequest", "PlayerRequest", "PlayersRequest", "ReplacementsRequest",
    "RouteRequest", "SignalsRequest", "SquadRequest", "TeamDnaRequest", "TickerRequest",
    "TransfersRequest", "TrendingRequest",
    # ⚠️ private helpers the tests reach for directly — a known wart, recorded in ADR-324 rather than
    # quietly preserved: a name with a leading underscore that another file imports is not private.
    "_age_minutes", "_award_of", "_awards", "_badges", "_chip_status", "_data_freshness",
    "_deadline_parts", "_entry_history", "_explained", "_legal_swaps", "_manager_rows",
    "_market_subjects", "_next_gameweek", "_picks_for", "_recent_rows", "_suggested_lineup",
    "_worth_a_look", "_worth_noticing",
]
