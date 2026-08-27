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
    _chips_facts,
    _decide_chips,
    _decide_compare,
    _decide_gameweek,
    _decide_history,
    _decide_price,
    _decide_rules,
    _decide_shortlist,
    _decide_worth,
    _gameweek_facts,
    _lineup_change,
    _match_players,
    _plan_facts,
    _resolve_pronoun,
    _shortlist_query,
    _squad_budget,
    _swap_position,
    _transfer_count,
    _transfer_facts,
    _value_verdict,
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


def test_routes_gameweek_for_a_holistic_weekly_question():
    # ADR-070: "what should I do this week" / "this gameweek plan" → the weekly plan intent
    assert route("what should I do this week for TS?", known_squads=["TS"]) == ("gameweek", "TS")
    assert route("this gameweek plan", known_squads=[])[0] == "gameweek"


def test_a_pointed_captain_question_still_beats_gameweek():
    # "captain this week" carries a specific keyword → captain wins (gameweek is placed after it)
    assert route("who should I captain this week for TS?", known_squads=["TS"])[0] == "captain"


def test_gameweek_asks_for_a_squad_when_missing():
    r = ask.answer("what should I do this week", narrator=lambda p: "unused")
    assert r.intent == "gameweek" and "squad" in r.message.lower()


def test_routes_chips_for_chip_questions():
    # ADR-082: the distinctive chip phrases route to the chips intent...
    assert route("which chip should I use for TS?", known_squads=["TS"]) == ("chips", "TS")
    assert route("chip strategy", known_squads=[])[0] == "chips"
    assert route("when should I use my bench boost?", known_squads=[])[0] == "chips"
    assert route("triple captain advice", known_squads=[])[0] == "chips"
    assert route("use my wildcard?", known_squads=[])[0] == "chips"


def test_chips_intent_does_not_hijack_the_build_captain_or_bench_routes():
    # the chip phrases are chosen so they can't steal the existing routes (the collision guard, ADR-082)
    assert route("build me a squad for a bench boost", known_squads=[])[0] == "build_squad"
    assert route("who should I captain from TS?", known_squads=["TS"])[0] == "captain"
    assert route("who should I start from TS?", known_squads=["TS"])[0] == "start_bench"


def test_chips_asks_for_a_squad_when_missing():
    r = ask.answer("which chip should I use", narrator=lambda p: "unused")
    assert r.intent == "chips" and "squad" in r.message.lower()


def test_routes_rules_for_general_fpl_questions():
    # ADR-085: question-shaped rules cues route to the rules intent
    for q in ("how does bench boost work?", "how do transfers work?", "how many points for a goal?",
              "when is the deadline?", "how does defensive contribution work?"):
        assert route(q, known_squads=["TS"])[0] == "rules", q


def test_rules_intent_does_not_hijack_squad_commands():
    # rules cues are general/question-shaped, so squad commands keep their intents (the collision guard)
    assert route("fix my bench", known_squads=[])[0] == "start_bench"
    assert route("what transfer should I make", known_squads=[])[0] == "transfer"
    assert route("how good is my squad", known_squads=[])[0] == "analyse"
    assert route("which chip should I use for TS?", known_squads=["TS"])[0] == "chips"
    assert route("build me a squad for a bench boost", known_squads=[])[0] == "build_squad"


def test_decide_rules_is_grounded_and_verified():
    # ADR-085: the rules answer is the curated facts; a narration restating them verifies clean (✓),
    # an invented number is flagged (⚠), and without a model the facts block still shows.
    decision = _decide_rules("how do transfers work?")
    assert "transfers" in decision["facts"] and "FPL rules" in decision["detail"]

    ok = assemble("q", "rules", decision,
                  narrator=lambda p: "You get 1 free transfer a week, saved up to 5; extras cost 4 points.")
    assert ok.trust == {"numbers": [], "names": []}                 # every figure traces to the KB facts

    bad = assemble("q", "rules", decision, narrator=lambda p: "Extra transfers cost 99 points.")
    assert bad.trust == {"numbers": ["99"], "names": []}            # the invented figure is flagged

    degraded = assemble("q", "rules", decision, narrator=lambda p: None)
    assert degraded.detail and degraded.trust is None              # the facts block is the truth without a model


