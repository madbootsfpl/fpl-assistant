"""Tests for the `ask` command's brain (ADR-034).

All offline — no live LLM. The narrator is injected (a fake, or one returning None to
exercise the graceful-degradation path). Covers routing, fact-humanising, the prompt
contract, and assembling a result (narrated vs degraded vs unrecognised).
"""

import types

from src import ask
from src.analytics import WEEKLY_BENCH_WEIGHT
from src.ask import (
    AskResult,
    Context,
    FollowUp,
    _analyse_facts,
    _apply_followup,
    _archetype_counts,
    _bench_mode,
    _build_prompt,
    _captain_facts,
    _decide_compare,
    _decide_shortlist,
    _lineup_change,
    _match_players,
    _plan_facts,
    _shortlist_query,
    _squad_budget,
    _swap_position,
    _transfer_count,
    _transfer_facts,
    assemble,
    converse,
    detect_followup,
    route,
    verify_grounding,
)
from src.ui.compare import render_compare
from src.ui.shortlist import render_shortlist
from src.ui.startbench import render_start_bench

# ---- routing ----------------------------------------------------------------

def test_routes_captain_and_extracts_squad():
    assert route("who should I captain from TS?", known_squads=["TS"]) == ("captain", "TS")


def test_routes_transfer_and_analyse():
    assert route("what transfer should I make", known_squads=[])[0] == "transfer"
    assert route("analyse my squad", known_squads=[])[0] == "analyse"
    assert route("how good is my squad", known_squads=[])[0] == "analyse"


def test_routes_start_bench():
    assert route("who should I start from TS?", known_squads=["TS"]) == ("start_bench", "TS")
    assert route("fix my bench", known_squads=[])[0] == "start_bench"
    assert route("what's my best lineup?", known_squads=[])[0] == "start_bench"


def test_lineup_change_reports_no_saved_bench():
    assert "no saved bench" in _lineup_change([], [], has_declared_bench=False)


def test_lineup_change_reports_already_optimal():
    assert "already the best legal XI" in _lineup_change([], [], has_declared_bench=True)


def test_lineup_change_names_the_swap():
    msg = _lineup_change(
        [{"web_name": "Haaland"}], [{"web_name": "Diop"}], has_declared_bench=True,
    )
    assert msg == "Change: start Haaland — bench Diop."


def test_start_bench_asks_for_a_squad_when_missing():
    r = ask.answer("who should I start", narrator=lambda p: "unused")
    assert r.intent == "start_bench" and "squad" in r.message.lower()


def test_render_start_bench_shows_xi_bench_and_change():
    def _row(name, pos, xp, w):
        return {"web_name": name, "team": "ARS", "position": pos, "price": 5.0,
                "xp": xp, "status": "a", "chance": None, "minutes_weight": w}
    out = render_start_bench(
        [_row("Haaland", "FWD", 29.0, 0.82)], [_row("Diop", "DEF", 4.1, 0.32)],
        "Change: none — your current XI is already the best legal XI.", "TS", 208.9,
    )
    assert "Start (XI):" in out and "Bench:" in out
    assert "Haaland" in out and "Diop" in out
    assert " 74" in out                       # 0.82 × 90 → 74 expected minutes (the xMins column)
    assert "already the best legal XI" in out


# ---- compare intent (US-114) ------------------------------------------------

def _pl(pid, web_name, team="ARS"):
    return {"id": pid, "web_name": web_name, "team": team, "position": "MID",
            "team_id": 1, "status": "a", "chance": None, "penalties_order": None}


def test_routes_compare():
    assert route("Haaland or B.Fernandes?", known_squads=[])[0] == "compare"
    assert route("compare Saka and Palmer", known_squads=[])[0] == "compare"
    # a captain question keeps priority even with 'or' in it (compare is checked last)
    assert route("who should I captain, this week or next", known_squads=[])[0] == "captain"


def test_match_players_drops_a_name_that_is_a_substring_of_another():
    players = [_pl(1, "Haaland"), _pl(2, "B.Fernandes"), _pl(3, "Fernandes")]
    matched = _match_players("Haaland or B.Fernandes?", players)
    assert list(matched.keys()) == ["Haaland", "B.Fernandes"]   # 'Fernandes' dropped, order kept


