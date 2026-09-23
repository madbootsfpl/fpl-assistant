"""What a client sends — ids and options, never rows.

⭐ **Ids, not player rows** (mobile audit §4.2). A client that uploaded rows would be defining the engine's
input, which is how two implementations of one rule appear; this codebase has three ADRs about exactly that
(123, 127, 181). The server loads the board; the client says who.

⭐⭐ **Every check here exists because its absence produces a PLAUSIBLE answer, not a crash.** A squad of
nine analyses fine and simply projects less. A bench id that is not in the squad benches nobody and fields
all fifteen. Those are the failures worth refusing.
"""

from dataclasses import dataclass, field

DEFAULT_HORIZON = 5
MAX_HORIZON = 8          # the UI's own slider maximum — refusing 8 would refuse the app's top setting
MAX_PLAN = 3             # the Transfer tab plans at most three coordinated moves
FPL_BUDGET = 100.0


def _check_horizon(horizon: int) -> None:
    if not 1 <= horizon <= MAX_HORIZON:
        raise ValueError(f"horizon {horizon} is outside 1-{MAX_HORIZON}")


def _check_money(name: str, amount: float) -> None:
    # ⚠️ A negative bank is not a rounding artefact — it silently makes every transfer unaffordable, and the
    # answer comes back as "no moves found", which reads as a settled squad rather than a bad request.
    if amount < 0:
        raise ValueError(f"{name} cannot be negative")


@dataclass(frozen=True)
class SquadRequest:
    """A squad, and how far ahead to look. The base every squad-shaped question extends."""

    player_ids: list[int]
    bench_ids: list[int] = field(default_factory=list)
    horizon: int = DEFAULT_HORIZON

    def validate(self) -> None:
        if not self.player_ids:
            raise ValueError("no players given")
        if len(set(self.player_ids)) != len(self.player_ids):
            raise ValueError("duplicate player ids")
        _check_horizon(self.horizon)
        stray = set(self.bench_ids) - set(self.player_ids)
        if stray:
            raise ValueError(f"bench ids not in the squad: {sorted(stray)}")


@dataclass(frozen=True)
class TransfersRequest(SquadRequest):
    """`count` > 1 asks for a **coordinated plan** whose moves share a bank, not a menu of alternatives
    (ADR-191) — so the gains add up rather than double-counting the same money."""

    bank: float = 0.0
    count: int = 1
    limit: int = 5

    def validate(self) -> None:
        super().validate()
        _check_money("bank", self.bank)
        if not 1 <= self.count <= MAX_PLAN:
            raise ValueError(f"count {self.count} is outside 1-{MAX_PLAN}")
        if self.limit < 1:
            raise ValueError("limit must be at least 1")


@dataclass(frozen=True)
class CaptainRequest(SquadRequest):
    """⚠️ `horizon` is accepted and **not used for the ranking**: captaincy is always the next gameweek.
    It is kept so one client-side squad object serves every endpoint, and stated here so nobody concludes
    from the signature that a five-week captain pick is on offer."""

    limit: int = 5

    def validate(self) -> None:
        super().validate()
        if self.limit < 1:
            raise ValueError("limit must be at least 1")


@dataclass(frozen=True)
class GameweekRequest(SquadRequest):
    """⭐ `free` and `bank` are the manager's **actual position**, not defaults (ADR-191). Hard-coding them
    had the app advising a position the manager was not in — and a stated assumption can be corrected where
    a silent one cannot, so both come back in the answer."""

    bank: float = 0.0
    free: int = 1

    def validate(self) -> None:
        super().validate()
        _check_money("bank", self.bank)
        if not 0 <= self.free <= 5:
            raise ValueError(f"free transfers {self.free} is outside 0-5")


@dataclass(frozen=True)
class RouteRequest(SquadRequest):
    """*"What would it take to field X?"* (ADR-207) — the incoming player is fixed and the **route** is
    searched, which is the inverse of what `transfers` asks."""

    target_id: int | None = None
    bank: float = 0.0

    # ⭐ **Optional, and its absence changes the answer rather than being ignored.** With a manager id the
    # endpoint knows which chips have been **spent**; without one it says *unknown* — ⚠️ never *available*,
    # because recommending a wildcard someone played in GW4 is a wrong answer delivered confidently.
    manager_id: int | None = None

    def validate(self) -> None:
        super().validate()
        _check_money("bank", self.bank)
        if self.manager_id is not None and self.manager_id < 1:
            raise ValueError("no manager id given")
        if not self.target_id:
            raise ValueError("no target player given")