def test_decide_rules_falls_back_to_free_form_when_no_topic_matches():
    # US-260 (ADR-085): a rules-shaped question with no curated fact → the labelled free-form tail
    decision = _decide_rules("how does the offside rule work?")
    assert decision == {"free_form": True, "question": "how does the offside rule work?"}


def test_free_form_answer_is_labelled_and_degrades(monkeypatch):
    # US-260 (ADR-085): an unrecognised question → a free-form answer tagged ℹ (not verified); no model → help.
    from src.ui.ask import render_ask

    # a fake store so route()/_fresh run without touching the real DB for player names
    class _S:
        def get_players(self):
            return []

    r, _ = converse("what's your general philosophy on early-season teams?", None, store=_S(),
                    narrator=lambda p: "Early on, favour proven minutes and good fixtures over punts.")
    assert r.intent == "chat" and r.trust == {"free_form": True}
    assert "not checked" in render_ask(r).lower()                      # the ℹ label is shown

    degraded, _ = converse("what's your general philosophy on early-season teams?", None, store=_S(),
                           narrator=lambda p: None)
    assert degraded.message and degraded.explanation is None           # no model → the honest help message


def test_resolve_pronoun_rewrites_to_the_sole_subject():
    # ADR-080: a pronoun → the last turn's single subject; possessives → name's
    ctx = Context(intent="worth", decision={"subjects": ["Haaland"], "facts": {}})
    assert _resolve_pronoun("is he worth captaining?", ctx) == "is Haaland worth captaining?"
    assert _resolve_pronoun("compare him to Isak", ctx) == "compare Haaland to Isak"
    assert _resolve_pronoun("what are his fixtures?", ctx) == "what are Haaland's fixtures?"


def test_resolve_pronoun_is_a_no_op_when_ambiguous_or_no_pronoun():
    two = Context(intent="compare", decision={"subjects": ["Haaland", "Salah"], "facts": {}})
    assert _resolve_pronoun("is he better?", two) == "is he better?"        # 2 subjects → ambiguous
    one = Context(intent="worth", decision={"subjects": ["Haaland"], "facts": {}})
    assert _resolve_pronoun("best midfielders under £8m", one) == "best midfielders under £8m"  # no pronoun
    assert _resolve_pronoun("is he worth it?", None) == "is he worth it?"   # no context
    assert _resolve_pronoun("the theatre", one) == "the theatre"           # 'the' not matched (whole-word)


def test_pronoun_resolves_across_a_converse_turn():
    # a real chat: worth(Haaland) → "compare him to Isak" resolves 'him' → Haaland → the compare intent
    from src import ask
    from src.storage import Storage

    store = Storage()
    try:
        _r1, ctx = ask.converse("is Haaland worth the money?", None, store=store, narrator=lambda p: None)
        r2, _c2 = ask.converse("compare him to Isak", ctx, store=store, narrator=lambda p: None)
    finally:
        store.close()
    assert r2.intent == "compare" and not r2.message   # resolved + routed, not a "name a player" fallback


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


def _pp(pid, name, tin, tout, own, status="a"):
    # a price-test player row (US-317): net transfers + ownership drive price_pressure
    return {"id": pid, "web_name": name, "team": "ARS", "position": "MID", "status": status,
            "transfers_in_event": tin, "transfers_out_event": tout, "selected_by": own}


def test_routes_price_for_prediction_questions():
    # US-317: price-prediction phrasing hits the predictor; a rules Q about price stays rules; bare risers = trends
    assert route("who's about to rise?", known_squads=[])[0] == "price"
    assert route("which players are about to fall in price?", known_squads=[])[0] == "price"
    assert route("price risers", known_squads=[])[0] == "price"
    assert route("how do price rises work?", known_squads=[])[0] == "rules"
    assert route("who are the risers?", known_squads=[])[0] == "trends"


def test_decide_price_is_a_preseason_message_when_flat():
    # US-317: 0 net transfers (preseason) → no movers → a clear 'live at GW1' message
    store = types.SimpleNamespace(get_players=lambda: [_pp(1, "Flat", 0, 0, 20)])
    d = _decide_price(store, "who's about to rise?")
    assert "GW1" in d["message"] and "flat" in d["message"].lower()