def test_match_players_flags_an_ambiguous_name():
    players = [_pl(1, "Palmer", "CHE"), _pl(2, "Palmer", "AVL")]
    matched = _match_players("compare Palmer", players)
    assert len(matched["Palmer"]) == 2       # same web_name, two players → ambiguous


def test_match_players_is_bounded_to_whole_names():
    players = [_pl(1, "Isak")]
    assert _match_players("this is a mistaken sentence", players) == {}   # no match inside a word


def test_compare_message_when_fewer_than_two_players():
    store = types.SimpleNamespace(get_players=lambda: [_pl(1, "Haaland")])
    d = _decide_compare(store, "Haaland or Salah?")
    assert "two players" in d["message"] and "Haaland" in d["message"]


def test_compare_message_when_ambiguous():
    store = types.SimpleNamespace(
        get_players=lambda: [_pl(1, "Palmer", "CHE"), _pl(2, "Palmer", "AVL")]
    )
    d = _decide_compare(store, "compare Palmer")
    assert "More than one player called 'Palmer'" in d["message"]


def test_compare_message_short_circuits_in_assemble():
    r = assemble("q", "compare", {"message": "Name two players."}, narrator=lambda p: "unused")
    assert r.message == "Name two players." and r.explanation is None


def test_render_compare_orders_by_xp_and_shows_columns():
    def _row(name, xp, w):
        return {"web_name": name, "team": "MCI", "position": "FWD", "xp": xp,
                "status": "a", "chance": None, "minutes_weight": w,
                "opponent": "BOU", "venue": "H", "penalty_taker": True}
    out = render_compare([_row("Haaland", 29.0, 0.82), _row("B.Fernandes", 27.3, 0.89)])
    assert out.index("Haaland") < out.index("B.Fernandes")   # strongest xP first
    assert "xMins" in out and "29.0" in out


# ---- build_squad intent (US-120) --------------------------------------------

def test_routes_build_squad():
    assert route("build me a squad for £100m", known_squads=[])[0] == "build_squad"
    assert route("what's the best squad for £90m?", known_squads=[])[0] == "build_squad"
    # 'start'/'bench' still win where they apply (build is checked after them)
    assert route("who should I start from TS", known_squads=["TS"])[0] == "start_bench"


def test_squad_budget_parses_the_amount_or_defaults():
    assert _squad_budget("build me a squad for £100m") == 100.0
    assert _squad_budget("build a team for 85m") == 85.0
    assert _squad_budget("build me a squad") == 100.0        # FULL_BUDGET default


def test_archetype_counts_parses_low_cost_premium_and_differential():
    # ADR-043: (low_cost, premium, differential) counts from a build request.
    assert _archetype_counts(
        "build me a squad for £100M with 3 low cost players and 1 premium player") == (3, 1, None)
    assert _archetype_counts("build a squad with 2 premium and 4 budget players") == (4, 2, None)
    assert _archetype_counts("build a team with 2 differentials") == (None, None, 2)
    assert _archetype_counts("build me a squad for £100m") == (None, None, None)


def test_routes_multifaceted_build_to_build_squad():
    q = "build me a squad for £100m with 3 low cost players and 1 premium player"
    assert route(q, known_squads=[])[0] == "build_squad"    # 'build' wins over 'players'/'premium'


def test_bench_mode_parses_boost_and_rotation():
    # ADR-045: "bench boost" → the max-15; "rotation"/"weekly" → a bench-aware XI; else default.
    assert _bench_mode("build me a squad for a bench boost") == (None, True)
    assert _bench_mode("build a team for rotation") == (WEEKLY_BENCH_WEIGHT, False)
    assert _bench_mode("build me a squad for £100m") == (None, False)


def test_bench_boost_build_routes_to_build_squad_not_start_bench():
    # 'build' must win over 'bench' — else a bench-boost build hits the start/bench intent.
    assert route("build me a squad for a bench boost", known_squads=[])[0] == "build_squad"