@dataclass(frozen=True)
class BuildRequest:
    """Build a squad from nothing — ⚠️ **the one request with no `player_ids`**, so it does not extend
    `SquadRequest`. Making it inherit would have forced a meaningless empty list on every caller."""

    budget: float = FPL_BUDGET
    horizon: int = DEFAULT_HORIZON
    include_ids: list[int] = field(default_factory=list)
    exclude_ids: list[int] = field(default_factory=list)

    def validate(self) -> None:
        _check_horizon(self.horizon)
        if self.budget <= 0:
            raise ValueError("budget must be positive")
        clash = set(self.include_ids) & set(self.exclude_ids)
        if clash:
            # ⚠️ Without this the solver simply returns no squad, and "Infeasible" reads as *"your budget is
            # too low"* rather than *"you asked for a player you also banned"*.
            raise ValueError(f"ids both included and excluded: {sorted(clash)}")


@dataclass(frozen=True)
class MyTeamRequest:
    """*"Show me my team"* — ⚠️ **the one request that names a person rather than a squad.**

    Every other endpoint takes player ids, because a client that uploaded rows would be defining the
    engine's input. This one takes an **FPL manager id**, which is public, and the server fetches the squad
    — so the phone never has to know how to read FPL's picks payload either.
    """

    manager_id: int | None = None
    horizon: int = 1
    # ⚠️ **Manager-entered, because FPL does not publish it.** The entry payload carries bank and value but
    # **not free transfers** — those sit behind a login. ADR-191 is the record of what happens when it is
    # guessed: the app advised a position the manager was not in. ⭐ A stated assumption can be corrected
    # where a silent one cannot, so it comes back in the answer.
    free_transfers: int = 1

    # ⭐⭐ **A DRAFT: price this squad, not the one FPL holds.** The app lets a manager try a swap before
    # committing to it — and a phone that could only ever show the committed team could not answer *"what
    # if?"*, which is the question the whole product exists for.
    #
    # ⚠️ **The manager is still fetched.** The name, the bank, the deadline and the armbands all come from
    # FPL; only the fifteen change. A draft that invented its own bank would let a manager plan a transfer
    # he cannot afford.
    draft_player_ids: list[int] = field(default_factory=list)
    draft_bench_ids: list[int] = field(default_factory=list)

    def validate(self) -> None:
        # ⭐ The horizon defaults to **1**, not five, and that is the screen's decision showing through: a
        # landing pitch is about *this* gameweek. Every other endpoint looks further by default.
        _check_horizon(self.horizon)
        if not self.manager_id or self.manager_id < 1:
            raise ValueError("no manager id given")
        if not 0 <= self.free_transfers <= 5:
            raise ValueError(f"free transfers {self.free_transfers} is outside 0-5")
        if self.draft_player_ids:
            if len(set(self.draft_player_ids)) != len(self.draft_player_ids):
                raise ValueError("duplicate player ids in the draft")
            # ⚠️ Fifteen, exactly. A draft of fourteen analyses fine and simply projects less — the
            # failure this codebase keeps writing down: *a wrong answer wearing the shape of a right one.*
            if len(self.draft_player_ids) != 15:
                raise ValueError(f"a draft squad needs 15 players, got {len(self.draft_player_ids)}")
            stray = set(self.draft_bench_ids) - set(self.draft_player_ids)
            if stray:
                raise ValueError(f"draft bench ids not in the draft squad: {sorted(stray)}")


