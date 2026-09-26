"""How old the board is, and whether a finished gameweek is missing from it (ADR-248).

⭐⭐⭐ **The app had no way to say how old its numbers were, so a stale database looked like a broken
engine.** The owner checked a player's last five, saw a blank against Coventry and no Arsenal fixture at
all, and reasonably asked why the app was not reflecting reality. It was reflecting reality — *a reality
from the previous afternoon.* The engine was right, the data was a day old, and nothing on the screen could
tell the difference.

⚠️⚠️ **`refreshed_at` alone is not the answer.** *"Updated 20 hours ago"* is fine on a Tuesday and useless
the evening a gameweek finishes. What matters is whether a **completed gameweek is missing** — a different
question, and one `backfill_due` already answers. ⭐ *Asking the pipeline's own question beats inventing a
second definition of "behind".*
"""

import pytest

from src import service
from src.service import answers
from src.storage import Storage


@pytest.fixture(scope="module")
def store():
    s = Storage()
    yield s
    s.close()


def as_manager(store, ids):
    squad = {"name": "Test XI", "player_ids": ids, "bench_ids": ids[-4:],
             "captain_id": ids[0], "vice_captain_id": ids[1]}
    real = answers.fetch_manager_team
    answers.fetch_manager_team = lambda entry_id, players: (squad, "")
    try:
        return service.my_team(service.MyTeamRequest(manager_id=1, horizon=1), store=store)
    finally:
        answers.fetch_manager_team = real


@pytest.fixture(scope="module")
def squad(store):
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in store.get_players():
        if need.get(p["position"], 0) and per_club.get(p["team"], 0) < 3 and len(picked) < 15:
            picked.append(p["id"])
            need[p["position"]] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return picked


def test_the_screen_a_manager_opens_carries_the_age(store, squad):
    """⚠️ **On `my-team`, not on `/health`.** A freshness field on the health route would be read by
    monitoring and by nobody else — ⭐ *the place to say "these numbers are from yesterday" is beside the
    numbers.*"""
    data = as_manager(store, squad)["data"]
    # ⭐ The **exact** set, which is why this test noticed `age_minutes` arriving (ADR-303) — ⚠️ *a test
    # that checked only for the keys it wanted would let a fifth appear unremarked.*
    assert set(data) == {"refreshed_at", "missing_gameweeks", "behind", "why", "age_minutes"}
    assert isinstance(data["behind"], bool)
    assert data["why"], "a freshness verdict with no reason is a mood, not a fact"
    # ⚠️⚠️ **Age sits BESIDE `behind`, never inside it.** `behind` is *a completed gameweek has no rows*;
    # age is *the last refresh was a while ago*. ⭐ Merging them is the mistake ADR-301 caught, where a
    # schema lag would have told nine testers their data was broken.
    assert isinstance(data["age_minutes"], (int, type(None)))


def test_it_names_the_missing_gameweeks_not_just_a_flag(store, squad, monkeypatch):
    """⭐ *"Missing GW5"* is a fact someone can act on; *"stale"* is a mood."""
    monkeypatch.setattr(answers, "backfill_due", None, raising=False)
    from src import pipeline

    monkeypatch.setattr(pipeline, "backfill_due",
                        lambda *a, **k: (True, "no stored history for GW[5]", {5}))
    data = as_manager(store, squad)["data"]
    assert data["behind"] is True
    assert data["missing_gameweeks"] == [5]


def test_a_freshness_check_never_takes_the_screen_down(store, squad, monkeypatch):
    """⚠️⚠️ **The one thing this must not do is break the pitch.**

    ⭐ A banner telling you the data might be wrong is worth having; a crash on the way to drawing it is
    not. If the check itself fails, the screen renders and says the check could not be made.
    """
    from src import pipeline

    def explode(*a, **k):
        raise RuntimeError("fixtures table went away")

    monkeypatch.setattr(pipeline, "backfill_due", explode)
    answer = as_manager(store, squad)
    assert answer["analysis"]["xi"], "the squad did not render"
    assert answer["data"]["behind"] is False
    assert "could not" in answer["data"]["why"]


def test_it_asks_the_pipelines_own_question(store, monkeypatch):
    """⭐⭐ **Not a second definition of "behind".** `backfill_due` decides when the scheduled job runs;
    if this used different reasoning, the app and the pipeline could disagree about whether the data is
    current — and the app would be the one a person believes.

    ⚠️ Asserted by *breaking* `backfill_due` and watching the answer change, which is the only way to show
    that the call is the one being made.
    """
    from src import pipeline

    seen = []

    def spy(fixtures, history):
        seen.append((len(list(fixtures)), len(history)))
        return False, "spied", set()

    monkeypatch.setattr(pipeline, "backfill_due", spy)
    out = answers._data_freshness(store)
    assert out["why"] == "spied"
    assert seen, "backfill_due was never called"
    # ⚠️ The whole fixture list, not just the upcoming ones — a completed gameweek is not "upcoming",
    # so the narrower list can never show anything as finished. (That mistake was made while writing
    # this, and it reported "nothing is due" for a board that was a gameweek behind.)
    assert seen[0][0] > 330, f"only {seen[0][0]} fixtures — that looks like the upcoming-only list"