def test_verify_grounding_handles_a_pound_sign_in_the_facts():
    # ADR-037 bug found via build_squad: a '£' fact must not corrupt the number set (its JSON
    # escape used to inject stray digits, wrongly flagging a grounded figure like £100.0m).
    facts = {"budget": "£100.0m", "squad_cost": "£100.0m"}
    trust = verify_grounding("The squad costs £100.0m of the £100.0m budget.", facts)
    assert trust["numbers"] == []


# ---- shortlist intent (US-123) ----------------------------------------------

def test_routes_shortlist_after_build_squad():
    assert route("best midfielders under £8m", known_squads=[])[0] == "shortlist"
    assert route("best value goalkeepers", known_squads=[])[0] == "shortlist"
    assert route("best squad for £100m", known_squads=[])[0] == "build_squad"   # build still wins


def test_routes_differentials_to_shortlist_not_trends():
    # ADR-061: "best differentials" is a shortlist (ownership filter), not a trends board ("most owned")
    assert route("best differentials", known_squads=[])[0] == "shortlist"
    assert route("best differential forwards under £7m", known_squads=[])[0] == "shortlist"
    assert route("most owned players", known_squads=[])[0] == "trends"          # trends still owns this


def test_shortlist_query_parses_position_price_and_value():
    assert _shortlist_query("best midfielders under £8m") == ("MID", 8.0, False, False)
    assert _shortlist_query("best value goalkeepers") == ("GK", None, True, False)
    assert _shortlist_query("best forwards") == ("FWD", None, False, False)
    assert _shortlist_query("best players") == (None, None, False, False)   # no position → all


def test_shortlist_query_parses_the_differential_cue():
    # ADR-061: "differential(s)" / off-template / low-owned → the ownership lens
    assert _shortlist_query("best differential forwards under £7m") == ("FWD", 7.0, False, True)
    assert _shortlist_query("best differentials") == (None, None, False, True)
    assert _shortlist_query("best low-owned midfielders") == ("MID", None, False, True)
    assert _shortlist_query("best midfielders") == ("MID", None, False, False)  # not differential


def test_shortlist_differential_filters_by_ownership():
    # two MIDs, one template (30%) one differential (3%); the differential query keeps only the latter
    store = types.SimpleNamespace(
        get_players=lambda: [
            {"id": 1, "web_name": "Template", "position": "MID", "price": 8.0, "status": "a",
             "team": "X", "team_id": 1, "points_per_game": 5.0, "ep_next": 4.0,
             "selected_by": 30.0, "code": 1},
            {"id": 2, "web_name": "Diff", "position": "MID", "price": 6.0, "status": "a",
             "team": "Y", "team_id": 2, "points_per_game": 4.0, "ep_next": 3.0,
             "selected_by": 3.0, "code": 2},
        ],
        get_upcoming_fixtures=lambda: [],
        get_history_by_code=lambda: {},
        get_gw_history_by_code=lambda: {},
    )
    d = _decide_shortlist(store, "best differential midfielders")
    assert d["subjects"] == ["Diff"]                       # the template is filtered out
    assert "≤5% owned" in d["detail"]                      # the caption + Own% column
    assert "3.0" in d["detail"]                            # Diff's ownership shown


def test_shortlist_message_when_nothing_matches_the_filter():
    # Only a MID exists; "best goalkeepers" filters to none → a clear message (no fixtures needed,
    # since the filter runs before the xP calc).
    store = types.SimpleNamespace(
        get_players=lambda: [{"id": 1, "web_name": "P1", "position": "MID", "price": 5.0,
                              "status": "a", "team": "X"}]
    )
    d = _decide_shortlist(store, "best goalkeepers")
    assert "No available GK players" in d["message"]


def test_render_shortlist_ranks_and_shows_price_and_xp():
    def _row(name, price, xp, w):
        return {"web_name": name, "team": "MUN", "position": "MID", "price": price,
                "status": "a", "chance": None, "xp": xp, "minutes_weight": w}
    out = render_shortlist([_row("Mbeumo", 8.0, 23.3, 0.81), _row("Rice", 7.5, 20.9, 0.88)],
                           "Best MID ≤£8.0m — by expected points (xP)")
    assert out.index("Mbeumo") < out.index("Rice")   # given order preserved (analytics rank)
    assert "8.0" in out and "23.3" in out and "73" in out   # price, xP, and xMins (0.81×90→73)
    assert "Own%" not in out                          # plain shortlist: no ownership column


