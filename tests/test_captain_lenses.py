"""One captaincy engine, one intent (ADR-308).

⚠️⚠️⚠️ **Five different questions used to get the same answer.** Measured in ADR-307 against the owner's
own list: *"who should be my **vice**-captain?"*, *"who is the **safest** captain?"*, *"who is the best
**differential** captain?"* and *"is my captain at **rotation risk**?"* all returned the top pick, with an
authoritative headline, because the router matched `captain` and dropped the word that made the question
specific.

⭐ `src/ask.py` already carried the principle in its own routing table — a bare *"strategy"* is left
unroutable on purpose, because guessing *"would trade an honest miss for a confident wrong answer — the
one failure the routing corpus measured as actually harmful."*
"""

from __future__ import annotations

import pytest

from src import ask as ask_engine
from src.service import AskRequest, ask_question
from src.storage import Storage


@pytest.fixture(scope="module")
def store():
    s = Storage()
    yield s
    s.close()


@pytest.fixture(scope="module")
def squad(store):
    """A legal fifteen from the fixture — enough players for a lens to have a choice."""
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in sorted(store.get_players(), key=lambda r: -(r["price"] or 0)):
        if need.get(p["position"]) and per_club.get(p["team"], 0) < 3:
            picked.append(p["id"])
            need[p["position"]] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return picked


def ask(question: str, squad, store) -> dict:
    return ask_question(
        AskRequest(question=question, player_ids=squad, bench_ids=squad[-4:]), store=store
    )


# ── the routing ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("question", "lens"),
    [
        ("Who should I captain this gameweek?", None),
        ("Who should be my vice-captain?", "vice"),
        ("Who is my vice captain?", "vice"),
        ("Who is the safest captain?", "safest"),
        ("Who is the most reliable captain?", "safest"),
        ("Who is the best differential captain?", "differential"),
        ("Give me a captaincy punt", "differential"),
        ("Is my captain at rotation risk?", "rotation"),
    ],
)
def test_the_qualifier_is_heard(question, lens):
    assert ask_engine.captain_lens(question) == lens


def test_vice_is_not_read_as_captain():
    """⭐ The longest phrase wins, so *"vice-captain"* can never be matched as *"captain"* — ⚠️ *the
    substring that breaks this is inside every one of these questions.*"""
    assert ask_engine.captain_lens("who should be my vice-captain?") == "vice"


# ── the answers ──────────────────────────────────────────────────────────────

def test_five_questions_get_five_headings(squad, store):
    """⚠️⚠️ **The defect, stated as a test.** Before ADR-308 every one of these returned the same
    headline — ⭐ *a failure that was invisible precisely because the answers looked identical.*

    ⚠️ This checks the **heading**, which changes per lens whether or not the pick does; that is why it
    survived eleven mutants that broke the picking. The picks themselves are tested on constructed inputs
    further down, where the safe player and the high-scoring player are deliberately different people.
    """
    headlines = {
        q: ask(q, squad, store)["headline"]
        for q in (
            "Who should I captain?",
            "Who should be my vice-captain?",
            "Who is the safest captain?",
            "Who is the best differential captain?",
        )
    }

    assert len(set(headlines.values())) == 4, (
        "two of these questions still share an answer:\n  " + "\n  ".join(headlines.values())
    )


def test_the_headline_names_the_question_it_answered(squad, store):
    """⭐ *A heading that repeats the question is a heading that proves it was heard* — and it is the only
    part a reader checks before trusting the rest."""
    assert ask("Who should be my vice-captain?", squad, store)["headline"].startswith("Vice-captain")
    assert ask("Who is the safest captain?", squad, store)["headline"].startswith("Safest captain")
    assert ask("Who is the best differential captain?", squad, store)["headline"].startswith(
        "Differential captain"
    )


def test_the_vice_is_the_second_pick_not_the_first(squad, store):
    best = ask("Who should I captain?", squad, store)["facts"]["player"]
    vice = ask("Who should be my vice-captain?", squad, store)["facts"]["player"]

    assert vice != best, "the vice-captain is the captain"


