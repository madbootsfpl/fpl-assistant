"""The badges a player card carries (ADR-286).

⭐⭐ **These were computed already and the phone could not see them.** The web card has shown set-piece
duty and the ownership tier since ADR-081/US-289; the mobile card showed neither, because the `player`
endpoint never sent them. ⚠️ *A lens the engine already applies, withheld from one client, is not a
missing feature — it is the same product disagreeing with itself.*
"""

from __future__ import annotations

from src.service.answers import _badges


def test_a_taker_carries_every_duty_he_takes() -> None:
    badges = _badges(
        {"selected_by": 27.6, "penalties_order": 1, "corners_order": 1, "freekicks_order": 1}
    )

    assert [b["label"] for b in badges] == ["template", "pens", "corners", "FK"]
    assert [b["glyph"] for b in badges] == ["🟦", "⚽", "🚩", "🎯"]


def test_ownership_leads() -> None:
    # ⭐ The order the two answer in: *how many people own him* frames *what he does for them*.
    assert _badges({"selected_by": 27.6, "penalties_order": 1})[0]["label"] == "template"


def test_second_choice_is_not_a_taker() -> None:
    # ⚠️ Only `order == 1`. ⭐ *A badge that means "might take one" means nothing* — it is the first-choice
    # taker whose penalties are already in his projection.
    badges = _badges({"selected_by": 2.0, "penalties_order": 2, "corners_order": 3})

    assert [b["label"] for b in badges] == ["differential"]


def test_glyph_and_word_arrive_apart() -> None:
    """⚠️ Not the `"🟦 template"` string the tables use.

    ⭐ *A client that has to split a string to lay it out will one day split it differently* — and the
    phone draws the two at different sizes.
    """
    for badge in _badges({"selected_by": 70.0, "corners_order": 1}):
        assert set(badge) == {"glyph", "label"}
        assert " " not in badge["glyph"]
        assert badge["label"] and not badge["label"][0].isspace()


def test_an_unknown_ownership_yields_no_tier() -> None:
    # ⭐ Preseason has no ownership at all, and a card must not invent one.
    assert _badges({"selected_by": None, "penalties_order": 1}) == [
        {"glyph": "⚽", "label": "pens"}
    ]


def test_a_player_with_nothing_to_say_says_nothing() -> None:
    # ⚠️ An empty list, not a row of blanks — *the card must be able to render no badges at all.*
    assert _badges({}) == []


def test_the_tiers_come_from_crowd_not_a_second_copy() -> None:
    """⚠️ *A second copy of "who takes the corners" is a second answer to it.*"""
    from src.analytics.crowd import ownership_tier, set_piece_flags

    row = {"selected_by": 12.0, "freekicks_order": 1}
    rendered = [f"{b['glyph']} {b['label']}" for b in _badges(row)]

    assert rendered == [ownership_tier(row), *set_piece_flags(row)]