def test_decide_price_names_risers_and_fallers():
    # US-317: a big +net/own → ▲ rise; a big −net/own → ▼ fall; the movers are named + grounded (ADR-140)
    store = types.SimpleNamespace(get_players=lambda: [
        _pp(1, "Riser", 120_000, 0, 5),        # pressure +24,000 ≥ threshold → rise
        _pp(2, "Faller", 0, 120_000, 5),       # pressure −24,000 → fall
        _pp(3, "Stable", 100, 100, 50),        # net 0 → stable
    ])
    d = _decide_price(store, "who's about to rise or fall?")
    assert "Riser" in d["subjects"] and "Faller" in d["subjects"] and "Stable" not in d["subjects"]
    assert any("Riser" in r for r in d["facts"]["likely_risers"])
    assert any("Faller" in r for r in d["facts"]["likely_fallers"])
    assert "▲" in d["detail"] and "▼" in d["detail"]


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
    assert "Why a differential?" in d["detail"]            # US-288: the benefit lead
    assert "Standout signals" in d["detail"] and "Diff (" in d["detail"]   # per-pick "why these"


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


def test_render_shortlist_rationale_adds_a_why_and_standout_signals():
    # US-288: a rationale prepends the benefit lead + per-pick standout signals; without it, byte-identical.
    def _row(name, xp, w, **extra):
        base = {"web_name": name, "team": "ARS", "position": "MID", "price": 6.0, "status": "a",
                "chance": None, "xp": xp, "minutes_weight": w, "selected_by": 2.0,
                "penalties_order": None, "corners_order": None, "freekicks_order": None, "form": 0.0}
        return {**base, **extra}
    rows = [_row("Nailed", 18.0, 0.9), _row("Rotated", 17.0, 0.5, freekicks_order=1)]
    out = render_shortlist(rows, "Best differential MID — by xP", show_own=True,
                           rationale="Why a differential? Play them for upside.")
    assert "Why a differential?" in out and "Standout signals (ranked by xP):" in out
    assert "Nailed (18.0 xP) — nailed" in out                         # mw ≥ 0.7 → nailed
    assert "Rotated (17.0 xP) — rotation risk" in out and "🎯 FK" in out   # mw < 0.7 → risk + set-piece
    assert "Standout signals" not in render_shortlist(rows, "Best MID — by xP")   # plain: no rationale block


# ---- history intent (US-296) — single-player season record ------------------

def test_routes_history_without_stealing_worth_or_squad_commands():
    assert route("Haaland's history", known_squads=[])[0] == "history"
    assert route("how did Haaland do last season?", known_squads=[])[0] == "history"
    assert route("Palmer past seasons", known_squads=[])[0] == "history"
    assert route("is Haaland worth the money?", known_squads=[])[0] == "worth"       # worth still wins
    assert route("who should I captain?", known_squads=[])[0] == "captain"           # not history


def test_decide_history_grounds_a_players_seasons_and_verifies():
    # US-296: the answer carries a rendered detail + facts (last season pts/mins) so narration verifies.
    from src.storage import Storage
    store = Storage()
    try:
        has = any(p["web_name"] == "Haaland" and store.get_history_past(p["code"]) for p in store.get_players())
    finally:
        store.close()
    if not has:
        return
    d = _decide_history(Storage(), "Haaland's history")
    assert "History — Haaland" in d["detail"] and "Past seasons" in d["detail"]
    assert "player" in d["facts"] and d["facts"]["seasons_on_record"] >= 1
    assert "last_season" in d["facts"] and "pts" in d["facts"]["last_season"]
    assert d["subjects"] == ["Haaland"]


def test_decide_history_degrades_without_a_player():
    import types
    store = types.SimpleNamespace(get_players=lambda: [{"id": 1, "web_name": "Solo", "team": "X",
                                                        "position": "MID", "code": 1}])
    d = _decide_history(store, "show me a history")           # no named player
    assert "Name a player" in d["message"]


# ---- worth intent (ADR-061) — single-player value verdict -------------------