def test_the_differential_is_less_owned_than_the_captain(squad, store):
    """⭐ *A differential is a bet on other people not having him*, so ownership is the criterion."""
    players = {p["id"]: p for p in Storage().get_players()}
    best = ask("Who should I captain?", squad, store)["facts"]["player"]
    diff = ask("Who is the best differential captain?", squad, store)["facts"]["player"]

    owned = {f"{p['web_name']} ({p['team']})": p["selected_by"] for p in players.values()}
    assert owned.get(diff) is not None and owned.get(best) is not None
    assert owned[diff] <= owned[best], (
        f"the 'differential' ({diff}, {owned[diff]}%) is more owned than the captain "
        f"({best}, {owned[best]}%)"
    )


def test_a_minutes_question_is_answered_with_minutes(squad, store):
    """⚠️⚠️ **Naming the lens and returning the same four facts would be the same failure in nicer
    clothing** — the reader asked whether his captain might be rested and would still be reading expected
    points."""
    facts = ask("Is my captain at rotation risk?", squad, store)["facts"]

    assert "expected_minutes_share" in facts
    assert "is_flagged_doubtful" in facts
    # ⭐ A sentence, not a coefficient: *0.82 is a number the model produced, not one a person can act on.*
    assert "%" in facts["expected_minutes_share"]
    assert "full game" in facts["expected_minutes_share"]


# ── two named players ────────────────────────────────────────────────────────

def test_two_named_players_are_compared_with_each_other(squad, store):
    """⚠️ *"Is A a better captain than B?"* is a question about two men, and answering it with whoever the
    engine ranked first is the most confident way to ignore somebody.

    ⚠️⚠️ The two names come from **the engine's own shortlist**, not from the squad's price order. ⭐ *A test
    that picks its subjects by a property the code under test does not use is a test that passes on one
    dataset* — this asked about the two most expensive players, who are ranked in the live cache and are not
    in the committed seed, so it took the "neither is ranked" path in CI and nowhere else.
    """
    names = [ask(q, squad, store)["facts"]["player"].split(" (")[0]
             for q in ("Who should I captain?", "Who should be my vice-captain?")]
    assert names[0] != names[1]

    out = ask(f"Is {names[0]} a better captain than {names[1]}?", squad, store)

    assert out["headline"].startswith("Better captain"), out["headline"]
    for name in names:
        assert name in out["detail"], f"{name} was not mentioned in the comparison"


def test_a_name_that_cannot_be_placed_is_said_out_loud(squad, store):
    """⚠️⚠️⚠️ **The failure this ADR exists to stop, reintroduced one function along.** A comparison
    naming someone unresolvable resolves one name, falls through, and answers *"Captain pick: X"* — a
    correct sentence and a dishonest answer.

    ⭐⭐ **And it still answers**, because the owner's rule is that Ask does not send you elsewhere: the
    pick and the caveat arrive in one reply.
    """
    store_players = {p["id"]: p for p in Storage().get_players()}
    known = store_players[squad[0]]["web_name"]

    out = ask(f"Is Zlatan Ibrahimovic a better captain than {known}?", squad, store)

    assert "could not place" in out["headline"], out["headline"]
    # ⭐ The answer it *can* stand behind is still there.
    assert out["facts"]["player"], "the caveat replaced the answer instead of joining it"


def test_an_ordinary_question_gains_no_caveat(squad, store):
    """⭐ The counterpart. ⚠️ *A caveat on every answer is a caveat nobody reads*, and it would make the
    honest one invisible."""
    out = ask("Who should I captain?", squad, store)

    assert "could not place" not in out["headline"]
    assert out["headline"].startswith("Captain pick")


# ── the lens itself, on constructed inputs ───────────────────────────────────
#
# ⚠️⚠️⚠️ **Every test above passed against eleven mutants that broke the engine.** Mutation testing found
# them all in one place: *"safest" ranked by expected points*, *"safest" picked the **least** safe*, *every
# player "starts"*, *the flag went unmentioned*, *the comparison picked the **lower** xP* — all eleven
# survived the end-to-end tests.
#
# ⭐⭐⭐ **A fixture gap, not a missing assertion.** In the committed fixture the highest-xP player is also
# the highest-minutes player, nobody is flagged, and ownership never ties — so *a lens that ignores its own
# criterion returns the same man as the lens that honours it*, and no assertion about the answer can see
# the difference. ⭐ The headline distinctness test was the worst of them: it compares *headings*, which
# differ by lens whether or not the pick does.
#
# ⭐⭐ So the decision functions are tested on **inputs built to discriminate**, where the safe pick and the
# high-scoring pick are deliberately different people.

