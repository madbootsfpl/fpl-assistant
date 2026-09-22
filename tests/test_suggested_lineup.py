"""The best XI you already own, offered where you are looking at it (ADR-244).

⭐⭐ **The pitch could already tell you the lineup was wrong and gave you no way to fix it.** This Week said
*"3 changes"* and named them; acting on it meant reading three lines, remembering them, and tapping four
shirts on a different screen. ⭐ *An app that can compute the answer and makes you transcribe it has
stopped halfway.*

⚠️⚠️ **The failure this guards is two screens recommending different teams.** `my_team` and `gameweek_plan`
now both answer "who should start", by different routes, from the same data. A drift between them would
not raise anything — it would just quietly make the app argue with itself.
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


@pytest.fixture(scope="module")
def owned(store):
    """A legal fifteen whose declared bench is deliberately WRONG, so there is something to suggest."""
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in sorted(store.get_players(), key=lambda p: -(p["total_points"] or 0)):
        if need.get(p["position"], 0) and per_club.get(p["team"], 0) < 3 and len(picked) < 15:
            picked.append(p)
            need[p["position"]] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return [p["id"] for p in picked]


def as_manager(store, ids, bench_ids):
    squad = {"name": "Test XI", "player_ids": ids, "bench_ids": bench_ids,
             "captain_id": ids[0], "vice_captain_id": ids[1]}
    real = answers.fetch_manager_team
    answers.fetch_manager_team = lambda entry_id, players: (squad, "")
    try:
        return service.my_team(service.MyTeamRequest(manager_id=1, horizon=1), store=store)
    finally:
        answers.fetch_manager_team = real


def test_the_two_screens_field_the_same_eleven(store, owned):
    """⭐⭐⭐ **The whole reason this is not a second implementation.**

    ⚠️ `my_team` reuses `best_legal_xi` on the same `lineup_xp` convention as `gameweek_plan`. If someone
    ever "simplifies" one of them, this is what says so — and nothing else would, because both answers are
    individually plausible.
    """
    bench = owned[-4:]
    week = service.gameweek(
        service.GameweekRequest(player_ids=owned, bench_ids=bench, horizon=1, bank=0.0, free=1),
        store=store)
    mine = as_manager(store, owned, bench)["suggested_lineup"]

    week_xi = {p["id"] for p in week["lineup"]["start"]}
    assert mine is not None, "a deliberately wrong bench produced no suggestion"
    assert set(mine["start"]) == week_xi


def test_a_squad_already_optimal_gets_no_suggestion(store, owned):
    """⭐ The absence of a strip IS the answer. A card that said "nothing to do" on every visit would be
    noise, and one that appeared with zero changes would be a lie."""
    week = service.gameweek(
        service.GameweekRequest(player_ids=owned, bench_ids=owned[-4:], horizon=1, bank=0.0, free=1),
        store=store)
    best_bench = [p["id"] for p in week["lineup"]["bench"]]
    assert as_manager(store, owned, best_bench)["suggested_lineup"] is None


def test_the_fifteen_are_never_changed(store, owned):
    """⚠️⚠️ **Lineup only.** Starting a player you own is free and reversible; a transfer costs points and
    cannot be undone. ⭐ *One button must not do both, whatever the xP says.*"""
    plan = as_manager(store, owned, owned[-4:])["suggested_lineup"]
    assert plan is not None
    assert set(plan["start"]) | set(plan["bench"]) == set(owned), (
        "the suggestion introduced or dropped a player — it must only reorder the fifteen you own"
    )
    assert len(plan["start"]) == 11 and len(plan["bench"]) == 4


def test_the_gain_is_real_points_and_not_the_selection_fiction(store, owned):
    """⚠️ ADR-154 ranks a reported leaver as if he scores nothing **for selection only**. Quoting a gain
    computed from that map would credit the manager with points a fiction created."""
    plan = as_manager(store, owned, owned[-4:])["suggested_lineup"]
    answer = as_manager(store, owned, owned[-4:])["analysis"]
    xp = {p["id"]: p["xp"] for p in answer["xi"] + answer["bench"]}

    declared_xi = [i for i in owned if i not in owned[-4:]]
    expected = round(sum(xp[i] for i in plan["start"]) - sum(xp[i] for i in declared_xi), 1)
    assert plan["gain"] == expected
    assert plan["gain"] > 0, "a suggestion that loses points should not have been made"


def test_the_bench_comes_back_in_substitution_order(store, owned):
    """⭐ Applying the plan must not silently reorder the bench into something the auto-sub disagrees with.

    ⚠️⚠️ An earlier version asserted only that the bench held exactly one keeper — which is true of **any**
    ordering, so a mutation replacing `bench_order` with the raw list survived it. ⭐ *An assertion that
    every permutation satisfies is not testing order.*
    """
    from src.analytics import bench_order

    answer = as_manager(store, owned, owned[-4:])
    plan = answer["suggested_lineup"]
    xp = {p["id"]: p["xp"] for p in answer["analysis"]["xi"] + answer["analysis"]["bench"]}
    by_id = {p["id"]: p for p in store.get_players()}

    expected = [p["id"] for _, p in bench_order([by_id[i] for i in plan["bench"]], xp)]
    assert plan["bench"] == expected, (
        f"bench came back as {[by_id[i]['web_name'] for i in plan['bench']]}, "
        f"FPL would substitute {[by_id[i]['web_name'] for i in expected]}"
    )


# ── the leaver branch, which live data cannot reach ──────────────────────────────────────────────
#
# ⚠️⚠️ **There are zero reported leavers on the board today**, measured rather than assumed. Two mutations
# — scoring the gain on the zeroed map, and not zeroing at all — survived the tests above for exactly that
# reason: they were no-ops on this data. ⭐ *A mutation that survives because the population has no instance
# of the thing under test says nothing about the test, and reporting it as coverage would be a lie.*
#
# ⭐ So these call `_suggested_lineup` directly with a constructed leaver. Building an input is the wrong
# move when live data can reach the branch and the right one when it cannot.

def test_a_reported_leaver_is_not_selected(store, owned):
    """⭐ ADR-154: a player the press says is leaving is ranked as if he scores nothing — **for selection
    only**. ⚠️ This is the one place where letting the projection win would put him in your XI.

    ⭐⭐ **Real players, one constructed fact.** An all-synthetic squad was tried first and `best_legal_xi`
    returned an empty XI from it — the optimiser needs fields a hand-written dict does not have. *A fixture
    that the code under test cannot consume is not a simpler test, it is a different one.*
    """
    from src.service.answers import _suggested_lineup

    squad = [p for p in store.get_players() if p["id"] in set(owned)]
    answer = as_manager(store, owned, owned[-4:])["analysis"]
    xp = {p["id"]: p["xp"] for p in answer["xi"] + answer["bench"]}

    # ⭐ The most certain starter in the squad — if ADR-154 can bench HIM, it works.
    best = max(xp, key=lambda i: xp[i])
    assert best in _suggested_lineup(squad, owned[-4:], xp, {})["start"], (
        "the fixture is wrong — the squad's best player should be a shoo-in when he is not leaving"
    )

    withleaver = _suggested_lineup(squad, owned[-4:], xp, {best: 5})
    assert withleaver is not None
    assert best not in withleaver["start"], "a reported leaver was picked for the XI"


def test_the_gain_never_counts_the_selection_fiction(store, owned):
    """⚠️⚠️ The zeroing is a **selection device**. Quoting a gain computed from it would credit the manager
    with points a fiction created — ⭐ *the number on the button has to be one he can actually get.*

    Concretely: with the best player zeroed for selection, the fictional gain is enormous and the real one
    is small or negative. This pins the number to the real map.
    """
    from src.service.answers import _suggested_lineup

    squad = [p for p in store.get_players() if p["id"] in set(owned)]
    bench = owned[-4:]
    answer = as_manager(store, owned, bench)["analysis"]
    xp = {p["id"]: p["xp"] for p in answer["xi"] + answer["bench"]}

    # ⚠️⚠️ **Chosen from the DECLARED XI, not from the whole squad.** Zeroing a player who is already
    # benched changes neither total, so the two numbers agree and the test proves nothing.
    #
    # ⭐ The guard below caught exactly that when the board was refreshed and the top-xP player moved onto
    # the bench — *a fixture derived from live data drifts with it, and an assertion that says so is worth
    # more than one that quietly starts passing for free.*
    best = max((i for i in owned if i not in set(bench)), key=lambda i: xp[i])

    plan = _suggested_lineup(squad, bench, xp, {best: 5})
    assert plan is not None

    declared_xi = [i for i in owned if i not in set(bench)]
    real = round(sum(xp[i] for i in plan["start"]) - sum(xp[i] for i in declared_xi), 1)
    fiction = dict(xp)
    fiction[best] = 0.0
    fictional = round(sum(fiction[i] for i in plan["start"]) - sum(fiction[i] for i in declared_xi), 1)

    assert plan["gain"] == real
    assert real != fictional, (
        "this squad cannot tell the two apart — the leaver is not in the declared XI, so the test proves "
        "nothing and needs a different fixture"
    )
