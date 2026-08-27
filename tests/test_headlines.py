"""Tests for headline extraction (ADR-151).

The model is always faked — no test needs Ollama, and the point of the design is that the model's answer is
**never trusted on its own**. Every guard here exists because a real model got something wrong on the real
corpus (spike 206), and the case is named in the docstring.
"""

from src.analytics.headlines import (
    event_phrase,
    extract,
    is_about_the_game,
    parse_response,
    resolve,
    supports_kind,
)
from src.analytics.names import build_index

PLAYERS = [
    {"id": 1, "web_name": "Watkins", "first_name": "Ollie", "second_name": "Watkins",
     "team": "AVL", "selected_by": 9.5},
    {"id": 2, "web_name": "Maddison", "first_name": "James", "second_name": "Maddison",
     "team": "TOT", "selected_by": 8.0},
    {"id": 3, "web_name": "James", "first_name": "Reece", "second_name": "James",
     "team": "CHE", "selected_by": 10.1},
]
INDEX = build_index(PLAYERS)


def _ask(reply):
    return lambda _prompt: reply


# ---- the model proposes; it never decides --------------------------------------------

def test_a_hallucinated_player_resolves_to_nobody_and_is_dropped():
    """The safety property the whole design rests on. A model that invents a name produces **fewer** events,
    never wrong ones, because the name has to resolve to exactly one player in our own data."""
    out = extract(["Someone signs for someone"], PLAYERS,
                  _ask('{"events":[{"player":"Xavier Nonexistent","kind":"transfer"}]}'))
    assert out == []


def test_a_kind_outside_the_closed_set_is_dropped():
    out = extract(["Watkins agreed a deal"], PLAYERS,
                  _ask('{"events":[{"player":"Ollie Watkins","kind":"vibes"}]}'))
    assert out == []


def test_a_malformed_reply_yields_nothing_rather_than_raising():
    """Models wrap JSON in prose, fences and thinking. A bad reply costs that headline, not the batch."""
    for reply in ("", "I think maybe?", "{oh no", '{"events": "not a list"}', None):
        assert parse_response(reply) == []


def test_a_model_that_errors_costs_one_headline_not_the_batch():
    def flaky(prompt):
        if "boom" in prompt:
            raise RuntimeError("model died")
        return '{"events":[{"player":"Ollie Watkins","kind":"transfer"}]}'

    out = extract(["boom", "Watkins agreed a deal to sign"], PLAYERS, flaky)
    assert len(out) == 1 and out[0]["element_id"] == 1


# ---- the veto: a rule that cannot propose, only refuse --------------------------------

def test_a_claimed_event_the_words_do_not_support_is_vetoed():
    """Measured: `qwen3:8b` scored 16/16 on the corpus, but the configured default `llama3.2` labelled
    *"Barry scores a hat-trick in the League Cup"*, *"Cole Palmer is Player of the Matchweek"* and
    *"Brentford attack is on fire!"* as **transfers**. Resolution could not catch those — the names are real,
    only the *kind* was invented — so the guard had a hole exactly where a smaller model fails.

    With the veto, the same weak model produced 7 events on the corpus, **all correct**: a weaker model now
    costs recall, never precision.
    """
    assert not supports_kind("Barry scores a hat-trick in the League Cup", "transfer")
    assert not supports_kind("Cole Palmer is Player of the Matchweek for GW1", "transfer")
    assert supports_kind("[Romano] Hilal agreed a deal to sign Ollie Watkins", "transfer")
    assert supports_kind("James Maddison out for up to two weeks due to a shoulder injury", "injury")

    vetoed = extract(["Watkins scores a hat-trick in the League Cup"], PLAYERS,
                     _ask('{"events":[{"player":"Ollie Watkins","kind":"transfer"}]}'))
    assert vetoed == [], "the model may claim a transfer; the sentence has to contain one"


