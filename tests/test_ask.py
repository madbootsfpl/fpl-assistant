"""Tests for the `ask` command's brain (ADR-034).

All offline — no live LLM. The narrator is injected (a fake, or one returning None to
exercise the graceful-degradation path). Covers routing, fact-humanising, the prompt
contract, and assembling a result (narrated vs degraded vs unrecognised).
"""

from src import ask
from src.ask import (
    AskResult,
    _analyse_facts,
    _build_prompt,
    _captain_facts,
    _plan_facts,
    _transfer_count,
    _transfer_facts,
    assemble,
    route,
)

# ---- routing ----------------------------------------------------------------

def test_routes_captain_and_extracts_squad():
    assert route("who should I captain from TS?", known_squads=["TS"]) == ("captain", "TS")


def test_routes_transfer_and_analyse():
    assert route("what transfer should I make", known_squads=[])[0] == "transfer"
    assert route("analyse my squad", known_squads=[])[0] == "analyse"
    assert route("how good is my squad", known_squads=[])[0] == "analyse"


def test_squad_matched_by_name_regardless_of_phrasing():
    assert route("what transfer for TS?", known_squads=["TS"])[1] == "TS"     # "for"
    assert route("captain from TS", known_squads=["TS"])[1] == "TS"           # "from"
    # a stray word isn't mistaken for a squad → captain stays global
    assert route("who should I captain for the next gameweek", known_squads=["TS"])[1] is None


def test_unrecognised_question_has_no_intent():
    assert route("what is the meaning of life", known_squads=[]) == (None, None)


# ---- humanising (self-describing facts — nothing to decode) ------------------

def test_captain_facts_humanise_venue_and_keep_codes():
    pick = {"web_name": "B.Fernandes", "team": "MUN", "xp": 7.4,
            "opponent": "HUL", "venue": "A", "penalty_taker": True}
    facts = _captain_facts(pick)
    assert facts["fixture"] == "away against HUL"      # "A" → "away against", code kept
    assert facts["player"] == "B.Fernandes (MUN)"
    assert facts["expected_points_next_gameweek"] == 7.4
    assert facts["is_penalty_taker"] is True


def test_home_venue_humanises_to_home():
    pick = {"web_name": "Saka", "team": "ARS", "xp": 7.2,
            "opponent": "COV", "venue": "H", "penalty_taker": True}
    assert _captain_facts(pick)["fixture"] == "home against COV"


# ---- prompt contract --------------------------------------------------------

def test_prompt_carries_the_facts_and_the_rules():
    decision = {"task": "explain why X is a good pick", "facts": {"player": "X (AAA)"}}
    prompt = _build_prompt(decision)
    assert "X (AAA)" in prompt                          # the facts are in the prompt
    assert "do NOT rank" in prompt and "invent" in prompt   # the grounding rules are stated


# ---- assemble: narrated / degraded / unrecognised ---------------------------

_DECISION = {"headline": "Captain pick: X — xP 7.4 next GW",
             "facts": {"player": "X (AAA)"}, "task": "explain why X"}


def test_assemble_narrates_when_the_model_answers():
    r = assemble("q", "captain", _DECISION, narrator=lambda p: "X is a great pick.")
    assert r.explanation == "X is a great pick."
    assert r.headline == _DECISION["headline"]


def test_assemble_degrades_when_the_model_is_unavailable():
    # narrator returns None (Ollama absent) → keep the decision + facts, no prose, no crash
    r = assemble("q", "captain", _DECISION, narrator=lambda p: None)
    assert r.explanation is None
    assert r.headline == _DECISION["headline"] and r.facts == _DECISION["facts"]


def test_assemble_carries_a_structured_detail():
    # a plan decision has a pre-rendered `detail` table instead of a one-line headline (ADR-036)
    decision = {"detail": "THE PLAN TABLE", "facts": {"x": 1}, "task": "summarise"}
    r = assemble("q", "transfer", decision, narrator=lambda p: "the prose")
    assert r.detail == "THE PLAN TABLE" and r.headline is None
    assert r.explanation == "the prose"


def test_render_ask_shows_detail_then_prose():
    from src.ui.ask import render_ask
    r = AskResult("q", "transfer", detail="THE PLAN TABLE", facts={}, explanation="the prose")
    out = render_ask(r)
    assert out.index("THE PLAN TABLE") < out.index("the prose")   # table first, then narration


def test_assemble_handles_no_decision():
    r = assemble("q", "captain", None, narrator=lambda p: "unused")
    assert r.headline is None and r.message and "refresh" in r.message


def test_assemble_unrecognised_intent_is_a_help_message():
    r = assemble("q", None, None, narrator=lambda p: "unused")
    assert isinstance(r, AskResult)
    assert r.intent is None and "captaincy" in r.message


# ---- transfer / analyse humanisers (US-097) ---------------------------------

def test_transfer_facts_humanise_a_move():
    m = {"out": {"web_name": "A", "team": "AAA", "xp": 19.6},
         "in": {"web_name": "B", "team": "BBB", "xp": 35.0}, "gain": 15.4}
    f = _transfer_facts(m)
    assert f["sell"] == "A (AAA, xP 19.6)" and f["buy"] == "B (BBB, xP 35.0)"
    assert f["expected_points_gain_over_5_gameweeks"] == 15.4


def test_analyse_facts_availability_reads_none_when_no_issues():
    a = {"projected_xp": 278.1, "issues": [], "weakest": [{"web_name": "X", "xp": 19.4}]}
    f = _analyse_facts(a)
    assert f["availability_problems"] == "none"        # self-describing → no false injury implied
    assert f["weakest_starters"] == ["X (xP 19.4)"]


def test_analyse_facts_lists_availability_problems():
    a = {"projected_xp": 200, "issues": [{"web_name": "Inj"}], "weakest": []}
    assert _analyse_facts(a)["availability_problems"] == "1: Inj"


def test_transfer_count_parsed_from_the_question():
    assert _transfer_count("which 3 transfers for TS?") == 3
    assert _transfer_count("what transfer should I make for TS") == 1   # no number → 1
    assert _transfer_count("plan 2 transfers") == 2
    assert _transfer_count("who should I captain for the next 5 gameweeks") == 1  # 5 not a count


def test_plan_facts_are_self_describing():
    plan = [
        {"out": {"web_name": "A"}, "in": {"web_name": "B"}, "gain": 15.4},
        {"out": {"web_name": "C"}, "in": {"web_name": "D"}, "gain": 9.9},
    ]
    f = _plan_facts(plan)
    assert f["transfers"] == ["sell A, buy B (+15.4 xP)", "sell C, buy D (+9.9 xP)"]
    assert f["total_expected_points_gain_over_5_gameweeks"] == 25.3


def test_transfer_and_analyse_ask_for_a_squad_when_missing():
    # these intents need a saved squad; no squad in the question → a helpful message (no store touched)
    r = ask.answer("what transfer should I make", narrator=lambda p: "unused")
    assert r.intent == "transfer" and "squad" in r.message.lower()
    r2 = ask.answer("analyse my chances", narrator=lambda p: "unused")
    assert r2.intent == "analyse" and "squad" in r2.message.lower()
