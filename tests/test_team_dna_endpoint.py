"""Every club's fingerprint, ranked across the league (ADR-247).

⭐⭐ **Team DNA, not player DNA, and that is the choice.** A player's fingerprint answers *what kind of
player is he?* — which the app already answers twice, on the expanding card (ADR-237) and in Boot Battle
(ADR-236). A club's answers *is this attack actually any good?*, which is what decides between two players
from different sides, and the app could not answer it at all.
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
def answer(store):
    return service.team_dna(service.TeamDnaRequest(horizon=1), store=store)


def test_every_club_is_ranked(answer, store):
    assert len(answer["teams"]) == len({t["short_name"] for t in store.get_teams()})


def test_best_first_and_stable(store):
    """⚠️ Ties broken by name, not left to dict order — ⭐ *an unstable sort is a diff that appears from
    nowhere*, and two runs of the same data must not disagree about the table."""
    once = service.team_dna(service.TeamDnaRequest(horizon=1), store=store)["teams"]
    twice = service.team_dna(service.TeamDnaRequest(horizon=1), store=store)["teams"]
    assert [t["team"] for t in once] == [t["team"] for t in twice]

    scores = [t["score"] for t in once]
    assert scores == sorted(scores, reverse=True)
    for a, b in zip(once, once[1:], strict=False):
        if a["score"] == b["score"]:
            assert a["name"] <= b["name"], f"{a['name']} before {b['name']} on equal scores"


def test_every_axis_is_a_percentile_or_honestly_absent(answer):
    """⭐ The whole reason eight different units can share one row of bars.

    ⚠️ **Null means unranked, not zero.** An empty bar for *"we could not rank this"* reads as *"worst in
    the league at it"* — a different and wrong claim, and the client relies on the distinction.
    """
    for club in answer["teams"]:
        assert club["axes"], f"{club['name']} has no axes"
        for axis in club["axes"]:
            p = axis["percentile"]
            assert p is None or 0 <= p <= 100, f"{club['name']} {axis['label']} = {p}"
            assert axis["label"] and axis["sublabel"]


def test_the_squad_marks_clubs_and_filters_nothing(store):
    """⚠️⚠️ **A mark, never a filter.** ⭐ *A league table you can see yourself in is a different object
    from a league table of the clubs you already own* — and a request that quietly narrowed to your own
    sides would make the grades meaningless, because they are ranks across all twenty.
    """
    players = store.get_players()
    squad = [p["id"] for p in players[:15]]
    mine = {p["team"] for p in players if p["id"] in set(squad)}

    plain = service.team_dna(service.TeamDnaRequest(horizon=1), store=store)
    marked = service.team_dna(service.TeamDnaRequest(player_ids=squad, horizon=1), store=store)

    assert len(marked["teams"]) == len(plain["teams"])
    assert [t["team"] for t in marked["teams"]] == [t["team"] for t in plain["teams"]]
    assert not any(t["yours"] for t in plain["teams"]), "clubs were marked without a squad"
    for club in marked["teams"]:
        assert club["yours"] == (club["team"] in mine)


def test_a_grade_is_a_letter_managers_already_speak(answer):
    """⭐ A→D, not a number they would have to learn a scale for."""
    assert {t["grade"] for t in answer["teams"]} <= {"A+", "A", "B", "C", "D"}
    for club in answer["teams"]:
        assert 0 <= club["score"] <= 100


def test_insights_use_the_webs_own_vocabulary(answer):
    """⚠️ The same four kinds the web renders (ADR-118). ⭐ *A fifth kind invented for the phone would be a
    second vocabulary for one idea*, and the app would start describing the same fact two ways."""
    kinds = {i["kind"] for club in answer["teams"] for i in club["insights"]}
    assert kinds <= {"good", "sp", "info", "warn"}, f"unexpected insight kinds: {kinds}"
    assert kinds, "no club produced a single insight"


def test_the_payload_is_small_enough_to_fetch_whole(answer):
    """⚠️ Twenty clubs × eight axes × four insights. ⭐ Measured, because the app fetches it in one go and
    the number is the reason that is allowed."""
    import json

    kb = len(json.dumps(answer, separators=(",", ":")).encode()) / 1024
    assert kb < 40, f"{kb:.0f} KB is past the point this should be one fetch"


# ── two branches the live board cannot reach ─────────────────────────────────────────────────────
#
# ⚠️⚠️ Measured, not assumed: today's board has **zero null percentiles and zero tied scores**, so two
# mutations — turning an unranked axis into a 0, and dropping the tie-break — survived the tests above by
# being no-ops. ⭐ *A mutation that survives because the data has no instance of the thing under test says
# nothing about the test.* These construct the instance.

def _club(team, name, score, grade="B", percentile=50):
    from src.analytics.player_dna import Axis
    from src.analytics.team_dna import TeamDNA

    return TeamDNA(
        team=team, name=name, grade=grade, grade_score=score,
        axes=[Axis(label="Attacking Threat", sublabel="xG", value=1.0, percentile=percentile)],
    )


def test_an_unranked_axis_stays_unranked(monkeypatch, store):
    """⚠️⚠️ **Null means unranked, not zero.** An empty bar for *"we could not rank this"* reads as
    *"worst in the league at it"* — a different and wrong claim, and the phone draws exactly that bar."""
    from src.service import answers

    monkeypatch.setattr(answers, "team_dna_all",
                        lambda *a, **k: {"ARS": _club("ARS", "Arsenal", 80, percentile=None)})
    out = service.team_dna(service.TeamDnaRequest(horizon=1), store=store)
    assert out["teams"][0]["axes"][0]["percentile"] is None


def test_tied_clubs_are_ordered_by_name_whatever_order_they_arrive_in(monkeypatch, store):
    """⭐⭐ **The tie-break is about INPUT order, which is why comparing two runs could not see it.**

    Python's sort is stable and the store hands the clubs over in a fixed order, so a test that ran the
    same query twice agreed with itself no matter what. ⚠️ *Stability is not determinism when the input
    can be reordered* — a schema change, a different index, another data source. This shuffles.
    """
    from src.service import answers

    forwards = {"BUR": _club("BUR", "Burnley", 50), "AVL": _club("AVL", "Aston Villa", 50)}
    backwards = dict(reversed(list(forwards.items())))

    order = []
    for arrival in (forwards, backwards):
        monkeypatch.setattr(answers, "team_dna_all", lambda *a, **k: arrival)
        out = service.team_dna(service.TeamDnaRequest(horizon=1), store=store)
        order.append([t["name"] for t in out["teams"]])

    assert order[0] == order[1] == ["Aston Villa", "Burnley"], order