def test_render_shortlist_show_own_adds_ownership_column():
    def _row(name, price, xp, w, own):
        return {"web_name": name, "team": "MUN", "position": "MID", "price": price,
                "status": "a", "chance": None, "xp": xp, "minutes_weight": w, "selected_by": own}
    out = render_shortlist([_row("Diff", 6.0, 18.0, 0.9, 2.5)],
                           "Best differential MID — by expected points (xP)", show_own=True)
    assert "Own%" in out and "2.5" in out             # the ownership column + value


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


def test_analyse_decision_carries_the_squad_table_as_detail(monkeypatch):
    # US-107: `ask "analyse"` shows the full squad-analysis table (per-GW xP + weak links),
    # not just a one-line headline — the same table the `analyse` command prints (ADR-036).
    def _p(pid, pos, team, price):
        return {"id": pid, "position": pos, "team": team, "price": price,
                "web_name": f"P{pid}", "status": "a", "chance": None}
    owned = [_p(1, "GK", "AAA", 5.0), _p(2, "DEF", "BBB", 6.0),
             _p(3, "MID", "CCC", 8.0), _p(4, "FWD", "DDD", 9.0)]
    xp_by_id = {1: 12.0, 2: 15.0, 3: 25.0, 4: 30.0}
    by_gw = {pid: {1: xp / 3, 2: xp / 3, 3: xp / 3} for pid, xp in xp_by_id.items()}
    weight_by_id = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}
    squad = {"player_ids": [1, 2, 3, 4], "bench_ids": [1]}   # P1 benched → XI = 2,3,4
    monkeypatch.setattr(
        ask, "_squad_xp",
        lambda store, name, active_squad=None: (squad, owned, owned, xp_by_id, by_gw, [1, 2, 3], weight_by_id),
    )
    decision = ask._decide_analyse(store=None, squad_name="TST")
    assert "headline" not in decision                 # detail replaces the one-line headline
    assert isinstance(decision["detail"], str)
    assert "Starting XI:" in decision["detail"]
    assert "GW1" in decision["detail"]                # the per-GW breakdown Tony wanted
    assert "xMins" in decision["detail"]              # the expected-minutes column (xMins v0)
    assert "Weakest links:" in decision["detail"]     # who the weak starters are


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
    assert f["starting_XI_improvement_over_5_gameweeks"] == 15.4   # XI gain, not raw player delta (ADR-046)


def test_analyse_facts_availability_reads_none_when_no_issues():
    a = {"projected_xp": 278.1, "issues": [], "weakest": [{"web_name": "X", "xp": 19.4}]}
    f = _analyse_facts(a)
    assert f["availability_problems"] == "none"        # self-describing → no false injury implied
    assert f["weakest_starters"] == ["X (xP 19.4)"]


def test_analyse_facts_lists_availability_problems():
    a = {"projected_xp": 200, "issues": [{"web_name": "Inj"}], "weakest": []}
    assert _analyse_facts(a)["availability_problems"] == "1: Inj"


# ---- grounding verification (ADR-037) ---------------------------------------

_CAPTAIN_FACTS = {"player": "B.Fernandes (MUN)", "expected_points_next_gameweek": 7.4,
                  "fixture": "away against HUL", "is_penalty_taker": True}


def test_grounded_narration_passes():
    text = "B.Fernandes has 7.4 expected points and is the penalty taker, away against HUL."
    result = verify_grounding(text, _CAPTAIN_FACTS, subjects=["B.Fernandes"])
    assert result == {"numbers": [], "names": []}


def test_fabricated_numbers_are_flagged():
    text = "B.Fernandes is superb: 22 goals and 9.8 xP this week."
    result = verify_grounding(text, _CAPTAIN_FACTS, subjects=["B.Fernandes"])
    assert result["numbers"] == ["22", "9.8"]