def test_routes_worth_before_transfer_and_captain():
    # ADR-061: a single-player value question → `worth`, not transfer ("buy") or captain
    assert route("is Haaland worth the money?", known_squads=[])[0] == "worth"
    assert route("is Palmer worth buying?", known_squads=[])[0] == "worth"        # not transfer via "buy"
    assert route("is Saka good value?", known_squads=[])[0] == "worth"
    assert route("is Haaland worth captaining?", known_squads=[])[0] == "captain"  # value phrases only


def test_value_verdict_tiers():
    assert _value_verdict(1.5) == "good value"
    assert _value_verdict(1.0) == "fair value"
    assert _value_verdict(0.5) == "pricey for the output"


def _worth_store(players):
    return types.SimpleNamespace(
        get_players=lambda: players,
        get_upcoming_fixtures=lambda: [
            {"event": 1, "team_h": 1, "team_a": 2, "home": "ARS", "away": "BUR",
             "team_h_difficulty": 3, "team_a_difficulty": 3,
             "home_team_strength": None, "away_team_strength": None}],
        get_history_by_code=lambda: {},
        get_gw_history_by_code=lambda: {},
    )


def _worth_player(name, ppg, price, pid, code, status="a"):
    # neutral fixture (difficulty 3) → xp == ppg, so value == ppg / price
    return {"id": pid, "code": code, "web_name": name, "position": "MID", "price": price,
            "status": status, "chance": None, "team": "ARS", "team_id": 1,
            "points_per_game": ppg, "ep_next": ppg, "selected_by": 3.0}


# three MIDs: values 1.20 / 0.83 / 0.50 → median 0.83
_WORTH_TRIO = [_worth_player("Aaa", 6.0, 5.0, 1, 1),
               _worth_player("Bbb", 5.0, 6.0, 2, 2),
               _worth_player("Ccc", 4.0, 8.0, 3, 3)]


def test_decide_worth_good_value_with_rank_and_median():
    d = _decide_worth(_worth_store(_WORTH_TRIO), "is Aaa worth the money?")
    assert d["facts"]["verdict"] == "good value"          # 1.20 / 0.83 = 1.44 ≥ 1.15
    assert d["facts"]["position_rank_by_value"] == "1 of 3 MIDs"
    assert d["facts"]["value"] == "1.20 xP per £m"
    assert "0.83" in d["facts"]["position_median_value"]
    assert d["subjects"] == ["Aaa"]
    # US-284: the answer now explains *why* — a grounded Confidence·Edge·Risk block + the Model note, and the
    # values are facts (so a narrated number verifies). ("Edge" = the reasons heading, MADBOOTS vocab ADR-107.)
    assert "Confidence:" in d["detail"] and "Edge" in d["detail"] and "Model note:" in d["detail"]
    assert "confidence" in d["facts"] and "why" in d["facts"]


def test_decide_worth_pricey_for_expensive_low_output():
    d = _decide_worth(_worth_store(_WORTH_TRIO), "is Ccc good value?")
    assert d["facts"]["verdict"] == "pricey for the output"   # 0.50 / 0.83 = 0.60 < 0.9
    assert d["facts"]["position_rank_by_value"] == "3 of 3 MIDs"


def test_decide_worth_degrades_without_a_player():
    d = _decide_worth(_worth_store(_WORTH_TRIO), "is it worth the money?")
    assert "Name a player" in d["message"]


def test_decide_worth_degrades_on_a_flagged_player():
    injured = [_worth_player("Zzz", 6.0, 5.0, 9, 9, status="i")]
    d = _decide_worth(_worth_store(injured), "is Zzz worth the money?")
    assert "flagged" in d["message"]


def test_squad_matched_by_name_regardless_of_phrasing():
    assert route("what transfer for TS?", known_squads=["TS"])[1] == "TS"     # "for"
    assert route("captain from TS", known_squads=["TS"])[1] == "TS"           # "from"
    # a stray word isn't mistaken for a squad → captain stays global
    assert route("who should I captain for the next gameweek", known_squads=["TS"])[1] is None


def test_unrecognised_question_has_no_intent():
    assert route("what is the meaning of life", known_squads=[]) == (None, None)


