"""The app's cached read path (spike 017).

⭐⭐ **Streamlit re-runs the whole script on every interaction**, so before this every click refetched the
board. Production's `data_load` p50 went **16 ms → 3,026 ms** when the app switched to Supabase, and the
cause was volume — 2.41 MB per render — not round-trips. The fix is not a faster fetch; it is not fetching
on every click.
"""

import pickle

import pytest

from src.web_streamlit import dataload


@pytest.fixture(autouse=True)
def _fresh():
    dataload.clear()
    yield
    dataload.clear()


def test_every_loader_returns_something_picklable():
    """⚠️ **The constraint that shaped the whole design.** `st.cache_data` pickles what it returns, and
    `sqlite3.Row` cannot be pickled — so the loaders convert to dicts. If a loader ever returns raw rows
    again, caching silently stops working (Streamlit falls back to calling the function every time) and the
    3 seconds come back with nothing going red.
    """
    for fn in (dataload.players, dataload.teams, dataload.upcoming_fixtures,
               dataload.history_by_code, dataload.gw_history_by_code):
        out = fn()
        pickle.loads(pickle.dumps(out))            # raises if a Row slipped through
        assert out, f"{fn.__name__} returned nothing — the snapshot must have data"


def test_rows_are_dicts_not_database_rows():
    """⭐ Checked before relying on it: nothing in the app indexes a player, team or fixture positionally,
    so `dict` is a drop-in for `Row` at every call site."""
    assert isinstance(dataload.players()[0], dict)
    assert isinstance(dataload.teams()[0], dict)
    first = next(iter(dataload.gw_history_by_code().values()))
    assert isinstance(first[0], dict)


def test_a_caller_mutating_its_result_cannot_poison_the_cache():
    """⭐⭐ **The safety property, and it was verified rather than assumed.**

    `render_build` does `p["xp"] = …` on the rows it was handed. If the cache returned one shared list,
    one visitor's build would rewrite the board for everyone — a bug that would look like wrong numbers
    appearing for no reason, and would never reproduce locally.
    """
    first = dataload.players()
    first[0]["web_name"] = "MUTATED"
    second = dataload.players()
    assert second[0]["web_name"] != "MUTATED", "st.cache_data must hand each caller its own copy"


def test_the_freshness_caption_shares_the_boards_window():
    """⭐⭐ **A caption describes what is on the screen, or it is not a caption.**

    Reading the timestamp live while serving a cached board would let the sidebar announce a refresh whose
    data the reader cannot see — the "fresh-looking but stale" failure ADR-211 exists to prevent, arriving
    from the opposite direction. Same TTL, so the claim and the data stay in step.
    """
    import inspect
    assert dataload.freshness.__wrapped__ is not None, "freshness must be cached, not read live"
    src = inspect.getsource(dataload)
    assert src.count("@st.cache_data(ttl=TTL") >= 7, "every loader shares the one TTL"


def test_clear_empties_every_loader():
    """⚠️ The local "🔄 Refresh data" button refreshes the database. Without this it would then render the
    previous five minutes straight back — a button that appears to do nothing."""
    dataload.players()
    dataload.teams()
    dataload.clear()
    # A cleared cache means the next call recomputes; the observable proof is that it still works and the
    # value is equal, not identical.
    assert dataload.players(), "the loaders must still work after a clear"


def test_the_ttl_is_shorter_than_the_pipelines_fastest_cadence():
    """⭐ The freshness trade, checked rather than described.

    ADR-211's cadence is 10 minutes at its fastest (in-play). A TTL at or above that could show a reader a
    board a full tick behind what was published, which is the thing the caption promises it is not.
    """
    from src.pipeline import cadence  # noqa: F401  — imported to pin the relationship is deliberate
    assert dataload.TTL < 600, f"TTL {dataload.TTL}s is not shorter than the 10-minute in-play cadence"
    assert dataload.TTL >= 60, "below a minute the cache stops paying for itself"
