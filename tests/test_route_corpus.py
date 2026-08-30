"""The routing corpus — a standing check that `ask.route` handles how people actually phrase things.

Built 2026-08-30 to test the claim *"the router is the ceiling, not the prose"* (ADR-168 §🔬) **before**
reaching for an LLM classifier. The corpus is deliberately not written to make that claim true: most of it
is phrasings the keyword table should already get, so a bad score would mean an unfair corpus rather than a
broken router.

**What it measured, and why it matters more than the score:** the first run found *one* genuinely harmful
mis-route in 30 — *"wildcard now or wait?"* built a squad, because `chips` carries no bare `"wildcard"` and
`build_squad` does. Three more questions fell through to the catch-all, all natural phrasings. Two others
looked wrong and **were not** — `rules` answers *"how many points is a goal worth?"* with the exact scoring
table, so the label was mine to fix, not the router's.

Four keyword additions took it to **24/25 routable, 0 missed**. That is the case against an LLM classifier,
not for one — and the decisive part is that a model **cannot run on Streamlit Cloud at all**, so it would
only ever help the owner-only Admin surface, while keywords work everywhere.

Add a row here whenever a real question routes badly. The corpus is the evidence; the score is a summary.
"""
import pytest

from src.ask import route

_SQUADS = ["RoboTS"]

# (question, expected intent or None) — None means "genuinely outside what the app does"
CORPUS = [
    # --- should route, phrased plainly (the keyword table's home ground) ---
    ("who should I captain from RoboTS?", "captain"),
    ("what transfer should I make for RoboTS?", "transfer"),
    ("analyse RoboTS", "analyse"),
    ("is Haaland worth the money?", "worth"),
    ("best differential midfielders under £8m", "shortlist"),
    ("how does bench boost work?", "rules"),
    ("when does Arsenal play next?", "fixtures"),
    ("compare Salah and Palmer", "compare"),
    ("which chip should I use for RoboTS?", "chips"),
    ("build me a squad", "build_squad"),
    ("who should I start this week for RoboTS?", "start_bench"),
    ("what should I do this week for RoboTS?", "gameweek"),
    ("who is trending?", "trends"),
    ("who is about to rise in price?", "price"),
    ("how many points is a goal worth?", "scoring"),
    ("show me Salah's history", "history"),
    # --- should route, phrased the way people actually talk ---
    ("armband this week?", "captain"),
    ("should I bring in Gyokeres?", "transfer"),
    ("is my team any good?", "analyse"),
    ("cheap defenders with good fixtures", "shortlist"),
    ("who do I bench?", "start_bench"),
    ("wildcard now or wait?", "chips"),
    ("Salah or Saka?", "compare"),
    ("is Watkins overpriced?", "worth"),
    ("who's in form?", "trends"),
    # --- genuinely open / strategic: nothing should match, and saying so is correct ---
    ("what's my best strategy for FPL", None),
    ("how do I get to the top 10k?", None),
    ("should I go for a set-and-forget team?", None),
    ("is it worth taking a hit this week?", None),
    ("how many premiums should I own?", None),
]


# `rules` legitimately answers scoring questions — it holds the scoring fact — so the two are interchangeable.
# This pair was a **label error of mine**, not a router bug: the first run scored it a failure and the answer
# was the exact scoring table.
_EQUIVALENT = {("scoring", "rules"), ("rules", "scoring")}


@pytest.mark.parametrize(("question", "expected"), CORPUS)
def test_a_real_question_routes_where_a_manager_would_expect(question, expected):
    got = route(question, known_squads=_SQUADS)[0]
    if expected is None:
        return                      # open/strategic: any outcome is a judgement call, not a contract
    assert got == expected or (expected, got) in _EQUIVALENT, (
        f"{question!r} routed to {got!r}, expected {expected!r}")


def test_a_wildcard_timing_question_is_never_answered_with_a_squad_build():
    """The one genuinely harmful mis-route the corpus found.

    Asked *when* to play a chip, the app built a fifteen and reported *"Confidence 95/100 · Spent £100.0m"* —
    a confident answer to a question nobody asked, which this project treats as worse than admitting it does
    not know. `chips` carried no bare `"wildcard"`; `build_squad` did.
    """
    for q in ("wildcard now or wait?", "should I hold my wildcard?", "wildcard this week or next?"):
        assert route(q, known_squads=_SQUADS)[0] == "chips", q
    # …while a build request still builds: the difference is the word after "wildcard".
    assert route("build me a wildcard squad", known_squads=_SQUADS)[0] == "build_squad"


def test_the_natural_phrasings_that_used_to_fall_through():
    """Three of the four gaps were people talking normally — the router only knew the textbook wording."""
    for question, expected in (("should I bring in Gyokeres?", "transfer"),
                               ("is my team any good?", "analyse"),
                               ("is Watkins overpriced?", "worth")):
        assert route(question, known_squads=_SQUADS)[0] == expected, question


def test_a_named_gameweek_reaches_the_weekly_plan():
    """*"What's the best strategy for GW3?"* used to hit the fallback (2026-08-30, owner-reported).

    The miss was narrow and slightly absurd: `gameweek` already answered this question — but every phrasing
    it knew assumed *this* week (`"this week"`, `"gw plan"`, `"what should i do"`), so naming the gameweek
    made it unreachable. `"what should I do in GW3?"` worked the whole time.
    """
    for q in ("what's the best strategy for GW3?",
              "what's th best strategy for GW3?",        # the owner's typo — routing must not care
              "what's the best strategy for gameweek 3?",
              "my plan for GW3",
              "how should I approach GW3?"):
        assert route(q, known_squads=_SQUADS)[0] == "gameweek", q


def test_strategy_is_a_modifier_not_a_topic():
    """`"<topic> strategy"` reaches the topic; bare `"strategy"` deliberately reaches **nothing**.

    Routing a bare "strategy" somewhere would mean picking one of chips/transfers/captaincy on the user's
    behalf and answering confidently — the exact failure shape as the wildcard-question-that-built-a-squad
    above. An honest miss now lists every intent (see `test_ask.py`), which is a better answer than a guess.
    """
    for q, expected in (("transfer strategy for GW3", "transfer"),
                        ("captaincy strategy for GW3", "captain"),
                        ("chip strategy for GW3", "chips")):
        assert route(q, known_squads=_SQUADS)[0] == expected, q

    for q in ("strategy", "best strategy", "what's the best strategy?"):
        assert route(q, known_squads=_SQUADS)[0] is None, q


def test_a_named_gameweek_does_not_swallow_the_position_shortlist():
    """`gameweek` is checked **before** `shortlist`, so its new phrases are "<planning word> for GW", never a
    bare "for gw" — which would have quietly captured every "best <position> for GW3"."""
    for q in ("best midfielders for GW3", "best value defenders for GW3",
              "best differential forwards for GW3"):
        assert route(q, known_squads=_SQUADS)[0] == "shortlist", q
