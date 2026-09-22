"""One player's fingerprint, ranked within his position (ADR-250).

⭐⭐ **Within position, never across the league.** A defender's attacking threat and a forward's are not
the same question — ranked together, every defender would look poor at a thing defenders are not asked to
do. ⚠️ *A single scale across incomparable roles is a ranking that flatters and punishes by position.*
"""

import pytest

from src import service
from src.storage import Storage


@pytest.fixture(scope="module")
def store():
    s = Storage()
    yield s
    s.close()


@pytest.fixture(scope="module")
def someone(store):
    """A player with real minutes, so the fingerprint is not all blanks."""
    return max(store.get_players(), key=lambda p: p["minutes"] or 0)


def test_the_fingerprint_has_every_axis(store, someone):
    out = service.player_dna(service.PlayerDnaRequest(player_id=someone["id"]), store=store)
    assert len(out["axes"]) == 8, "the eight axes are the fingerprint (ADR-118)"
    for axis in out["axes"]:
        assert axis["label"] and axis["sublabel"]
        p = axis["percentile"]
        assert p is None or 0 <= p <= 100


def test_it_says_which_field_he_was_ranked_in(store, someone):
    """⭐⭐ **The field, not just the place in it.**

    ⚠️ *"84th"* alone invites over-reading. Early in a season the pool can be **ten players** — this board
    has exactly that for midfielders — and a reader has to be able to see it before deciding what a
    percentile is worth.
    """
    out = service.player_dna(service.PlayerDnaRequest(player_id=someone["id"]), store=store)
    assert out["pool_size"] > 0
    assert out["min_minutes"] > 0
    assert isinstance(out["low_minutes"], bool)


def test_peers_are_the_same_position(store):
    """⭐ The property that makes the number mean anything: a keeper is ranked against keepers.

    ⚠️ Checked by **counting the pool against the board**, not by trusting a label — the pool size has to
    match the number of same-position players past the floor.
    """
    from src.analytics.player_dna import MIN_MINUTES

    players = [dict(p) for p in store.get_players()]
    for position in ("GK", "DEF", "MID", "FWD"):
        target = max((p for p in players if p["position"] == position),
                     key=lambda p: p["minutes"] or 0)
        out = service.player_dna(service.PlayerDnaRequest(player_id=target["id"]), store=store)
        expected = sum(1 for p in players
                       if p["position"] == position and (p["minutes"] or 0) >= MIN_MINUTES)
        assert out["pool_size"] == expected, (
            f"{position}: ranked against {out['pool_size']} but the board has {expected}"
        )


def test_a_player_below_the_floor_is_ranked_anyway_and_captioned(store):
    """⚠️⚠️ **Ranked, not excluded** (ADR-118). Dropping him would lose a player a manager is actively
    considering — ⭐ *the honest move is to answer and caption the answer*, which is what `low_minutes` is
    for."""
    from src.analytics.player_dna import MIN_MINUTES

    fringe = next((p for p in store.get_players()
                   if 0 < (p["minutes"] or 0) < MIN_MINUTES and p["position"]), None)
    assert fringe is not None, "no fringe player on this board to test with"

    out = service.player_dna(service.PlayerDnaRequest(player_id=fringe["id"]), store=store)
    assert out["low_minutes"] is True
    assert out["axes"], "a fringe player got no fingerprint at all"


def test_the_recent_run_comes_with_it(store, someone):
    """⭐ The fingerprint is a shape; the last five are what produced it. Sending both saves a round trip
    on the one screen where a reader will want to check one against the other."""
    out = service.player_dna(service.PlayerDnaRequest(player_id=someone["id"]), store=store)
    assert out["recent"], f"{someone['web_name']} has minutes but no appearances"
    for row in out["recent"]:
        assert set(row) == {"gameweek", "points", "minutes", "opponent", "home"}


def test_an_unknown_player_is_refused_by_name(store):
    with pytest.raises(ValueError, match="no player with id"):
        service.player_dna(service.PlayerDnaRequest(player_id=999999), store=store)


def test_no_player_is_refused(store):
    with pytest.raises(ValueError, match="no player given"):
        service.player_dna(service.PlayerDnaRequest(player_id=0), store=store)
