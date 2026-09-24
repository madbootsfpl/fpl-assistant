"""`/api/v1/squad/*` — the squad-shaped questions, over HTTP (mobile audit §4.2, ADR-219/220).

⚠️ **Separate from `src/web`, deliberately.** That is ADR-050's read-only HTML edge, which renders text into
a `<pre>` block for a browser. This returns JSON for a client that draws its own screens. Sharing an app
object would make one of them the other's constraint.

⭐ **No auth, and that is a fact about these endpoints rather than an omission.** Every one takes *player ids
in, analysis out* — there is no user row to protect. Owner-scoped data (your saved squad, your preferences)
is Stage C and is not served from here.

⭐⭐ **Every route is four lines and none of them decides anything.** The moment a rule can only be found
here, the in-process consumer and the HTTP consumer have different products — which is the failure this
whole layer exists to prevent.
"""

import importlib.metadata
import pathlib
from collections.abc import Callable

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src import service
from src.service.http.limits import RateLimiter, rate_limit_middleware
from src.service.http.usage import status as usage_status
from src.service.http.usage import usage_middleware
from src.service.requests import (
    DEFAULT_HORIZON,
    FPL_BUDGET,
    MAX_FEEDBACK,
    MAX_HORIZON,
    MAX_PLAN,
)

app = FastAPI(
    title="MADBOOTS service",
    version="1",
    # The interactive docs are the contract a client author reads first, so they stay on.
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)

# ⭐⭐ **Open to every origin, and that is the same fact as "no auth" above rather than a second decision.**
# These endpoints take *player ids in, analysis out*. There is no session, no cookie, no user row and nothing
# a hostile page could read that it could not read by calling the API itself — so an origin allow-list would
# protect nothing and would silently break a Flutter web build on whatever port it happened to pick.
#
# ⚠️ **`allow_credentials` stays False, and must.** The spec forbids pairing it with `*`, and Starlette
# enforces that by quietly refusing to echo the origin — ⭐ *the failure would be a working app that stops
# working the day someone adds a cookie*, which is exactly when nobody is looking at CORS.
#
# 🔴 **Revisit the moment an endpoint becomes owner-scoped** (Stage C: a saved squad, preferences). The
# reason this is safe is *what these endpoints serve*, not a judgement that CORS does not matter — and the
# reason expires the day the answer depends on who is asking.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ⭐⭐ **A public, unauthenticated API needs a cost control before it is public** (ADR-256). Two endpoints
# have a real price: `feedback` reaches a human, and `build` runs an LP solver whose CPU a stranger would
# be choosing. ⚠️ *It is a cost control, not a security boundary* — see `limits.caller`.
# ⭐ On `app.state`, where FastAPI expects app-scoped objects — and reachable from a test without import
# gymnastics. ⚠️ A module-level `_limiter` looked simpler and was not: `src/service/http/__init__.py` does
# `from src.service.http.app import app`, which binds the FastAPI **object** over its own submodule, so
# even the full dotted path hands you the app rather than the module.
app.state.limiter = RateLimiter()
app.middleware("http")(rate_limit_middleware(app.state.limiter))

# ⭐ Registered AFTER the limiter, so it runs OUTSIDE it — a rejected request is load too, and ⚠️ *a
# capacity measure that cannot see the traffic it refused is the one measure you need when refusing.*
app.middleware("http")(usage_middleware())


# ⭐ Read from the package metadata rather than typed here. A version string written in two places is a
# version string that disagrees with itself — ADR-212's lesson at its smallest scale.
def _version() -> str:
    """The package version, from metadata or — ⚠️ **in a container, where it is not installed** — from
    `pyproject.toml`.

    ⭐ Found by running the image rather than reading it: the hosted API reported `"version": "unknown"`,
    because `requirements-api.txt` deliberately omits `-e .` and `importlib.metadata` then has nothing to
    read. *A deployment that cannot say which build it is cannot be diagnosed*, and the phone's own
    connection check asserts the field is non-empty.
    """
    try:
        return importlib.metadata.version("fpl-assistant")
    except importlib.metadata.PackageNotFoundError:
        try:
            import tomllib

            root = pathlib.Path(__file__).resolve().parents[3]
            return tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
        except Exception:  # pragma: no cover - only if pyproject is absent too
            return "unknown"