def test_fpl_meta_headlines_never_reach_the_model():
    """FPL's vocabulary collides with football's. *"[FPL] Bruno Fernandes and Bryan Mbeumo have been
    transferred out over 277,000 times"* is a fact about managers clicking a button, and it produced the only
    two false positives in an otherwise clean run."""
    assert is_about_the_game("[FPL] Bruno Fernandes transferred out over 277,000 times")
    assert is_about_the_game("Tonight's Predicted Price Changes")
    assert not is_about_the_game("Nicolas Jackson to Aston Villa - David Ornstein")

    calls = []
    extract(["[FPL] Watkins transferred out 90,000 times"], PLAYERS,
            lambda p: calls.append(p) or '{"events":[]}')
    assert calls == [], "not even worth a model call"


# ---- resolution, dedupe, budget -------------------------------------------------------

def test_the_short_press_form_of_a_name_resolves():
    (event,) = extract(["Al-Hilal agreed a deal to sign Ollie Watkins"], PLAYERS,
                       _ask('{"events":[{"player":"Ollie Watkins","kind":"transfer"}]}'))
    assert event["element_id"] == 1 and event["kind"] == "transfer"


def test_the_same_story_from_two_feeds_is_stored_once():
    title = "Al-Hilal agreed a deal to sign Ollie Watkins"
    out = extract([title, title], PLAYERS,
                  _ask('{"events":[{"player":"Ollie Watkins","kind":"transfer"}]}'))
    assert len(out) == 1


def test_the_time_budget_stops_cleanly_and_keeps_what_it_had():
    """Not a nicety: this runs inside `refresh`, and a 60s per-call timeout across 112 headlines could hold
    the player data hostage for nearly two hours. Found by having to kill an unbudgeted run at ten minutes."""
    ticks = iter([0, 0, 1, 50])          # the third headline lands past a 10s budget
    calls = []

    def ask(prompt):
        calls.append(prompt)
        return '{"events":[{"player":"James Maddison","kind":"injury"}]}'

    out = extract(["a Maddison is injured", "b Maddison is injured", "c Maddison is injured"],
                  PLAYERS, ask, budget_seconds=10, clock=lambda: next(ticks))
    assert len(calls) == 2, "it must stop asking once the budget is gone"
    assert len(out) == 2, "…and keep both events it had already resolved — a partial read is worth having"
    assert [e["title"][0] for e in out] == ["a", "b"], "the third headline was never reached"


def test_the_source_is_named_when_the_headline_names_it():
    """"Romano reports" is a different claim from "someone said", and a reader is entitled to tell them
    apart — which is why the phrase quotes the headline it came from."""
    (event,) = extract(["[Romano] Hilal agreed a deal to sign Ollie Watkins, here we go!"], PLAYERS,
                       _ask('{"events":[{"player":"Ollie Watkins","kind":"transfer"}]}'))
    assert event["source"] == "Romano"
    phrase = event_phrase(event)
    assert "Romano reports" in phrase and "a move" in phrase and "Hilal" in phrase


def test_resolve_requires_exactly_one_match():
    assert resolve({"player": "James", "kind": "transfer"},
                   "James agreed a deal to sign", INDEX) is not None      # one player web_named James
    assert resolve({"player": "Nobody At All", "kind": "transfer"},
                   "Nobody At All agreed a deal", INDEX) is None


def test_money_alone_is_not_a_transfer():
    """From a live `refresh`: *"£4.0m defender boost, Sangare assist + Ampadu DefCons: FPL notes"* was stored
    as a **transfer**, because a bare "£" was a transfer cue — and **FPL prices are in pounds too**.

    A fee needs a verb. Removing the bare currency symbol cost none of the seven correct events in that run:
    each carries "sign", "joins", "agreed" or "closing in".
    """
    assert not supports_kind("£4.0m defender boost, Sangare assist: FPL notes", "transfer")
    assert supports_kind("Coventry agree £6m deal to sign Ethan Pinnock", "transfer")
    assert is_about_the_game("£4.0m defender boost, Sangare assist + Ampadu DefCons: FPL notes")
    # …and a genuine transfer that merely mentions FPL must survive both guards
    real = "[Crystal Palace] Axel Disasi (4.5m in FPL) signs for Crystal Palace on a season-long loan"
    assert not is_about_the_game(real) and supports_kind(real, "transfer")