def pick(pid, name, xp, minutes=1.0, doubtful=False, team="AAA"):
    """A captain pick with the fields the engine reads — ⭐ *the shape, not a stub of it.*"""
    return {"id": pid, "web_name": name, "xp": xp, "minutes_weight": minutes,
            "doubtful": doubtful, "team": team, "venue": "H", "opponent": "ZZZ",
            "penalty_taker": False}


#: ⭐ The shortlist that separates the lenses: the best scorer is a rotation risk, the safe man scores
#: less, and the differential is neither.
SHORTLIST = [
    pick(1, "Star", xp=9.0, minutes=0.55),      # best xP, rotated
    pick(2, "Nailed", xp=6.0, minutes=1.0),     # safest
    pick(3, "Flagged", xp=8.0, minutes=0.95, doubtful=True),
    pick(4, "Quiet", xp=4.0, minutes=0.9),      # the differential
]
OWNERSHIP = {1: 60.0, 2: 45.0, 3: 30.0, 4: 2.0}


def test_safest_is_the_most_likely_to_play_not_the_highest_scoring():
    """⚠️⚠️ *A captain who does not play is the only captaincy outcome that cannot be recovered from*,
    which is what the reader means by "safe" — ⭐ so minutes are the criterion and xP only breaks ties."""
    index, note = ask_engine._lens_pick(SHORTLIST, "safest", {})

    assert SHORTLIST[index]["web_name"] == "Nailed", (
        f"'safest' chose {SHORTLIST[index]['web_name']} — xP {SHORTLIST[index]['xp']}, "
        f"{SHORTLIST[index]['minutes_weight']} minutes"
    )
    assert note is None


def test_safest_prefers_an_unflagged_player_over_a_flagged_one():
    """⚠️ Flagged-at-95% would otherwise outrank nailed-at-100%'s nearest rival — ⭐ *a flag is a
    different kind of risk from rotation and must not be averaged into one.*"""
    index, _ = ask_engine._lens_pick([SHORTLIST[2], SHORTLIST[1]], "safest", {})

    assert [SHORTLIST[2], SHORTLIST[1]][index]["web_name"] == "Nailed"


def test_the_differential_is_the_least_owned():
    index, note = ask_engine._lens_pick(SHORTLIST, "differential", OWNERSHIP)

    assert SHORTLIST[index]["web_name"] == "Quiet"
    assert note is None


def test_tied_ownership_is_broken_by_points():
    """⭐ *Ownership is the criterion and points decide between equals* — with the comparison the wrong way
    round, the reader is handed the weaker of two equally-hidden punts."""
    tied = [pick(1, "Low", xp=3.0), pick(2, "High", xp=7.0)]

    index, _ = ask_engine._lens_pick(tied, "differential", {1: 5.0, 2: 5.0})

    assert tied[index]["web_name"] == "High"


def test_without_ownership_the_differential_says_so(squad, store):
    """⚠️⚠️ **The lens that cannot be honoured.** ⭐ It returns the pick it *can* stand behind **and** the
    reason — never silently, and never by sending the reader elsewhere."""
    index, note = ask_engine._lens_pick(SHORTLIST, "differential", {})

    assert index == 0
    assert note and "ownership" in note


def test_a_one_man_shortlist_cannot_have_a_vice():
    """⭐ Nothing to separate, so it says that rather than returning the captain twice under a new name."""
    index, note = ask_engine._lens_pick([SHORTLIST[0]], "vice", {})

    assert index == 0
    assert note and "vice" in note


def test_rotation_keeps_the_same_man():
    """⚠️ *"Is my captain at rotation risk?"* asks about **the** captain — answering with a different,
    safer player answers a question nobody asked."""
    index, note = ask_engine._lens_pick(SHORTLIST, "rotation", {})

    assert index == 0 and note is None