@dataclass(frozen=True)
class ReplacementsRequest(SquadRequest):
    """*"Who could I put in instead of him?"* — the manual transfer (ADR-226).

    ⭐ The inverse of `TransfersRequest`, which picks for you. This lists what you *could* do, because a
    manual transfer is a decision already made and wanting to be priced rather than recommended.
    """

    out_id: int | None = None
    bank: float = 0.0
    limit: int = 40

    def validate(self) -> None:
        super().validate()
        _check_money("bank", self.bank)
        if not self.out_id:
            raise ValueError("no player to replace")
        if self.out_id not in set(self.player_ids):
            # ⚠️ Without this the search runs against a player you do not own and returns a perfectly
            # plausible list — ⭐ *a wrong answer wearing the shape of a right one.*
            raise ValueError(f"player {self.out_id} is not in this squad")
        if self.limit < 1:
            raise ValueError("limit must be at least 1")


@dataclass(frozen=True)
class ChipsRequest(SquadRequest):
    """*"When should I play my chips?"* (ADR-082/229).

    ⚠️⚠️ **`horizon` is ignored, and that is the whole point.** ADR-166: a chip is a **season** decision
    with a fixed expiry, so the question is never *"is this week good?"* but *"is this week better than the
    weeks I have left?"* — and answering it over a one-gameweek window is not a smaller version of that
    question, it is **a different question**. The window is the **chip's deadline**, derived here.

    ⭐ The field stays on the request so one client-side squad object serves every endpoint, and this
    docstring is why nobody should conclude from the signature that it narrows the search.
    """

    bank: float = 0.0

    # ⭐ **Optional, and its absence changes the answer rather than being ignored.** With a manager id the
    # endpoint knows which chips have been **spent**; without one it reports *unknown* — ⚠️ never
    # *available*, because recommending a wildcard someone played in GW4 is a wrong answer delivered
    # confidently.
    manager_id: int | None = None

    def validate(self) -> None:
        super().validate()
        _check_money("bank", self.bank)
        if self.manager_id is not None and self.manager_id < 1:
            raise ValueError("no manager id given")


@dataclass(frozen=True)
class PlayersRequest:
    """The ranked market — ⚠️ **the one request with no squad at all** (ADR-230).

    ⭐ **Returns everyone, ranked, in one call**, and leaves searching and filtering to the client. Spike
    017 measured the whole board at ~162 KB; filtering 667 rows locally is instant, where a round trip per
    keystroke is not. *The cheap thing to send once is cheaper than the small thing sent constantly.*
    """

    horizon: int = DEFAULT_HORIZON
    limit: int = 800

    def validate(self) -> None:
        _check_horizon(self.horizon)
        if self.limit < 1:
            raise ValueError("limit must be at least 1")


@dataclass(frozen=True)
class TrendingRequest:
    """What the crowd is doing — ⚠️ **display-only, and never xP** (ADR-057/266).

    ⭐⭐ *"Lots of people did this" is a fact about other managers, not about the player.* It is the reason
    a template forms, and on its own it is not a reason to join one — which is why these numbers have
    never been allowed near the ranking, and are not here either.

    `player_ids` is optional and does **not** narrow the boards: it only lets a row come back flagged
    `owned`, so the app can say *"you have him"* without matching ids itself (ADR-245's pattern).
    """

    by: str = "in"
    limit: int = 15
    player_ids: tuple[int, ...] = ()

    def validate(self) -> None:
        from src.analytics.crowd import TREND_BYS

        if self.by not in TREND_BYS:
            raise ValueError(f"by must be one of {sorted(TREND_BYS)}, not {self.by!r}")
        if not 1 <= self.limit <= 50:
            raise ValueError(f"limit must be 1-50, not {self.limit}")


@dataclass(frozen=True)
class TickerRequest:
    """The fixture-difficulty grid — ⚠️ **the other request with no squad at all** (ADR-265).

    ⭐ It is about the **league**, not about you. A ticker answers *"whose run turns good?"*, which is the
    question you ask before you have decided who to buy — so asking it does not require a squad, and
    making it require one would have narrowed it to the clubs you already own.
    """

    next_n: int = 6
    source: str = "fpl"

    def validate(self) -> None:
        if not 1 <= self.next_n <= 10:
            raise ValueError(f"next_n must be 1-10, not {self.next_n}")
        # ⚠️ `elo` is deliberately absent: it needs `elo_bands` the caller would have to supply, and an
        # option that silently returns undefined difficulties is worse than one that is not offered.
        if self.source not in ("fpl", "custom"):
            raise ValueError(f"source must be 'fpl' or 'custom', not {self.source!r}")