def test_a_player_who_is_not_a_subject_is_flagged():
    text = "B.Fernandes is a better pick than Salah this week."
    result = verify_grounding(
        text, _CAPTAIN_FACTS, known_names=["B.Fernandes", "Salah"], subjects=["B.Fernandes"],
    )
    assert result["names"] == ["Salah"]          # Salah isn't a subject; B.Fernandes is


def test_the_subject_itself_is_not_flagged():
    text = "B.Fernandes is the clear pick."
    result = verify_grounding(
        text, _CAPTAIN_FACTS, known_names=["B.Fernandes"], subjects=["B.Fernandes"],
    )
    assert result["names"] == []


def test_short_names_and_common_words_do_not_false_positive():
    # "Son"/"Sá" are too short to match; "Ward" must be a whole word (not inside "forward")
    text = "A forward with a strong performance and a reason to start."
    result = verify_grounding(text, {}, known_names=["Son", "Sá", "Ward"])
    assert result["names"] == []


def test_empty_text_is_clean():
    assert verify_grounding("", _CAPTAIN_FACTS) == {"numbers": [], "names": []}


def test_assemble_verifies_the_narration():
    decision = {"headline": "Captain: X", "facts": {"expected_points": 7.4},
                "subjects": ["X"], "task": "explain"}
    clean = assemble("q", "captain", decision, narrator=lambda p: "X has 7.4 points.",
                     known_names=["X"])
    assert clean.trust == {"numbers": [], "names": []}
    fabricated = assemble("q", "captain", decision, narrator=lambda p: "X will score 20 goals.",
                          known_names=["X"])
    assert fabricated.trust["numbers"] == ["20"]


def test_render_ask_trust_line():
    from src.ui.ask import render_ask
    ok = AskResult("q", "captain", headline="H", facts={}, explanation="p",
                   trust={"numbers": [], "names": []})
    assert "✓ Checked" in render_ask(ok)
    warn = AskResult("q", "captain", headline="H", facts={}, explanation="p",
                     trust={"numbers": ["22"], "names": ["Salah"]})
    out = render_ask(warn)
    assert "⚠" in out and "22" in out and "Salah" in out


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
    assert f["transfers"] == ["sell A, buy B (+15.4 XI xP)", "sell C, buy D (+9.9 XI xP)"]
    assert f["total_starting_XI_improvement_over_5_gameweeks"] == 25.3


def test_transfer_and_analyse_ask_for_a_squad_when_missing():
    # these intents need a saved squad; no squad in the question → a helpful message (no store touched)
    r = ask.answer("what transfer should I make", narrator=lambda p: "unused")
    assert r.intent == "transfer" and "squad" in r.message.lower()
    r2 = ask.answer("analyse my chances", narrator=lambda p: "unused")
    assert r2.intent == "analyse" and "squad" in r2.message.lower()


# ---- conversational follow-ups (ADR-047) ------------------------------------

def test_detect_followup_classifies_bare_triggers():
    assert detect_followup("why?").kind == "why"
    assert detect_followup("why not?").kind == "why"
    assert detect_followup("explain that").kind == "why"
    assert detect_followup("and the second best?").kind == "next"
    assert detect_followup("who else?").kind == "next"
    assert detect_followup("another one?").kind == "next"
    fu = detect_followup("what about defenders?")
    assert fu.kind == "whatabout" and fu.position == "DEF"
    assert detect_followup("what about keepers?").position == "GK"


def test_detect_followup_ignores_fresh_questions_with_a_subject():
    # the safety property: a line carrying its own subject is a FRESH question, not a follow-up
    assert detect_followup("why is Haaland so good?") is None
    assert detect_followup("best midfielders under 8m") is None
    assert detect_followup("who should I captain for TS?") is None
    assert detect_followup("what about a cheap midfielder?") is None   # 'cheap' isn't filler
    assert detect_followup("") is None


def test_swap_position_keeps_price_and_value():
    assert _swap_position("best midfielders under 8m", "DEF") == "best defender under 8m"
    assert _swap_position("best value goalkeepers", "FWD") == "best value forward"
    # no position word in the original → the new position is appended (constraints preserved)
    assert _swap_position("best players under 6m", "MID") == "best players under 6m midfielder"


