"""Tests for the Trending overview (ADR-170).

Two things carry the risk here: the patterns must stay *disjoint and calibrated* (no invented thresholds, no
player counted three ways), and the copy must never drift into **why** — that is Signals' half of the
doing-vs-saying axis, and collapsing it would put an unsourced guess beside a measured fact.
"""

from src.analytics.crowd import DIFFERENTIAL_OWN, FORM_MIN, TEMPLATE_OWN, TRENDING_NET
from src.analytics.crowd_watch import classify, watch_note, worth_noticing


def _p(pid=1, name="P", own=10.0, form=0.0, tin=0, tout=0):
    return {"id": pid, "web_name": name, "team": "AAA", "position": "MID", "price": 6.0,
            "selected_by": own, "form": form, "transfers_in_event": tin, "transfers_out_event": tout}


def test_in_form_and_under_owned_is_the_headline_pattern():
    """The only one that tells you something *before* the crowd does — a differential with evidence, rather
    than a differential because nobody has heard of him."""
    assert classify(_p(own=DIFFERENTIAL_OWN - 1, form=FORM_MIN + 1)) == "undervalued"
    assert classify(_p(own=DIFFERENTIAL_OWN + 5, form=FORM_MIN + 1)) is None   # in form, but already owned
    assert classify(_p(own=DIFFERENTIAL_OWN - 1, form=FORM_MIN - 1)) is None   # under-owned, but not in form


def test_a_bandwagon_needs_the_move_and_the_room_to_join_it():
    assert classify(_p(own=TEMPLATE_OWN - 5, tin=TRENDING_NET + 1)) == "bandwagon"
    # already template: the move is real but you are not early, so it is not this pattern
    assert classify(_p(own=TEMPLATE_OWN + 5, tin=TRENDING_NET + 1)) is None


def test_the_template_breaking_up_is_the_mirror_image():
    assert classify(_p(own=TEMPLATE_OWN + 5, tout=TRENDING_NET + 1)) == "template_breaking"
    assert classify(_p(own=DIFFERENTIAL_OWN, tout=TRENDING_NET + 1)) is None   # nobody owned him to begin with


def test_a_player_reports_one_pattern_not_three():
    """The shortlist answers "what should I notice?" — a name appearing three times with three framings is a
    worse answer than a name appearing once."""
    both = _p(own=DIFFERENTIAL_OWN - 1, form=FORM_MIN + 1, tin=TRENDING_NET + 1)
    assert classify(both) == "undervalued"
    groups = worth_noticing([both])
    assert sum(len(g["players"]) for g in groups) == 1


def test_every_threshold_is_one_that_already_exists():
    """No new cut-offs. `FORM_MIN`, `TRENDING_NET`, `DIFFERENTIAL_OWN` and `TEMPLATE_OWN` are calibrated
    constants; a fourth invented here would be a number with no population behind it."""
    import inspect

    from src.analytics import crowd_watch
    src = inspect.getsource(crowd_watch)
    for constant in ("FORM_MIN", "TRENDING_NET", "DIFFERENTIAL_OWN", "TEMPLATE_OWN"):
        assert constant in src
    # the only tunable this module owns is a display cap, and it is an argument with a default
    assert "per_pattern: int = 4" in src


def test_empty_groups_are_dropped_and_a_quiet_week_says_so():
    assert worth_noticing([_p()]) == []
    note = watch_note([])
    assert "quiet week is a finding, not a gap" in note


def test_the_note_points_at_signals_for_why_and_never_guesses():
    """Trending says what the crowd is **doing**; Signals says what is being **said** (ADR-149/150). The note
    must send the reader there rather than speculating on a cause."""
    groups = worth_noticing([_p(own=1.0, form=FORM_MIN + 2)])
    note = watch_note(groups)
    assert "Signals" in note and "not a points projection" in note
    for guess in ("because", "injur", "transfer rumour", "expected to"):
        assert guess not in note.lower()


def test_the_reason_speaks_in_the_crowds_own_units():
    groups = worth_noticing([_p(own=2.2, form=8.0)])
    reason = groups[0]["players"][0]["reason"]
    assert "form 8.0" in reason and "2.2% owned" in reason
    assert "xP" not in reason, "crowd data never claims points"


def test_it_is_safe_on_missing_or_empty_data():
    assert worth_noticing([]) == [] and worth_noticing(None) == []
    assert classify({"web_name": "X"}) is None                 # no ownership → nothing to say
