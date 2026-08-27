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


# ---- A longer name we don't hold (ADR-157) --------------------------------------------------------
# Span consumption defeats "James Maddison" vs Reece James because we hold BOTH names. It cannot help when
# the longer name belongs to someone outside the Premier League — or to someone who isn't a player at all.
# All three of these came off the live 112-headline corpus.

_OUTSIDERS = [
    {"id": 1, "web_name": "Bradley", "first_name": "Conor", "second_name": "Bradley",
     "team": "LIV", "selected_by": 5.0},
    {"id": 2, "web_name": "Enzo", "first_name": "Enzo", "second_name": "Fernández",
     "team": "CHE", "selected_by": 6.0},
    {"id": 3, "web_name": "Watkins", "first_name": "Ollie", "second_name": "Watkins",
     "team": "AVL", "selected_by": 9.0},
]


def test_a_foreign_players_first_name_is_not_our_defender():
    """PSG's Bradley Barcola was crediting Conor Bradley with a €135m transfer."""
    index = build_index(_OUTSIDERS)
    assert find_mentions("Liverpool reach agreement with PSG for Bradley Barcola", index) == {}


def test_a_manager_is_not_a_player():
    """Enzo Maresca — a manager — was resolving to Enzo Fernández, and a transfer headline with his name in
    it is exactly the input the departure rule consumes."""
    index = build_index(_OUTSIDERS)
    assert find_mentions("Enzo Maresca reacts to the deal", index) == {}


def test_the_journalist_we_cite_as_a_source_is_not_a_player():
    index = build_index([*_OUTSIDERS, {"id": 4, "web_name": "David", "first_name": "David",
                                       "second_name": "Raya", "team": "ARS", "selected_by": 8.0}])
    assert 4 not in find_mentions("David Ornstein: Coventry agree a £6m deal", index)


def test_a_full_name_still_matches_when_a_capitalised_word_follows():
    """The rule is for bare surnames only. A full-name match is unambiguous by construction, so a real story
    must survive — this is the headline the whole departure feature was built on."""
    index = build_index(_OUTSIDERS)
    hits = find_mentions("Al-Hilal agreed a deal to sign Ollie Watkins, here we go", index)
    assert hits == {3: 1}


def test_an_ordinary_surname_mention_is_untouched():
    index = build_index(_OUTSIDERS)
    assert find_mentions("Watkins scored twice", index) == {3: 1}
    assert find_mentions("a late Bradley cross", index) == {1: 1}