_VERSION = _version()


_GAMEWEEK_KEYS = ("⚠️ `by_gameweek` arrives keyed by gameweek as a **string**, because JSON has no integer "
                  "object keys — the same shape PostgREST already serves for the published board. ⭐ Parse "
                  "them to integers before sorting: as text, `\"10\"` sorts before `\"6\"`, so a prefix sum "
                  "over *the next two gameweeks* would quietly answer for the wrong two.")


class SquadBody(BaseModel):
    """A squad, by FPL element id.

    ⭐ Ids, not rows (audit §4.2). A client that uploaded player rows would be defining the engine's input,
    which is how one rule becomes two implementations.
    """

    player_ids: list[int] = Field(..., min_length=1, description="The squad's players, by FPL element id.")
    bench_ids: list[int] = Field(default_factory=list,
                                 description="Optional. Omit and the best legal XI is derived.")
    horizon: int = Field(DEFAULT_HORIZON, ge=1, le=MAX_HORIZON, description="Gameweeks to look ahead.")


class TransfersBody(SquadBody):
    bank: float = Field(0.0, ge=0, description="Money available, in £m.")
    count: int = Field(1, ge=1, le=MAX_PLAN,
                       description="Moves to plan together. Above 1 they share the bank, so the gains add "
                                   "up — a plan, not a menu of alternatives.")
    limit: int = Field(5, ge=1, le=50, description="How many single swaps to rank when count is 1.")


class CaptainBody(SquadBody):
    limit: int = Field(5, ge=1, le=15, description="How many candidates to return.")


class GameweekBody(SquadBody):
    bank: float = Field(0.0, ge=0, description="Money available, in £m.")
    free: int = Field(1, ge=0, le=5,
                      description="Free transfers held. The plan recommends this many moves, so sending the "
                                  "wrong number advises a position the manager is not in.")


class RouteBody(SquadBody):
    target_id: int = Field(..., description="The player you want to field, by FPL element id.")
    bank: float = Field(0.0, ge=0, description="Money available, in £m.")


class CompareBody(BaseModel):
    """⚠️ No squad — a comparison is about two players, and requiring the fifteen would stop the transfer
    screen asking about someone you do not own, which is the only interesting case."""

    a_id: int = Field(..., ge=1)
    b_id: int = Field(..., ge=1)
    horizon: int = Field(DEFAULT_HORIZON, ge=1, le=MAX_HORIZON)


class FeedbackBody(BaseModel):
    """A note from a tester. ⚠️ Free text, so it is capped — and relayed verbatim, never interpreted."""

    message: str = Field(..., min_length=1, max_length=MAX_FEEDBACK)
    contact: str = Field("", max_length=200, description="Optional — how to reply.")
    screen: str = Field("", max_length=60, description="Which screen this is about.")
    version: str = Field("", max_length=40)


class PlayerBody(BaseModel):
    """One player, in full — the card behind a row."""

    player_id: int = Field(..., ge=1)
    horizon: int = Field(DEFAULT_HORIZON, ge=1, le=MAX_HORIZON)


class PlayersBody(BaseModel):
    """⚠️ No squad — this is the market, not your team."""

    horizon: int = Field(DEFAULT_HORIZON, ge=1, le=MAX_HORIZON)
    limit: int = Field(800, ge=1, le=1000,
                       description="⭐ Defaults to everyone. The whole board is ~110 KB and filtering it "
                                   "locally is instant, where a round trip per keystroke is not.")


class LeaguesBody(BaseModel):
    """⭐ A manager id, not a league id — *nobody knows their league id* (ADR-141)."""

    manager_id: int = Field(..., ge=1)


class LeagueBody(BaseModel):
    """One classic league. ⚠️⚠️ `with_captains` costs **one FPL request per manager**; the table costs one
    in total."""

    league_id: int = Field(..., ge=1)
    manager_id: int = Field(0, ge=0)
    gameweek: int | None = Field(None, ge=1)
    with_captains: bool = False
    limit: int = Field(20, ge=1, le=50)