def test_build_answer_carries_the_squad():
    # ADR-062: a build answer exposes the 15 (SquadStore shape) so a web edge can adopt it
    res = ask.answer("build me a squad for £100m", narrator=lambda p: None)
    assert res.intent == "build_squad"
    assert res.squad and res.squad["name"] == "My squad"
    assert 11 <= len(res.squad["player_ids"]) <= 15
    assert len(res.squad["bench_ids"]) == len(res.squad["player_ids"]) - 11


def test_a_non_build_answer_carries_no_squad():
    res = ask.answer("best midfielders under £8m", narrator=lambda p: None)
    assert res.squad is None


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


def test_gameweek_facts_read_plainly_and_carry_every_number():
    plan = {
        "captain": {"web_name": "Haaland", "team": "MCI", "xp": 6.2, "venue": "H", "opponent": "BUR"},
        "lineup": {"has_declared_bench": True, "bring_in": [{"web_name": "Saka"}],
                   "drop": [{"web_name": "Foden"}]},
        "transfer": {"out": {"web_name": "Watkins", "xp": 3.1}, "in": {"web_name": "Isak", "xp": 5.0},
                     "gain": 1.9},
        "flags": [{"web_name": "Foden", "reason": "doubtful", "chance": 75}],
    }
    facts = _gameweek_facts(plan)
    assert facts["captain"].startswith("Haaland (MCI) — xP 6.2")
    assert facts["lineup_change"] == "start Saka; bench Foden"
    assert "buy Isak (xP 5.0)" in facts["transfer_to_consider"] and "+1.9" in facts["transfer_to_consider"]
    assert facts["flagged_players"] == "1: Foden (doubtful, 75%)"


class _FakeStore:
    """A store whose reads the gameweek decision touches directly return empty — the plan is stubbed."""
    def get_history_by_code(self):
        return {}

    def get_upcoming_fixtures(self):
        return []

    def get_headline_events(self):
        # ADR-151/153: a snapshot built without a language model carries none, which is the ordinary case and
        # the one this test models — the plan must read exactly as it did before headlines existed.
        return []

    def headline_events_by_id(self):
        return {}


def test_decide_gameweek_is_grounded_and_verified(monkeypatch):
    # ADR-070: the decision carries the plan as `detail`, names all owned players + the buy as
    # subjects, and a narration that restates only the facts verifies clean (✓, ADR-037).
    owned = [{"id": 1, "web_name": "Haaland"}, {"id": 2, "web_name": "Saka"}]
    plan = {
        "captain": {"web_name": "Haaland", "team": "MCI", "xp": 6.2, "venue": "H",
                    "opponent": "BUR", "penalty_taker": True, "doubtful": False},
        "lineup": {"start": owned, "bench": [], "has_declared_bench": False,
                   "bring_in": [], "drop": []},
        "transfer": {"out": {"web_name": "Saka", "team": "ARS", "xp": 3.1},
                     "in": {"web_name": "Palmer", "team": "CHE", "xp": 5.0}, "gain": 1.9},
        "flags": [],
    }
    monkeypatch.setattr(
        ask, "_squad_xp",
        lambda store, name, active_squad=None, *, horizon=5: (
            {"player_ids": [1, 2], "bench_ids": []}, owned, owned, {1: 6.2, 2: 3.1}, {}, [], {}),
    )
    monkeypatch.setattr(ask, "gameweek_plan", lambda *a, **k: plan)

    decision = _decide_gameweek(_FakeStore(), "TST")
    assert "This week — squad 'TST'" in decision["detail"]
    assert "Haaland" in decision["subjects"] and "Palmer" in decision["subjects"]   # owned + the buy
    assert "over 5 GW" in decision["detail"]                                        # default horizon
    # US-273/274 (ADR-089): explainability — a plan-level Confidence + a per-recommendation Edge (ADR-107 vocab)
    assert "Confidence:" in decision["detail"] and "Edge:" in decision["detail"]
    assert "confidence" in decision["facts"] and "why" in decision["facts"]         # in the facts → verifiable

    res = assemble("q", "gameweek", decision,
                   narrator=lambda p: "Captain Haaland (xP 6.2). Consider Saka to Palmer (+1.9).",
                   known_names=["Haaland", "Saka", "Palmer", "Isak"])
    assert res.trust == {"numbers": [], "names": []}                                 # every figure/name traces

    # US-238 (ADR-077): a chosen horizon flows through to the plan's transfer window
    narrowed = _decide_gameweek(_FakeStore(), "TST", horizon=2)
    assert "over 2 GW" in narrowed["detail"]