# ── the minutes sentence ─────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("weight", "doubtful", "expected"),
    [
        (1.0, False, "he starts"),
        (0.95, False, "he starts"),
        (0.8, False, "usually starts"),
        (0.5, False, "rotated"),
        (0.9, True, "flagged"),
    ],
)
def test_the_minutes_bands_read_differently(weight, doubtful, expected):
    """⚠️ Every band containing the words "full game" is why *"everyone starts"* survived the first
    mutation pass — ⭐ *the assertion has to test the part that differs.*"""
    phrase = ask_engine._minutes_phrase(pick(1, "X", xp=5.0, minutes=weight, doubtful=doubtful))

    assert expected in phrase
    assert f"{round(weight * 100)}%" in phrase


def test_unknown_minutes_are_not_guessed():
    assert ask_engine._minutes_phrase({"minutes_weight": None}) == "not known"


# ── the two-player comparison ────────────────────────────────────────────────

def test_the_better_captain_of_the_two_is_the_higher_scoring_one():
    out = ask_engine._captain_versus(SHORTLIST, [SHORTLIST[1], SHORTLIST[0]], SHORTLIST, "squad", {})

    assert "Star" in out["headline"], out["headline"]
    assert out["facts"]["player"].startswith("Star")


def test_a_player_outside_the_shortlist_is_told_he_is_outside_it():
    """⚠️⚠️ **A player the engine did not rank is a player it does not think you should captain**, and
    that is the answer — ⭐ *not grounds for silently substituting somebody who is ranked.*"""
    outsider = pick(99, "Outsider", xp=1.0)

    out = ask_engine._captain_versus(SHORTLIST, [outsider, SHORTLIST[1]], SHORTLIST, "squad", {})

    assert "Outsider" in out["detail"]
    assert "not among the captain options" in out["detail"]
    assert "Nailed" in out["headline"]


def test_when_neither_is_ranked_it_still_answers():
    """⭐⭐ The owner's rule, at its hardest case: *"if they use Ask they will want the answer from there
    and not to be directed somewhere else to find it."* ⚠️ Both names unrankable is exactly where an
    engine is most tempted to return nothing."""
    a, b = pick(98, "One", xp=1.0), pick(99, "Two", xp=1.0)

    out = ask_engine._captain_versus(SHORTLIST, [a, b], SHORTLIST, "squad", {})

    assert "Neither" in out["headline"]
    assert "Star" in out["headline"], "the fallback dropped the answer it could give"
    assert out["facts"]["player"]


# ── the three the constructed inputs could not reach ─────────────────────────

def test_a_flag_outranks_a_better_minutes_share():
    """⚠️⚠️ The flag has to be the **first** term, not a tiebreak. ⭐ *A player FPL has flagged at 100%
    minutes is a worse bet than an unflagged player at 90%* — the flag is news about this week, the share
    is a description of last month.

    ⚠️ The earlier version of this test could not see the difference: it flagged the man who *also* had
    fewer minutes, so ignoring the flag changed nothing.
    """
    flagged_but_nailed = pick(1, "Flagged", xp=9.0, minutes=1.0, doubtful=True)
    merely_good = pick(2, "Clear", xp=5.0, minutes=0.9)

    order = [flagged_but_nailed, merely_good]
    index, _ = ask_engine._lens_pick(order, "safest", {})

    assert order[index]["web_name"] == "Clear", (
        "'safest' chose the flagged player because he plays more minutes"
    )


def test_a_lens_sees_the_whole_shortlist_not_the_top_three(squad, store):
    """⚠️⚠️⚠️ **A filter applied to a truncated list is a filter that answers about the truncation.** The
    plain captain question needs three picks; a lens routinely answers with someone outside them.

    ⭐ Measured: truncated to three, *"who is the best differential captain?"* returns a **13.5%-owned**
    player and calls him a differential. Given the whole shortlist it returns one owned by **0.4%**.
    """
    players = {p["id"]: p for p in Storage().get_players()}
    name = ask(
        "Who is the best differential captain?", squad, store
    )["facts"]["player"].split(" (")[0]

    owned = next(p["selected_by"] for p in players.values() if p["web_name"] == name)
    assert owned < 5.0, (
        f"the 'differential' is {name}, owned by {owned}% — the lens is choosing from a truncated list"
    )