#: ⚠️ A cap, because this endpoint relays to the owner's own sink. It is not a general abuse defence —
#: see `answers.feedback` — it is the difference between a bug report and a payload.
MAX_FEEDBACK = 4000


@dataclass(frozen=True)
class FeedbackRequest:
    """A note from a tester (ADR-231).

    ⚠️ **The one request that carries free text**, which is why it is capped and why the server never
    interprets it — it is relayed verbatim to a sink the owner controls.
    """

    message: str = ""
    contact: str = ""
    screen: str = ""
    version: str = ""

    def validate(self) -> None:
        if not self.message.strip():
            raise ValueError("no message given")
        if len(self.message) > MAX_FEEDBACK:
            raise ValueError(f"message is longer than {MAX_FEEDBACK} characters")
        if len(self.contact) > 200:
            raise ValueError("contact is too long")


@dataclass(frozen=True)
class SignalsRequest(SquadRequest):
    """*"What should I know?"* — about **your** players, or about the market (ADR-150/232/245).

    ⭐ Squad scope is the decision layer: a manager checking a phone before a deadline is asking about the
    fifteen he owns. ⭐ **Global** is the exploration layer, and it is here because the alternative was a
    separate Trending screen saying the same things in a different shape.

    ⚠️ `scope` defaults to `"squad"` — the narrower, cheaper answer. *A default that widens the question is
    a default that surprises somebody.*
    """

    # ⭐ Optional here, unlike every other squad-shaped request: a global sweep has no squad to give.
    player_ids: list[int] = field(default_factory=list)
    scope: str = "squad"

    def validate(self) -> None:
        # ⚠️ Global needs no squad, so the parent's "give me fifteen ids" rule cannot apply to it.
        if self.scope not in ("squad", "global"):
            raise ValueError(f"scope must be 'squad' or 'global', not {self.scope!r}")
        if self.scope == "squad":
            super().validate()


@dataclass(frozen=True)
class PlayerDnaRequest:
    """One player's eight-axis fingerprint, ranked **within his position** (ADR-118, ADR-250).

    ⭐ Within position, not across the league: a defender's attacking threat and a forward's are not the
    same question, and ranking them together would make every defender look poor at a thing defenders are
    not asked to do.
    """

    player_id: int
    horizon: int = DEFAULT_HORIZON

    def validate(self) -> None:
        if not self.player_id:
            raise ValueError("no player given")
        _check_horizon(self.horizon)


@dataclass(frozen=True)
class TeamDnaRequest:
    """Every club's eight-axis fingerprint, ranked across the league (ADR-118, ADR-247).

    ⭐ `player_ids` is **optional and does not filter anything** — it only marks which clubs your own
    players come from. A league table you can see yourself in is a different object from a league table.
    """

    player_ids: list[int] = field(default_factory=list)
    horizon: int = DEFAULT_HORIZON

    def validate(self) -> None:
        _check_horizon(self.horizon)


@dataclass(frozen=True)
class CompareRequest:
    """**Boot Battle** — two players, side by side (ADR-110/236).

    ⚠️ **No squad.** A comparison is about two players, and requiring the fifteen would stop the transfer
    screen asking it about a player you do not own — which is the only interesting case.
    """

    a_id: int | None = None
    b_id: int | None = None
    horizon: int = DEFAULT_HORIZON

    def validate(self) -> None:
        _check_horizon(self.horizon)
        if not self.a_id or not self.b_id:
            raise ValueError("two player ids are needed")
        if self.a_id == self.b_id:
            # ⚠️ Every row would tie and every winner would be None — a page that looks broken rather than
            # one that says "you asked the same question twice".
            raise ValueError("a player cannot be compared with himself")


@dataclass(frozen=True)
class PlayerRequest:
    """One player, in full — the **card** (ADR-109/237).

    ⭐ Fetched when a row is expanded, not with the list. The market is 481 players; carrying every stat
    for all of them so that one can be opened is the opposite of the trade the list was built on.
    """

    player_id: int | None = None
    horizon: int = DEFAULT_HORIZON

    def validate(self) -> None:
        _check_horizon(self.horizon)
        if not self.player_id:
            raise ValueError("no player given")
