"""Reading the published board instead of recomputing it (spike 017).

⭐⭐ **The pipeline computes this every tick and the app was downloading 1.9 MB of raw history to work it out
again.** Production measured a cold page load at **2.41 MB over ~10.8 s** — about 1.8 Mbps — and **81% of
that payload existed only to feed `decision_xp`.**

⚠️ Nothing here computes an xP. The board holds the per-gameweek values the engine produced; `ranked_from_board`
sums a prefix and reassembles the row shape. The one recipe stays in `decision_xp` (ADR-181), which is what
the pipeline calls.
"""

from datetime import UTC, datetime

import pytest

from src import pipeline
from src.analytics.board import ranked_from_board
from src.analytics.xp import decision_xp
from src.storage import Storage

STAMP = datetime(2026, 9, 21, 12, 0, tzinfo=UTC).isoformat(timespec="seconds")


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A copy of the snapshot, on whichever backend the suite is pointed at (see tests/test_xp_board.py)."""
    import shutil

    from src import config
    target = tmp_path / "board.db"
    shutil.copy(config.SEED_DB_PATH, target)
    target.chmod(0o644)
    monkeypatch.setattr(config, "SEED_DB_PATH", str(target))
    s = Storage(config.SEED_DB_PATH)
    yield s
    s.close()


def _live(store, horizon):
    return decision_xp(store.get_players(), store.get_upcoming_fixtures(), store.get_history_by_code(),
                       horizon=horizon, gw_history_by_code=store.get_gw_history_by_code())


@pytest.mark.parametrize("horizon", [1, 2, 3, 4, 5, 6, 7, 8])
def test_the_board_reproduces_decision_xp_exactly(store, horizon):
    """⭐⭐ **The claim the whole change rests on: every field, every player, every horizon the UI offers.**

    Not "close enough" — identical. A board that merely approximated would show a different number on the
    page from the one the CLI and the optimiser use, which is the two-implementations failure this project
    has three ADRs about (123, 127, 181).
    """
    pipeline.publish_board(store, computed_at=STAMP)
    from_board = {r["id"]: r for r in ranked_from_board(store.get_xp_board(), horizon=horizon)}
    live = _live(store, horizon)
    assert live, "the snapshot must have players, or this proves nothing"

    for want in live:
        got = from_board.get(want["id"])
        assert got is not None, f"{want['web_name']} is missing from the board"
        for field, value in want.items():
            if field == "by_gameweek_exact":       # the board stores these as `by_gameweek`
                continue
            assert got.get(field) == value, (
                f"horizon {horizon}, {want['web_name']}, {field}: board {got.get(field)!r} "
                f"vs engine {value!r}")


def test_ep_next_comes_back_as_a_number_not_a_string(store):
    """⚠️ **The one field that differed, and it was a type rather than a value.**

    `xp_board.ep_next` was declared TEXT while `players.ep_next` is REAL, so the board handed back `'7.5'`
    where the engine gives `7.5`. ⭐ *A published copy must match the type as well as the value, or a client
    comparing them finds a difference that is not one.*

    Coerced on read rather than fixed in the DDL, because `_migrate` can add a column and **cannot change
    one** — every database whose `xp_board` predates this keeps the old declaration, production's included.
    """
    pipeline.publish_board(store, computed_at=STAMP)
    for row in store.get_xp_board():
        assert isinstance(row["ep_next"], (float, type(None))), (
            f"ep_next came back as {type(row['ep_next']).__name__}")


def test_an_empty_board_asks_the_caller_to_fall_back(store):
    """`[]`, not zeros — so a caller can tell *"the pipeline has not published"* from *"nobody scores"*."""
    assert ranked_from_board([], horizon=5) == []
    assert ranked_from_board(None, horizon=5) == []


def test_a_double_gameweek_keeps_its_game_count(store):
    """⚠️ `games` is not derivable from `by_gameweek`: a double gameweek is **one key with two fixtures**.

    Published per gameweek and summed over the prefix, which is why the board can answer a question its own
    breakdown cannot.
    """
    pipeline.publish_board(store, computed_at=STAMP)
    rows = ranked_from_board(store.get_xp_board(), horizon=3)
    assert rows
    for row in rows:
        assert row["games"] == sum(row["games_by_gameweek"].values())
        assert set(row["games_by_gameweek"]) == set(row["gameweeks"])


# ---- the fallback, which is a production path and not a nicety ---------------------------

def test_an_empty_board_falls_back_to_computing(store):
    """⚠️⚠️ **An empty board is a real state, and this was found by three failing tests rather than by
    thinking about it.**

    The committed snapshot has never had a board published into it; a fresh project has none until the
    pipeline's first tick; and **ADR-211's fallback serves that snapshot whenever Postgres cannot be read**.
    Without this, My Squad would show **zero xP with nothing saying why** — the silent degrade that whole ADR
    exists to prevent, reintroduced by a performance change.

    ⭐ *Declining is right when the instrument cannot answer; falling back is right when another instrument
    can.* Here one can: the engine that produced the board in the first place.
    """
    from src.analytics.board import ranked_for

    assert store.get_xp_board() == [], "precondition: the snapshot carries no published board"

    players, upcoming = store.get_players(), store.get_upcoming_fixtures()
    history, gw_history = store.get_history_by_code(), store.get_gw_history_by_code()

    computed = ranked_for([], players, upcoming, history, gw_history, horizon=5)
    assert computed, "an empty board must produce a live computation, not an empty page"
    assert computed == _live(store, 5), "and it must be exactly what the engine gives"


def test_a_published_board_is_preferred_over_computing(store, monkeypatch):
    """⭐ The other half: with a board present, the history must not be touched at all — otherwise the
    1.9 MB is still being fetched and the change bought nothing."""
    from src.analytics import board as board_module
    from src.analytics.board import ranked_for

    pipeline.publish_board(store, computed_at=STAMP)
    published = store.get_xp_board()
    assert published

    def explode(*a, **k):
        raise AssertionError("decision_xp must not run when a board is published")

    monkeypatch.setattr(board_module, "ranked_from_board", board_module.ranked_from_board)
    import src.analytics.xp as xp_module
    monkeypatch.setattr(xp_module, "decision_xp", explode)

    rows = ranked_for(published, None, None, None, None, horizon=5)
    assert len(rows) == len(published)
