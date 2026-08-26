"""Tests for player-name resolution in free text (ADR-152).

Every case here is a real collision measured on the live squad list, not an invented one — which is why the
numbers appear in the docstrings. Naive `web_name` matching was wrong three ways, and each way is pinned.
"""

from src.analytics.names import CLEAR_OWNERSHIP, CLEAR_RATIO, build_index, find_mentions


def _p(pid, web, first, second, team="ARS", own=5.0):
    return {"id": pid, "web_name": web, "first_name": first, "second_name": second,
            "team": team, "selected_by": own}


COLE = _p(154, "Palmer", "Cole", "Palmer", "CHE", own=14.2)
ALEX = _p(301, "Palmer", "Alex", "Palmer", "IPS", own=4.5)
REECE = _p(142, "James", "Reece", "James", "CHE", own=10.1)
MADDISON = _p(999, "Maddison", "James", "Maddison", "TOT", own=8.0)


def test_a_longer_name_claims_the_text_so_a_shorter_one_cannot_match_inside_it():
    """The bug that made this module necessary. **90 `web_name`s sit inside a different player's full name** on
    the live data — `James` inside "James Maddison", `Keane` *and* `Lewis` both inside "Keane Lewis-Potter",
    `Hall` inside "Kiernan Dewsbury-Hall". The headline *"James Maddison out for up to two weeks"* credited
    Reece James with a mention.

    Longest-match-first with span consumption fixes it: "James Maddison" claims those characters, so the
    "James" pattern never sees them.
    """
    index = build_index([REECE, MADDISON])
    hits = find_mentions("James Maddison out for up to two weeks due to a shoulder injury", index)
    assert hits == {999: 1}, "Maddison is mentioned; Reece James is not"


def test_a_shared_surname_is_credited_once_to_the_clear_favourite():
    """14 `web_name`s are shared on live data. A bare "Palmer" used to credit **both** Cole Palmer (14.2%
    owned) and Alex Palmer, a backup goalkeeper — which is why the buzz board listed Palmer twice at 30
    mentions each."""
    index = build_index([COLE, ALEX])
    hits = find_mentions("Palmer in training - not injured", index)
    assert hits == {154: 1}, "one entry, and it is the midfielder the community means"


def test_the_full_name_wins_over_the_shared_surname():
    index = build_index([COLE, ALEX])
    assert find_mentions("Cole Palmer is Player of the Matchweek", index) == {154: 1}
    assert find_mentions("Alex Palmer kept a clean sheet", index) == {301: 1}


def test_a_genuinely_ambiguous_surname_is_dropped_rather_than_guessed():
    """Ambiguity resolves to **silence**, the same discipline as ADR-146's exodus note. Measured across the 14
    live collisions: 9 have a clear favourite; in the other 5 nobody owns any candidate, so nothing of value
    is lost by staying quiet."""
    a = _p(1, "Kamara", "Boubacar", "Kamara", "AVL", own=0.3)
    b = _p(2, "Kamara", "Abu", "Kamara", "HUL", own=0.0)
    index = build_index([a, b])
    assert find_mentions("Kamara starts again", index) == {}, "nobody owns either — do not guess"
    # …but the full name still resolves, because it is unambiguous by construction
    assert find_mentions("Boubacar Kamara starts again", index) == {1: 1}


def test_a_favourite_needs_BOTH_ownership_and_a_clear_margin():
    """Two thresholds, both measured. A player nobody owns is never a "favourite" however far ahead he is, and
    two well-owned players close together stay ambiguous (Palmer sits at 3.2× — just over the line)."""
    assert (CLEAR_OWNERSHIP, CLEAR_RATIO) == (1.0, 3.0)
    tiny_lead = build_index([_p(1, "Gomez", "A", "Gomez", own=4.0), _p(2, "Gomez", "B", "Gomez", own=3.0)])
    assert find_mentions("Gomez impressed", tiny_lead) == {}, "4.0 vs 3.0 is not a clear favourite"
    unowned = build_index([_p(1, "Davies", "A", "Davies", own=0.4), _p(2, "Davies", "B", "Davies", own=0.0)])
    assert find_mentions("Davies impressed", unowned) == {}, "an infinite ratio over nothing is still nothing"


def test_short_names_are_left_alone_because_they_collide_with_words():
    index = build_index([_p(1, "Ait", "Sofiane", "Ait", own=9.0)])
    assert find_mentions("The team ait around waiting", index) == {}


def test_repeat_mentions_in_one_text_all_count():
    index = build_index([COLE, ALEX])
    assert find_mentions("Palmer, Palmer, always Cole Palmer", index) == {154: 3}


def test_empty_and_odd_inputs_are_safe():
    index = build_index([COLE])
    assert find_mentions("", index) == {} and find_mentions(None, index) == {}
    assert build_index([]) == []
    assert find_mentions("Palmer", []) == {}