def test_chips_facts_read_plainly_and_carry_every_number():
    advice = {
        "triple_captain": {"gameweek": 1, "player": {"web_name": "Haaland", "team": "MCI"},
                           "player_xp": 9.0, "extra_points": 9.0},
        "bench_boost": {"gameweek": 2, "squad_total": 62.0, "bench_points": 13.0},
        "free_hit": {"gameweek": 4, "xi_total": 46.0},
        "wildcard": {"window": (3, 5), "gameweeks": [3, 4, 5], "avg_xi": 47.0},
    }
    facts = _chips_facts(advice)
    assert facts["triple_captain"].startswith("GW1: Haaland (MCI) — xP 9.0")
    assert "all 15 project 62.0 xP" in facts["bench_boost"] and "adds 13.0" in facts["bench_boost"]
    assert facts["free_hit"] == "GW4: your best XI projects only 46.0 xP — your weakest single week"
    assert "GW3 to GW5" in facts["wildcard"] and "average XI 47.0 xP" in facts["wildcard"]


def test_decide_chips_is_grounded_and_verified(monkeypatch):
    # ADR-082: the decision carries the advice as `detail`, names the TC player as a subject, and a
    # narration that restates only the facts verifies clean (✓, ADR-037).
    owned = [{"id": 1, "web_name": "Haaland"}, {"id": 2, "web_name": "Saka"}]
    advice = {
        "triple_captain": {"gameweek": 1, "player": {"web_name": "Haaland", "team": "MCI"},
                           "player_xp": 9.0, "extra_points": 9.0},
        "bench_boost": {"gameweek": 2, "squad_total": 62.0, "bench_points": 13.0},
        "free_hit": {"gameweek": 4, "xi_total": 46.0},
        "wildcard": {"window": (3, 5), "gameweeks": [3, 4, 5], "avg_xi": 47.0},
    }
    monkeypatch.setattr(
        ask, "_squad_xp",
        lambda store, name, active_squad=None, *, horizon=5: (
            {"player_ids": [1, 2], "bench_ids": []}, owned, owned, {}, {}, [1, 2, 3, 4], {}),
    )
    monkeypatch.setattr(ask, "chip_advisor", lambda *a, **k: advice)

    decision = _decide_chips(_FakeStore(), "TST", horizon=8)
    assert "Chip strategy — squad 'TST'" in decision["detail"]
    assert decision["subjects"] == ["Haaland"]                       # the named TC player

    res = assemble("q", "chips", decision,
                   narrator=lambda p: "Triple Captain in GW1 (Haaland, xP 9.0). Bench Boost GW2 "
                                      "(62.0 xP). Free Hit GW4 (46.0). Wildcard GW3 to GW5 (47.0).",
                   known_names=["Haaland", "Saka"])
    assert res.trust == {"numbers": [], "names": []}                 # every figure/name traces


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


def test_answer_one_shot_degrades_to_help_for_an_unrecognised_question(monkeypatch):
    # US-260 (ADR-085): an unrecognised question takes the free-form path (intent "chat"); with no model it
    # still degrades to the same help message — the honest fallback is unchanged.
    monkeypatch.setattr(ask, "SquadStore", lambda: types.SimpleNamespace(names=lambda: []))
    store = types.SimpleNamespace(get_players=lambda: [])
    result = ask.answer("what is the meaning of life", store=store, narrator=lambda p: None)
    assert result.intent == "chat" and "captaincy" in result.message


