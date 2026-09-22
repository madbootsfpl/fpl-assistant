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

from collections.abc import Callable

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src import service
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
    """Is the service up? Deliberately does not touch the database — ⭐ a health check that fails when the
    database is slow reports on the database, not the service, and would take the app out of rotation for a
    dependency it can survive."""
    return {"ok": True}


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


@app.post("/api/v1/squad/signals")
def squad_signals(body: SquadBody) -> dict:
    """What a manager should know about his own fifteen, **strongest evidence first**.

    ⭐ Each signal carries a `kind` — `official` · `departure` · `exodus` · `headline` — because they are
    not equally reliable, and an unexplained sell-off is not the same claim as an injury FPL confirmed.
    ⚠️ *Rendering them as one undifferentiated list is the page ADR-150 was written to replace.*

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