def _canned(rank=0, **extra):
    return {"headline": f"rank {rank}", "facts": {"r": rank}, "subjects": ["X"], "task": "t", **extra}


def test_why_renarrates_the_same_facts_and_leaves_context():
    store = types.SimpleNamespace(get_players=lambda: [])
    decision = {"headline": "h", "facts": {"x": 1}, "subjects": ["Haaland"], "task": "orig"}
    ctx = Context(intent="captain", squad="TS", question="captain for TS", decision=decision)
    seen = {}
    result, new_ctx = _apply_followup(
        FollowUp("why"), ctx, store, lambda prompt: seen.setdefault("p", prompt) or "because",
    )
    assert new_ctx is ctx                       # a "why" doesn't move the conversation on
    assert result.facts == {"x": 1}             # SAME facts (re-narration, not new analytics)
    assert "Haaland" in seen["p"]               # the detailed task names the subject


def test_next_advances_the_rank(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ask, "_dispatch",
        lambda intent, store, q, squad, *, count=1, rank=0, active_squad=None: (
            calls.append((intent, rank)) or _canned(rank)),
    )
    store = types.SimpleNamespace(get_players=lambda: [])
    ctx = Context(intent="captain", squad="TS", question="captain for TS", decision=_canned(0))
    result, new_ctx = _apply_followup(FollowUp("next"), ctx, store, lambda p: None)
    assert calls == [("captain", 1)] and new_ctx.rank == 1


def test_next_past_the_end_keeps_the_rank(monkeypatch):
    monkeypatch.setattr(ask, "_dispatch",
                        lambda *a, **k: {"message": "That's all I have."})
    store = types.SimpleNamespace(get_players=lambda: [])
    ctx = Context(intent="captain", squad="TS", question="captain for TS", rank=2,
                  decision=_canned(2))
    result, new_ctx = _apply_followup(FollowUp("next"), ctx, store, lambda p: None)
    assert result.message == "That's all I have." and new_ctx.rank == 2   # not advanced past end


def test_whatabout_swaps_position_shortlist_only(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        ask, "_dispatch",
        lambda intent, store, q, squad, *, count=1, rank=0, active_squad=None: (
            seen.update(q=q, rank=rank) or _canned(rank, detail="d")),
    )
    store = types.SimpleNamespace(get_players=lambda: [])
    ctx = Context(intent="shortlist", question="best midfielders under 8m", rank=3,
                  decision=_canned(3))
    result, new_ctx = _apply_followup(FollowUp("whatabout", position="DEF"), ctx, store,
                                      lambda p: None)
    assert "defender" in seen["q"] and "8m" in seen["q"]   # swapped position, kept the cap
    assert seen["rank"] == 0 and new_ctx.rank == 0         # a new query resets the page
    # what-about after a non-shortlist intent doesn't apply → None (converse falls through)
    ctx2 = Context(intent="captain", squad="TS", question="captain for TS", decision=_canned(0))
    assert _apply_followup(FollowUp("whatabout", position="DEF"), ctx2, store, lambda p: None) is None


def test_converse_nudges_a_followup_with_no_context():
    store = types.SimpleNamespace(get_players=lambda: [])
    result, ctx = converse("why?", None, store=store, narrator=lambda p: None)
    assert ctx is None and "Ask a question first" in result.message


def test_answer_one_shot_is_unchanged_for_an_unrecognised_question(monkeypatch):
    # the one-shot `ask` is `converse` with no context → a follow-up-only line still falls back
    monkeypatch.setattr(ask, "SquadStore", lambda: types.SimpleNamespace(names=lambda: []))
    store = types.SimpleNamespace(get_players=lambda: [])
    result = ask.answer("what is the meaning of life", store=store, narrator=lambda p: None)
    assert result.intent is None and "captaincy" in result.message