def test_chat_transcript_threads_context_and_stops_at_quit(monkeypatch):
    # the REPL heart: blank lines skipped, an exit word stops, the context carries turn-to-turn
    seen = []

    def fake_converse(q, ctx, *, store, narrator=None, active_squad=None):
        seen.append((q, ctx))
        return AskResult(q, "x", headline=f"ans:{q}"), f"ctx-after-{q}"

    monkeypatch.setattr(ask, "converse", fake_converse)
    lines = ["who should I captain?", "", "  ", "why?", "quit", "never reached"]
    turns = list(ask.chat_transcript(lines, store=object(), narrator=lambda p: None))

    assert [r.headline for r, _ctx in turns] == ["ans:who should I captain?", "ans:why?"]   # yields (result, ctx)
    assert [ctx for _r, ctx in turns] == ["ctx-after-who should I captain?", "ctx-after-why?"]  # ctx for persisting
    assert seen == [("who should I captain?", None),        # first turn starts with no context…
                    ("why?", "ctx-after-who should I captain?")]   # …then the last turn's context


def test_chat_transcript_resumes_a_seeded_context_and_forget_resets(monkeypatch):
    # ADR-091: a saved context seeds the thread (resume across runs); "forget" drops it (yields None context).
    def fake_converse(q, ctx, *, store, narrator=None, active_squad=None):
        return AskResult(q, "x", headline=f"ans:{q}"), f"ctx-after-{q}"

    monkeypatch.setattr(ask, "converse", fake_converse)
    turns = list(ask.chat_transcript(["why?", "forget", "who's the best?"], store=object(),
                                     context="resumed-ctx"))
    # the first turn builds on the seeded context; "forget" yields a None context; the next starts fresh
    assert turns[0][0].headline == "ans:why?"
    assert turns[1][1] is None and "forgotten" in turns[1][0].message
    assert turns[2][0].headline == "ans:who's the best?"


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


def test_ask_captain_defaults_to_the_loaded_squad_hyphen_and_bare(tmp_path, monkeypatch):
    # ADR-090: with a squad loaded, a hyphenated "my-team" AND a bare question both scope to it; an
    # explicit-global cue escapes to all players; and with no active squad it stays global (CLI parity).
    import src.ask as ask_mod
    from src.squads import SquadStore
    from src.storage import Storage
    from src.ui.ask import render_ask

    # Isolate the saved-squad store to an empty temp file, so ambient saved squads (RoboTS/TS) can't make
    # "my-team" resolve to a different saved squad — the routing then sees only the active squad.
    empty = str(tmp_path / "squads.json")
    monkeypatch.setattr(ask_mod, "SquadStore", lambda path=empty: SquadStore(path))

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

    hyphen = render_ask(ask.answer("who should I captain from my-team?", active_squad=active))
    assert "squad 'ZZTestXI'" in hyphen and "all players" not in hyphen   # the reported bug, fixed
    bare = render_ask(ask.answer("who should I captain?", active_squad=active))
    assert "squad 'ZZTestXI'" in bare                                     # default-to-loaded-squad
    glob = render_ask(ask.answer("who should I captain from all players?", active_squad=active))
    assert "all players" in glob and "squad 'ZZTestXI'" not in glob       # explicit-global escapes
    assert "Best Captain Picks" in glob and "to scope to your squad" in glob   # US-280: reframed + nudged
    assert "Best Captain Picks" not in bare and "Captain Pick" in bare    # the scoped answer reads differently
    cli = render_ask(ask.answer("who should I captain?"))                 # no active squad → global (CLI)
    assert "all players" in cli and "Best Captain Picks" in cli


def test_ask_captain_explains_with_confidence_and_verifies():
    # US-269 (ADR-089): the captain answer carries a grounded Why/Risk/Confidence block + facts, and a
    # narration restating those values verifies clean (✓); the LLM never invents a reason or the number.
    from src.storage import Storage
    from src.ui.ask import render_ask

    store = Storage()
    try:
        if not store.get_players():
            return
    finally:
        store.close()

    r = ask.answer("who should I captain from RoboTS?", narrator=lambda p: None)
    if r.intent != "captain" or r.detail is None:
        return                                                  # no such squad locally → nothing to assert
    assert "Confidence:" in r.detail and "Edge" in r.detail     # the grounded explanation block (ADR-107 vocab)
    assert "confidence" in r.facts and "why" in r.facts         # the values are facts (so narration verifies)
    rendered = render_ask(r)
    assert "✓" in rendered and "Captain Pick" in rendered       # US-277: the structured card
    assert "Alternatives" in rendered and "Model note:" in rendered   # runner-ups + the honest footer


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
