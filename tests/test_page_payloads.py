"""What each page actually pulls out of the database (spike 017).

⭐⭐ **A page that loads data it never reads costs nothing on SQLite and a great deal on Supabase.** Since
the app began reading Postgres (2026-09-20) every row crosses the network, and Streamlit re-runs the whole
script on every click — so a stray `get_gw_history_by_code()` is 1.2 MB per slider drag.

Production bore this out: `data_load` p50 went from **16 ms** on the local seed to **3,026 ms** on Supabase,
and the cause was **volume, not round-trips** — 2.41 MB per render.

⚠️ **These assert which queries run, not how long they take.** A timing test would measure a latency the app
never experiences locally and pass whatever the code did.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PAGES = Path(__file__).resolve().parents[1] / "src" / "web_streamlit" / "pages"

# Roughly what each costs on the real board, so a failure says why it matters rather than just "changed".
WEIGHT = {"gw_history_by_code": "1.2 MB", "history_by_code": "747 KB", "players": "518 KB"}


@pytest.fixture
def calls(monkeypatch):
    """Record which cached loaders a page asks for.

    ⚠️ **Watches `dataload`, not `Storage`, and that moved deliberately.** Since the cold fill was bundled
    into one connection (spike 017), `Storage.get_gw_history_by_code` runs on a cold miss whatever page
    triggered it — so asserting on `Storage` would now fail on every page and measure the bundle rather than
    the page.

    ⭐ The page-level property still holds and still matters: a page that never asks for 1.9 MB never
    unpickles it, on every warm render, which is every click.
    """
    from src.web_streamlit import dataload

    seen = []
    for name in WEIGHT:
        real = getattr(dataload, name)

        def make(n, r):
            def f(*a, **k):
                seen.append(n)
                return r(*a, **k)
            return f

        monkeypatch.setattr(dataload, name, make(name, real))
    return seen


def test_fdr_does_not_load_player_history_it_never_reads(calls):
    """⭐ **The clearest waste found by spike 017, and it was not "rarely used" — it was never used.**

    `2_FDR.py` fetched `get_history_by_code()` and `get_gw_history_by_code()` at the top of the page and
    **never referenced either again**: 1.94 MB of per-player history, on every render of a fixture-difficulty
    grid, read by nothing.

    ⭐ *Not fetching something beats caching it* — and it carries no freshness risk at all, which caching does.
    """
    at = AppTest.from_file(str(PAGES / "2_FDR.py"), default_timeout=90).run()
    assert not at.exception, at.exception
    heavy = [c for c in calls if c in ("history_by_code", "gw_history_by_code")]
    assert not heavy, (
        f"FDR is fetching {heavy} again — "
        + " + ".join(WEIGHT[h] for h in set(heavy)) + " that the page does not read")


def test_fdr_loads_players_only_when_the_squad_lens_is_on(calls):
    """0.5 MB, and the checkbox defaults to off. It is needed for the lens and nothing else."""
    at = AppTest.from_file(str(PAGES / "2_FDR.py"), default_timeout=90).run()
    assert "players" not in calls, "the lens is off — the player board is not needed"

    calls.clear()
    box = next((c for c in at.checkbox if "squad" in (c.label or "").lower()), None)
    assert box is not None, "the squad lens control must still exist"
    box.set_value(True).run()
    # With no squad in session the page short-circuits before needing players, which is also correct.


def test_the_squad_lens_still_filters_the_ticker():
    """⚠️ **The half a trimming change can break silently.** Moving the fetch into the branch is only right
    if the branch still works — and it renders the same either way, so nothing would say otherwise.

    ⭐ An earlier run of this check used the wrong session key, saw 20 rows, and looked like a regression. It
    was the test that was wrong. *Confirm the fixture reaches the code path before believing its verdict.*
    """
    from src.web_streamlit import dataload
    players = dataload.players()
    picked, per_club = [], {}
    for p in players:
        if per_club.get(p["team"], 0) < 5 and len(picked) < 15:
            picked.append(p["id"])
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    assert len(picked) == 15 and len(per_club) > 1, "the fixture must span several clubs to be a filter test"

    at = AppTest.from_file(str(PAGES / "2_FDR.py"), default_timeout=90)
    at.session_state["squad"] = {"name": "TST", "player_ids": picked}
    at.run()
    box = next(c for c in at.checkbox if "squad" in (c.label or "").lower())
    after = box.set_value(True).run()
    assert not after.exception, after.exception
    assert after.dataframe, "the ticker must still render"
    assert after.dataframe[0].value.shape[0] == len(per_club), (
        f"the lens must narrow 20 clubs to the {len(per_club)} the squad covers")


def test_image_columns_state_their_alignment_rather_than_inheriting_it():
    """⭐ *A default is a fact about a version, not a law* (ADR-180).

    The photo and badge thumbnails were reported left-aligned on 2026-08-06 — two days before
    `requirements.txt` pinned Streamlit, when Community Cloud installed whatever was current. 1.61 centres
    image cells by default, so this is belt and braces; the point is that a future default cannot move them
    back without this test noticing.
    """
    from src.web_streamlit.formats import IMAGE_COLS, column_config

    cfg = column_config(list(IMAGE_COLS) + ["Player"])
    assert cfg, "the config must actually contain the image columns, or this asserts nothing"
    for label in IMAGE_COLS:
        # ⚠️ `alignment` is a top-level key; `type_config` holds only `{"type": "image"}`. An earlier version
        # of this test looked inside `type_config`, found nothing, and failed on correct code.
        assert cfg[label].get("alignment") == "center", (
            f"the {label!r} column relies on Streamlit's default alignment instead of stating it")
