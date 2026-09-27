"""Names arriving from a microphone (ADR-315).

⭐⭐ A phone's recogniser has never heard of Semenyo, Ndiaye or Cunha. It returns the nearest thing in its
own vocabulary — *"semenio"*, *"n diaye"*, *"koonya"* — so the question reaching the engine names a player
who does not exist.

⚠️⚠️⚠️ **A similarity threshold alone cannot fix that, and measuring is what said so.** Of 647 web names,
**87 pairs are already ≥0.80 similar to each other**, including **`McAteer` ↔ `McAtee` at 0.92 — two
different players.** Any cutoff loose enough to catch a mangled name sits inside the range where real
players are confusable, which is why the rule is a threshold **and a margin**.
"""

from __future__ import annotations

import pytest

from src.analytics.names import (
    MIN_MARGIN,
    MIN_RATIO,
    build_index,
    find_spoken_mentions,
    nearest_name,
)
from src.storage import Storage


@pytest.fixture(scope="module")
def players():
    store = Storage()
    try:
        return store.get_players()
    finally:
        store.close()


@pytest.fixture(scope="module")
def index(players):
    return build_index(players)


#: What a recogniser actually returns for names it does not hold, and who was meant.
#: ⭐ Only the ones the measured rule accepts — the rest are covered by `test_an_unclear_guess_is_refused`.
HEARD = {
    "semenio": "Semenyo",
    "sam enyo": "Semenyo",
    "n diaye": "Ndiaye",
    "cuna": "Cunha",
    "harland": "Haaland",
    "gvardial": "Gvardiol",
    "mbeumo": "Mbeumo",
}

#: ⚠️ Ordinary words a question is full of. **None may ever resolve to a player** — this is the failure that
#: would matter, because it puts a name into an answer the reader never said.
NOISE = ["captain", "transfer", "should", "bench", "this week", "who", "better", "points",
         "my team", "fixtures", "differential", "wildcard", "assist", "vice", "gameweek"]


@pytest.mark.parametrize("spoken", sorted(HEARD))
def test_a_mangled_name_still_finds_its_player(spoken, index, players):
    by_id = {p["id"]: p["web_name"] for p in players}

    found = nearest_name(spoken, index)

    assert found is not None, f"{spoken!r} resolved to nobody"
    assert by_id[found[0]["id"]] == HEARD[spoken]


@pytest.mark.parametrize("word", NOISE)
def test_an_ordinary_word_is_never_a_player(word, index):
    """⭐ Measured: the noise words peak at **0.71** (*"better"* → Zetterer), so the 0.85 threshold clears
    them all — ⚠️ *a question is mostly not names, and a matcher that forgets that will name somebody in
    every sentence.*"""
    assert nearest_name(word, index) is None, f"{word!r} was read as a player"


@pytest.mark.parametrize("spoken", ["sala", "salar", "koonya", "isaac", "ottawa"])
def test_an_unclear_guess_is_refused(spoken, index):
    """⚠️⚠️ **The one that matters is `sala`.** It scores **0.89 against Salia** — a high ratio and the
    *wrong* player — and only its **0.09 margin** rejects it. ⭐ *A dropped name costs a question; a wrong
    one answers about somebody else* (ADR-154's direction, applied to speech).
    """
    assert nearest_name(spoken, index) is None


def test_the_margin_is_what_does_the_work(index, players):
    """⭐ Stated as a property rather than a number: there exist real names close enough that the ratio
    alone would accept the wrong one. ⚠️ *If this ever stops being true the margin is free to be dropped —
    and it will not stop being true while two players share a surname.*"""
    import difflib

    from src.analytics.names import _fold

    webs = sorted({p["web_name"] for p in players})
    folded = [_fold(w) for w in webs]
    close = [
        (a, b)
        for i, a in enumerate(folded)
        for b in folded[i + 1:]
        if a != b and difflib.SequenceMatcher(None, a, b).ratio() >= MIN_RATIO
    ]

    assert close, "no two real names are within the threshold — the margin would be unnecessary"


def test_exact_matching_is_untouched(index, players):
    """⭐⭐ The fuzzy pass runs **second, over leftovers only**, so a correctly spelled name behaves exactly
    as it always has — ⚠️ *a fallback that changes the path it falls back from is not a fallback.*"""
    by_id = {p["id"]: p["web_name"] for p in players}
    real = next(p["web_name"] for p in players if len(p["web_name"]) > 6 and p["web_name"].isalpha())

    hits = find_spoken_mentions(f"is {real} a good captain?", index)

    assert [by_id[pid] for pid in hits] == [real]


def test_a_whole_question_of_noise_names_nobody(index):
    for question in (
        "who should i captain?",
        "what should i do this week with my bench",
        "should i take a hit for a transfer",
        "when should i play my wildcard",
    ):
        assert find_spoken_mentions(question, index) == {}, f"{question!r} found a player in the words"


def test_two_mangled_names_in_one_question(index, players):
    """⭐ The shape the comparison lens needs (ADR-308): *"who should i captain, semenio or gvardial?"*"""
    by_id = {p["id"]: p["web_name"] for p in players}

    hits = find_spoken_mentions("who should i captain, semenio or gvardial?", index)

    assert sorted(by_id[pid] for pid in hits) == ["Gvardiol", "Semenyo"]


def test_the_thresholds_are_the_measured_ones():
    """⚠️ Pinned, because they were **measured, not chosen** — 16 manglings and 15 noise words — and a
    future edit that loosens them should have to say so here."""
    assert (MIN_RATIO, MIN_MARGIN) == (0.85, 0.15)