class HeadToHeadBody(BaseModel):
    """You against one rival. ⭐ A table says who is ahead; this says **what would have to happen**."""

    manager_id: int = Field(..., ge=1)
    rival_id: int = Field(..., ge=1)
    horizon: int = Field(1, ge=1, le=MAX_HORIZON)


class TrendingBody(BaseModel):
    """What the crowd is doing. ⚠️ `player_ids` is **optional and does not narrow the boards** — it only
    lets a row come back flagged `owned` (ADR-245's pattern)."""

    by: str = Field("look", pattern="^(look|watch|in|out|owned|form)$",
                    description="⭐ `look` is **worth a look** (ADR-167) — players standing out on two or "
                                "more stat boards at once, each with its evidence. It leads because it is "
                                "the only board here about the *player* rather than about other managers. "
                                "`watch` is **worth noticing** (ADR-170) — three crowd patterns each "
                                "needing two boards at once, grouped. Then `in` most bought · `out` most "
                                "sold · `owned` · `form`.")
    limit: int = Field(15, ge=1, le=50)
    player_ids: list[int] = Field(default_factory=list)


class TickerBody(BaseModel):
    """⚠️ No squad — this is the **league's** fixtures, not yours."""

    next_n: int = Field(6, ge=1, le=10,
                        description="How many gameweeks wide the grid is.")
    source: str = Field("fpl", pattern="^(fpl|custom)$",
                        description="⭐ `fpl` is the official 1-5 difficulty, so it reads the same as the "
                                    "FPL app; `custom` is our own strength-at-venue number (ADR-005).")


class ChipsBody(SquadBody):
    bank: float = Field(0.0, ge=0, description="Money available, in £m — a wildcard is priced against it.")
    manager_id: int | None = Field(
        None, ge=1,
        description="⭐ **Supply it and the answer knows which chips you have already spent.** Without it "
                    "each chip's `available` is `null` — ⚠️ *unknown*, never *true*: recommending a "
                    "wildcard someone played in GW4 is a wrong answer delivered confidently.")


class MyTeamBody(BaseModel):
    """⚠️ **An FPL manager id, not a squad** — the one endpoint that names a person.

    It is public information: anyone can look up any manager's team on FPL's own site once a deadline has
    passed. ⭐ *Nothing owner-scoped is served here* — this reads a public squad and analyses it, which is
    why it needs no auth any more than the others do.
    """

    manager_id: int = Field(..., ge=1, description="The FPL manager (entry) id — the number in your team URL.")
    horizon: int = Field(1, ge=1, le=MAX_HORIZON,
                         description="Gameweeks to look ahead. Defaults to **1**: a landing pitch is about "
                                     "this gameweek, where every other endpoint looks further.")
    draft_player_ids: list[int] = Field(
        default_factory=list,
        description="⭐ **A draft: price THIS squad instead of the one FPL holds.** Fifteen ids. The "
                    "manager's name, bank, deadline and armbands still come from FPL — only the players "
                    "change. Omit for the real team.")
    draft_bench_ids: list[int] = Field(default_factory=list,
                                       description="The draft's bench. Must be drawn from `draft_player_ids`.")
    free_transfers: int = Field(1, ge=0, le=5,
                                description="⚠️ **You must supply this — FPL does not publish it.** The "
                                            "entry payload carries bank and value but free transfers sit "
                                            "behind a login. It is echoed back so a header can show what "
                                            "the answer assumed.")


class ReplacementsBody(SquadBody):
    out_id: int = Field(..., description="The owned player you want to replace.")
    bank: float = Field(0.0, ge=0, description="Money available, in £m.")
    limit: int = Field(40, ge=1, le=200, description="How many candidates to return.")


