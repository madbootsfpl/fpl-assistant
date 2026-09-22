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

    def validate(self) -> None:
        super().validate()
        _check_money("bank", self.bank)
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

    def validate(self) -> None:
        super().validate()
        _check_money("bank", self.bank)