def test_a_named_player_outside_the_squad_still_resolves(squad, store):
    """⚠️⚠️ **Names resolve against the whole market, never against the squad.** This is the bug this ADR
    reintroduced one function along: *"is X a better captain than Y?"* with X unowned resolved **one**
    name, fell through, and answered *"Captain pick: Y"* — ⭐ *silently dropping the player the question
    was about.*
    """
    store_players = Storage().get_players()
    mine = {p["id"]: p for p in store_players if p["id"] in squad}
    owned_name = mine[squad[0]]["web_name"]
    outsider = next(
        p["web_name"] for p in store_players
        if p["id"] not in squad and (p["minutes"] or 0) > 300
    )

    out = ask(f"Is {outsider} a better captain than {owned_name}?", squad, store)

    assert outsider in out["detail"], (
        f"{outsider} is in the game but outside the squad, and the answer never mentions him"
    )
    assert "not among the captain options" in out["detail"]


# ── the contract every decision owes its consumer ────────────────────────────
#
# ⚠️⚠️⚠️ **This is the bug the mutation pass could not see, and CI caught.** `_captain_versus`'s
# "neither is ranked" branch returned `facts` **without** `task`, and `_build_prompt` reads
# `decision['task']` with a hard subscript — so the branch was a **`KeyError`, a 500 on the live API**,
# not a missing sentence.
#
# ⭐⭐⭐ **And the narrator being silenced does not save it**, which is the part worth remembering:
# `assemble` calls `narrator(_build_prompt(decision))`, so the prompt is built as the **argument**, before
# the call that throws it away. ⭐ *A field only the optional half consumes still has to be there, because
# the call that discards it is made after the one that builds it.*
#
# ⚠️⚠️ **Why the tests above missed it:** `test_when_neither_is_ranked_it_still_answers` calls
# `_captain_versus` **directly** and asserts on its dict — ⭐ *a unit test of a producer cannot see a
# contract its consumer imposes.* It only surfaced against the committed seed, where the two named players
# fall outside the shortlist; the richer local cache put them inside it and took the branch never.


def prompts_built(decision, question="q", intent="captain"):
    """Drive a decision through the real consumer, capturing what the narrator was handed."""
    seen = []

    def narrator(prompt, *a, **k):
        seen.append(prompt)
        return None          # ⭐ exactly the deployed case — silenced, but the prompt is still built

    ask_engine.assemble(question, intent, decision, narrator)
    return seen


def test_the_unranked_pair_survives_being_narrated():
    a, b = pick(98, "One", xp=1.0), pick(99, "Two", xp=1.0)
    decision = ask_engine._captain_versus(SHORTLIST, [a, b], SHORTLIST, "squad", {})

    seen = prompts_built(decision)      # ⚠️ this raised KeyError('task') before the fix

    assert seen and "Star" in seen[0]


@pytest.mark.parametrize("lens", [None, "vice", "safest", "differential", "rotation"])
def test_every_lens_owes_its_consumer_a_task(lens, squad, store):
    """⭐ The invariant stated once, over every path a captain question can take: **a decision carrying
    `facts` carries a `task`.**"""
    question = {None: "Who should I captain?", "vice": "Who should be my vice-captain?",
                "safest": "Who is the safest captain?",
                "differential": "Who is the best differential captain?",
                "rotation": "Is my captain at rotation risk?"}[lens]

    decision = ask_engine._decide_captain(
        store, "yours", lens=ask_engine.captain_lens(question), question=question,
        active_squad={"name": "yours", "player_ids": list(squad), "bench_ids": list(squad[-4:])},
    )

    assert decision is not None
    if "facts" in decision:
        assert decision.get("task"), f"{lens or 'plain'} returns facts with no task — a 500 when narrated"
        assert prompts_built(decision)


def test_both_named_shapes_owe_a_task_too():
    """⚠️ Both `_captain_versus` exits, since only one of them had it."""
    ranked = ask_engine._captain_versus(SHORTLIST, [SHORTLIST[1], SHORTLIST[0]], SHORTLIST, "squad", {})
    neither = ask_engine._captain_versus(
        SHORTLIST, [pick(98, "One", xp=1.0), pick(99, "Two", xp=1.0)], SHORTLIST, "squad", {})

    for name, decision in (("ranked pair", ranked), ("neither ranked", neither)):
        assert decision.get("task"), f"{name} returns facts with no task"
        assert prompts_built(decision), name