def test_chat_transcript_threads_context_and_stops_at_quit(monkeypatch):
    # the REPL heart: blank lines skipped, an exit word stops, the context carries turn-to-turn
    seen = []

    def fake_converse(q, ctx, *, store, narrator=None, active_squad=None):
        seen.append((q, ctx))
        return AskResult(q, "x", headline=f"ans:{q}"), f"ctx-after-{q}"

    monkeypatch.setattr(ask, "converse", fake_converse)
    lines = ["who should I captain?", "", "  ", "why?", "quit", "never reached"]
    results = list(ask.chat_transcript(lines, store=object(), narrator=lambda p: None))

    assert [r.headline for r in results] == ["ans:who should I captain?", "ans:why?"]
    assert seen == [("who should I captain?", None),        # first turn starts with no context…
                    ("why?", "ctx-after-who should I captain?")]   # …then the last turn's context


# --- Sprint 066: `ask` sees the session active squad (Feedback_Log — the web Ask bug) ---------------

def test_load_squad_prefers_the_active_session_squad():
    active = {"name": "MyXI", "player_ids": [1, 2, 3]}
    assert ask._load_squad("MyXI", active) is active          # the active squad wins on a name match
    assert ask._load_squad("no-such-zz", active) is None      # else → SquadStore (a bogus name → None)
    assert ask._load_squad("MyXI", None) is None              # no active squad → SquadStore (bogus → None)


def test_known_squad_names_includes_the_active_squad():
    active = {"name": "MyXI", "player_ids": [1]}
    assert "MyXI" in ask._known_squad_names(active)
    assert "MyXI" not in ask._known_squad_names(None)


def test_ask_captain_scopes_to_the_active_session_squad():
    # the reported bug: an active squad not in SquadStore must scope captain to it, not "(all players)"
    from src.storage import Storage
    from src.ui.ask import render_ask

    store = Storage()
    try:
        players = [dict(p) for p in store.get_players()]
    finally:
        store.close()
    if not players:
        return

    def cheap(pos, n):
        return sorted((p for p in players if p["position"] == pos), key=lambda p: p["price"])[:n]
    picks = cheap("GK", 2) + cheap("DEF", 5) + cheap("MID", 5) + cheap("FWD", 3)
    active = {"name": "ZZTestXI", "player_ids": [p["id"] for p in picks],
              "player_names": [p["web_name"] for p in picks], "bench_ids": [], "cost": 100.0}

    with_active = render_ask(ask.answer("who should i captain from ZZTestXI", active_squad=active))
    assert "squad 'ZZTestXI'" in with_active and "all players" not in with_active
    without = render_ask(ask.answer("who should i captain from ZZTestXI"))   # not in SquadStore
    assert "all players" in without                                          # the old fallback


# --- trends intent (Sprint 067) — community "trending" from free FPL crowd data --------------------

def test_routes_trends_and_not_transfer():
    assert route("who is most transferred in", known_squads=[])[0] == "trends"
    assert route("most owned midfielders", known_squads=[])[0] == "trends"
    assert route("who's in form", known_squads=[])[0] == "trends"
    assert route("what transfer should I make", known_squads=[])[0] == "transfer"   # advice, not trends


def _trend_player(pid, name, pos, own, net_in=0, form=0.0):
    return {"id": pid, "web_name": name, "team": "ARS", "position": pos, "selected_by": own,
            "transfers_in_event": net_in, "transfers_out_event": 0, "form": form}


def test_decide_trends_most_owned_now():
    players = [_trend_player(1, "A", "MID", 60), _trend_player(2, "B", "MID", 20),
               _trend_player(3, "C", "FWD", 90)]
    store = types.SimpleNamespace(get_players=lambda: players)
    d = ask._decide_trends(store, "most owned midfielders")           # position-filtered
    assert "detail" in d and "A" in d["detail"] and "C" not in d["detail"]   # MID only, A (60) leads
    assert d["facts"]["top"][0].startswith("A")


def test_decide_trends_momentum_is_preseason_gated():
    players = [_trend_player(1, "A", "MID", 60, net_in=0, form=0.0)]   # momentum 0 (preseason)
    store = types.SimpleNamespace(get_players=lambda: players)
    d = ask._decide_trends(store, "who is most transferred in")
    assert "GW1" in d["message"] and "detail" not in d              # a clear "live from GW1" message