class BuildBody(BaseModel):
    """⚠️ No `player_ids` — this is the one question that starts from nothing."""

    budget: float = Field(FPL_BUDGET, gt=0, description="Total spend, in £m.")
    horizon: int = Field(DEFAULT_HORIZON, ge=1, le=MAX_HORIZON, description="Gameweeks to optimise over.")
    include_ids: list[int] = Field(default_factory=list, description="Players to force in.")
    exclude_ids: list[int] = Field(default_factory=list, description="Players to rule out.")
    bench_weight: float | None = Field(
        None, ge=0, le=1,
        description="⭐ Makes the build **bench-aware** (ADR-045): the solver also picks the XI and "
                    "values the bench at this weight. `0.1` is a strong XI with a cheap-but-playing "
                    "bench. ⚠️⚠️ **Omit it and all fifteen are treated as if they play** — a squad that "
                    "spends real money on players who never score.")


def _answer(fn: Callable, request) -> dict:
    """Call one service function and translate its refusals.

    ⭐ A bad squad is the caller's mistake, not a server fault — 400, with the reason. Returning 500 would
    tell a client author to retry something that will never work.
    """
    try:
        return fn(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/health")
def health() -> dict:
    """Is the service up, **and is it us**? Deliberately does not touch the database — ⭐ a health check
    that fails when the database is slow reports on the database, not the service, and would take the app
    out of rotation for a dependency it can survive.

    ⭐⭐ **`service` and `version` are here for the phone, not for monitoring** (ADR-239). Once the base URL
    is something a person types, a typo can land on a router's admin page, another dev server on the same
    port, or a captive portal — all of which answer **200** and none of which are this API. A bare
    `{"ok": true}` cannot tell those apart, so the app would report a healthy connection to the wrong
    machine. ⚠️ *"Something answered" is not "the right thing answered",* and only the payload can say
    which.
    """
    # ⚠️⚠️ **`ok` is not a constant, and it used to be.** Running the image with no `FPL_DATABASE_URL`
    # produced a container that answered `/health` with `200 {"ok": true}` and **500-ed every real
    # request** — a platform polling health would have kept it in rotation, and the failure would have
    # reached a tester as "the app is broken".
    #
    # ⭐ So health answers the question it is being asked: *can this instance serve?* — which is a
    # different question from *is the process alive?*, and only the first one is worth reporting.
    #
    # ⚠️ Still does not touch the database's **contents**: a check that fails when a query is slow reports
    # on the database, not the service.
    reachable, why = _can_serve()
    return {"ok": reachable, "service": "madboots", "version": _VERSION,
            # ⭐ `off` · `never` · `ok` · `failing (…)` — ⚠️ *fail-silent usage recording hid a total
            # failure once* (ADR-281), and an empty panel read identically to a quiet week. This is the
            # one place to tell *not configured* from *configured and broken*. No url, no key, no data.
            "usage": usage_status(),
            **({} if reachable else {"reason": why})}


def _can_serve() -> tuple[bool, str]:
    """Whether this instance has a database to read at all.

    ⭐ Cheap and cached: it opens a store once and remembers. ⚠️ *A per-request connection test would make
    the health check the most expensive endpoint*, which is the opposite of the point.
    """
    global _SERVE_CHECK
    if _SERVE_CHECK is None:
        # ⚠️⚠️ **Named before it is diagnosed.** Without this the container reported
        # *"PermissionError: [Errno 13] Permission denied: 'data'"* — true, and useless: the actual fault
        # is a missing secret, and the permission error is three steps downstream of it. ⭐ *A health
        # reason that describes a symptom sends whoever reads it to the wrong file.*
        from src import config

        if not config.DATABASE_URL and not pathlib.Path(config.DB_PATH).exists():
            _SERVE_CHECK = (False, "FPL_DATABASE_URL is not set and there is no local database — "
                                   "a hosted instance reads Postgres (ADR-211)")
            return _SERVE_CHECK
        try:
            from src.storage import Storage

            store = Storage()
            try:
                store.get_teams()
            finally:
                store.close()
            _SERVE_CHECK = (True, "")
        except Exception as exc:
            # ⚠️ The reason travels: "no database" and "wrong credentials" are different deploys to fix.
            _SERVE_CHECK = (False, f"no readable database — {type(exc).__name__}: {exc}"[:200])
    return _SERVE_CHECK


#: ⭐ `None` until first asked. Reset by tests; never reset in production, where a database that vanishes
#: mid-life is a restart, not a recovery.
_SERVE_CHECK: tuple[bool, str] | None = None


@app.post("/api/v1/squad/analysis", description=_GAMEWEEK_KEYS)
def squad_analysis(body: SquadBody) -> dict:
    """A squad's health over the horizon: projected XI xP, the bench, weak links, club concentration."""
    return _answer(service.analysis, service.SquadRequest(**body.model_dump()))


@app.post("/api/v1/squad/transfers")
def squad_transfers(body: TransfersBody) -> dict:
    """The best swaps for this squad — a coordinated plan when `count` > 1, a ranked menu when it is 1."""
    return _answer(service.transfers, service.TransfersRequest(**body.model_dump()))


@app.post("/api/v1/squad/captain")
def squad_captain(body: CaptainBody) -> dict:
    """Who to captain **this gameweek**. ⚠️ Always the next gameweek, whatever `horizon` is sent."""
    return _answer(service.captain, service.CaptainRequest(**body.model_dump()))


@app.post("/api/v1/squad/gameweek-plan")
def squad_gameweek_plan(body: GameweekBody) -> dict:
    """The whole week in one answer: captain · lineup · transfers · timing · flags."""
    return _answer(service.gameweek, service.GameweekRequest(**body.model_dump()))


@app.post("/api/v1/squad/route")
def squad_route(body: RouteBody) -> dict:
    """*"What would it take to field X?"* — every legal one-transfer route to owning the target.

    ⭐ A blocked route is **information**: *"short by £0.6m"* answers the question, where an empty list looks
    like the question was not understood.
    """
    return _answer(service.route, service.RouteRequest(**body.model_dump()))


@app.post("/api/v1/compare")
def compare_players(body: CompareBody) -> dict:
    """**Boot Battle** — two players side by side: the stat grid with a winner per row, each one's last five
    gameweeks, and both projected runs.

    ⚠️ **Same position only.** The stats are ordered by what matters for a position, so comparing a keeper
    with a midfielder gives rows that are individually true and jointly meaningless.
    """
    return _answer(service.compare, service.CompareRequest(**body.model_dump()))


@app.post("/api/v1/feedback")
def send_feedback(body: FeedbackBody) -> dict:
    """Relay a tester's note to the owner's sink.

    ⭐ **The server holds the webhook so the client never has to** — a secret in a mobile binary is a
    secret every tester has.

    ⚠️⚠️ **Check `sent`.** It reports the relay's *own* verdict, and `false` with a `reason` is a real
    outcome — an unconfigured sink, an unreachable one, or a relay that refused. A blind *"thanks, sent!"*
    is the bug this exists to avoid.
    """
    return _answer(service.feedback, service.FeedbackRequest(**body.model_dump()))


@app.post("/api/v1/player")
def one_player(body: PlayerBody) -> dict:
    """One player in full: season stats **ordered for his position**, his last five gameweeks with minutes,
    and the projected run with fixture difficulty.

    ⭐ Fetched when a row is expanded, not with the list — the market is 481 players, and carrying every
    stat for all of them so that one can be opened is the opposite of the trade the list was built on.
    """
    return _answer(service.player, service.PlayerRequest(**body.model_dump()))


@app.post("/api/v1/players")
def all_players(body: PlayersBody) -> dict:
    """Every available player, ranked by xP over the horizon.

    ⭐ **Unavailable players are excluded, not flagged** — a browse list is for finding someone to buy, and
    a player who cannot play is not a candidate. ⚠️ *Doubtful* players stay: a doubt is a probability, not
    a verdict.
    """
    return _answer(service.players, service.PlayersRequest(**body.model_dump()))


@app.post("/api/v1/leagues")
def manager_leagues(body: LeaguesBody) -> dict:
    """The classic leagues a manager is in.

    ⭐⭐ **Looked up from the manager id**, because *nobody knows their league id* — it lives in a URL you
    have to go and find. ⚠️ **Private leagues lead**: FPL mixes the league you joined with friends in among
    automatic ones (your club, your region, Overall), and sorting by size would bury the only leagues
    anyone means.
    """
    return _answer(service.leagues, service.LeaguesRequest(**body.model_dump()))


@app.post("/api/v1/league")
def one_league(body: LeagueBody) -> dict:
    """A classic league's table, and optionally what its managers captained.

    ⚠️⚠️ **`with_captains` is opt-in and capped** — the table is one request, the split is `limit` more.
    ⭐ *A screen that quietly spends fifty requests to draw a second panel will be blamed for being slow.*

    ⚠️ **`captains_from` says how many squads it actually read.** A manager whose fetch fails is absent
    rather than fatal, and a partial read must never present itself as the whole league.
    """
    return _answer(service.league, service.LeagueRequest(**body.model_dump()))


@app.post("/api/v1/h2h")
def head_to_head(body: HeadToHeadBody) -> dict:
    """You against one rival, decomposed (ADR-161).

    ⭐⭐ **The shared players are reported and then set aside** — they are usually most of both totals and
    the part you can do nothing about. ⚠️ *Printing the shared total is what makes the small gap believable
    rather than looking like a rounding error on two big numbers.*

    ⚠️ It reads the **last finished** gameweek: a rival's picks are public only after a deadline.
    """
    return _answer(service.head_to_head, service.HeadToHeadRequest(**body.model_dump()))


@app.post("/api/v1/trending")
def what_the_crowd_is_doing(body: TrendingBody) -> dict:
    """The crowd's leaderboards — most bought, most sold, most owned, in form.

    ⚠️⚠️ **Display-only, and never xP.** ⭐ *"Lots of people did this" is a fact about other managers, not
    about the player* — the reason a template forms, and not on its own a reason to join one. ADR-150
    ranks this **last** among signal tiers, and the answer carries its own `caveat` so the framing cannot
    drift from the numbers.
    """
    return _answer(service.trending, service.TrendingRequest(
        by=body.by, limit=body.limit, player_ids=tuple(body.player_ids)))


@app.post("/api/v1/ticker")
def fixture_ticker(body: TickerBody) -> dict:
    """The fixture-difficulty grid — every club, their next few gameweeks, **easiest run first**.

    ⭐ **A blank gameweek is `null`, not a missing key**: *"they do not play"* is the most valuable thing a
    ticker says, and an absent cell reads as absent data.

    ⚠️ **A double carries both opponents** and is shaded by the **harder** of them — a double is only as
    easy as its worse fixture.

    ⚠️ `cells` is keyed by gameweek **as a string** (JSON has no integer keys); read the order from
    `gameweeks`, not from the map.
    """
    return _answer(service.ticker, service.TickerRequest(**body.model_dump()))


class SignalsBody(BaseModel):
    """A squad and a scope — ⚠️ **the one squad-shaped body where the squad is optional** (ADR-245).

    ⭐ A global sweep has no squad to give. Sending one anyway is still worth it: every signal comes back
    with `owned`, so a market list can say *"you have him"* without the client holding a second copy of the
    fifteen and matching ids itself.
    """

    player_ids: list[int] = Field(default_factory=list,
                                  description="Your squad. Required for scope=squad; optional for global, "
                                              "where it only marks which signals are about players you own.")
    horizon: int = Field(DEFAULT_HORIZON, ge=1, le=MAX_HORIZON, description="Gameweeks to look ahead.")
    scope: str = Field("squad", pattern="^(squad|global)$",
                       description="squad = your fifteen · global = the market, above a live ownership cut.")


class TeamDnaBody(BaseModel):
    """⭐ Your squad is optional and filters nothing — it only marks the clubs you hold players from."""

    player_ids: list[int] = Field(default_factory=list,
                                  description="Optional. Marks which clubs your own players come from.")
    horizon: int = Field(DEFAULT_HORIZON, ge=1, le=MAX_HORIZON, description="Gameweeks to look ahead.")


class PlayerDnaBody(BaseModel):
    player_id: int = Field(..., description="The player, by FPL element id.")
    horizon: int = Field(DEFAULT_HORIZON, ge=1, le=MAX_HORIZON, description="Gameweeks to look ahead.")


@app.post("/api/v1/player-dna")
def player_dna(body: PlayerDnaBody) -> dict:
    """One player's eight-axis fingerprint, ranked **within his position**.

    ⭐⭐ Within position, not across the league: a defender's attacking threat and a forward's are not the
    same question, and one scale across incomparable roles flatters and punishes by position.

    ⭐ `pool_size` and `low_minutes` come with it. *A percentile is only as meaningful as the field it was
    measured in* — "84th of 31 midfielders" is a fact; "84th" alone invites over-reading.
    """
    return _answer(service.player_dna, service.PlayerDnaRequest(**body.model_dump()))


@app.post("/api/v1/team-dna")
def team_dna(body: TeamDnaBody) -> dict:
    """Every club's eight-axis fingerprint, ranked across the league, best first.

    ⭐⭐ **Team DNA, not player DNA.** A player's fingerprint answers *what kind of player is he?*, which
    the app answers twice already — the expanding card and Boot Battle. A club's answers *is this attack
    actually any good?*, which is what decides between two players from different sides.

    ⚠️ Not under `/squad/` — this is the league, not your team.

    ⭐ Every axis is a **percentile**, so `74` means the same thing on Attacking Threat as on Squad Depth.
    """
    return _answer(service.team_dna, service.TeamDnaRequest(**body.model_dump()))


@app.post("/api/v1/squad/signals")
def squad_signals(body: SignalsBody) -> dict:
    """What a manager should know — about his own fifteen, or about the market.

    ⭐ Each signal carries a `kind` — `official` · `departure` · `exodus` · `headline` · `trending` —
    because they are not equally reliable, and an unexplained sell-off is not the same claim as an injury
    FPL confirmed. ⚠️ *Rendering them as one undifferentiated list is the page ADR-150 was written to
    replace.*

    ⭐ **`scope=global` folds in what Trending used to be a separate screen for.** It answers above a
    **live ownership percentile**, not a typed threshold, and reports the cut it used as
    `ownership_floor` — ⚠️ *a market view that silently drops four fifths of the board is a view that lies
    by omission.*

    ⭐ Every signal has a stable `key`, so a client can remember which it has already shown.
    """
    return _answer(service.signals, service.SignalsRequest(**body.model_dump()))


@app.post("/api/v1/squad/chips")
def squad_chips(body: ChipsBody) -> dict:
    """When to play each chip, and what a wildcard is **worth**.

    ⚠️⚠️ **`horizon` is accepted and ignored.** A chip is a season decision with a fixed expiry, so the
    window is the **chip's deadline** — the answer to *"is this week better than the weeks I have left?"*
    cannot be computed over a window chosen for a different screen (ADR-166). The window actually used
    comes back as `window`.
    """
    return _answer(service.chips, service.ChipsRequest(**body.model_dump()))


@app.post("/api/v1/squad/my-team")
def squad_my_team(body: MyTeamBody) -> dict:
    """Everything the **My Team** pitch draws, in one call: squad, armbands, deadline, analysis, kits,
    fixtures and bench order.

    ⭐ **A composition of endpoints that already exist**, offered as one because the alternative is five
    round trips on a phone before anything renders.

    ⚠️ A refusal here is often not the caller's fault — a team is not public until the first deadline, and
    FPL's API is sometimes simply unreachable. The message says which.
    """
    return _answer(service.my_team, service.MyTeamRequest(**body.model_dump()))


@app.post("/api/v1/squad/replacements")
def squad_replacements(body: ReplacementsBody) -> dict:
    """Every legal replacement for one owned player — **affordable or not**.

    ⚠️ Over-budget candidates come back with `affordable: false` and `over_by`, rather than being filtered
    out. ⭐ *A candidate silently removed looks like a candidate that does not exist*, so a manager would
    conclude the player is ineligible when he is merely dear — and FPL prices drift, so a move you cannot
    quite afford today is a plan, not an error.
    """
    return _answer(service.replacements, service.ReplacementsRequest(**body.model_dump()))


@app.post("/api/v1/squad/build")
def squad_build(body: BuildBody) -> dict:
    """The best legal fifteen within a budget — the wildcard question.

    ⚠️ Check `status`: the solver's own word. `Infeasible` means *nothing fits these constraints*, which is
    an answer, not a failure.
    """
    return _answer(service.build, service.BuildRequest(**body.model_dump()))
