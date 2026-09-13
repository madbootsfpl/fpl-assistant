"""The set-piece xP term is **closed**, and these are the guards that keep it closed (ADR-096 → ADR-190).

ADR-096 priced a per-90 bonus for first-choice dead-ball takers, on the fallback/cold-start rate tiers only —
never on the trusted historical baseline, which already contains an established taker's penalties. That
exclusion was correct, and it is also what made the term impossible to calibrate: of **43** first-choice
duty-holders it could reach **9**, and `history_by_code` holds only completed seasons, so those 9 are fixed
for the season. At weight 0.5 it produced a ranking **0.99998** correlated with the unweighted one. §B0's bar
was not unmet, it was **unreachable** — at GW6, at GW10, at any n.

So it was removed rather than left at 0 forever, which is the furniture ADR-101's stopping rule exists to
prevent.

⚠️ **The distinction this file exists to protect: the price went, the signal did not.** Set-piece duty is
still shown to the reader — the ⚽/🚩/🎯 glyphs on the pitch, the Scout board — and a "tidy-up" that removed
the display along with the weight would be a real regression dressed as consistency. The last test here is
the one that catches that.
"""

import inspect
import pathlib

from src import config
from src.analytics.xp import decision_xp, player_xp

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_there_is_no_set_piece_weight():
    """Not 0 — **absent**. A weight sitting at 0 that can never be raised is exactly the dormant-forever
    furniture §B0's stopping rule forbids, and it reads to the next person as *"not calibrated yet"* rather
    than *"asked and answered"*."""
    assert not hasattr(config, "SET_PIECE_WEIGHT"), \
        "the set-piece weight was closed as unmeasurable (ADR-190) — a 0 here would re-open it by implication"


def test_the_term_is_gone_from_the_projection_signature():
    """`player_xp` no longer takes it, so no caller can re-enable the term by passing an argument. This is the
    ADR-181 shape one level out: an optional weight on a shared helper is a silent opt-in that would price a
    player differently with no error and no crash."""
    assert "set_piece_weight" not in inspect.signature(player_xp).parameters
    assert not (ROOT / "src" / "analytics" / "setpieces.py").exists()


def test_it_cannot_be_swept_again():
    """⚠️ A closed question left in the sweep registry is an invitation to re-run it until it passes, which is
    what §B0's *"once per checkpoint"* rule forbids. Closing the question means closing the harness entry."""
    from src.cli import _CALIBRATE_WEIGHTS

    assert "set_piece" not in _CALIBRATE_WEIGHTS
    assert set(_CALIBRATE_WEIGHTS) == {"form", "defcon", "clean_sheet"}


def test_nothing_in_the_core_still_prices_set_pieces():
    """A sweep for the claim rather than a check of the files I happened to think of — ADR-184's lesson, where
    a retired claim survived 14 days on six surfaces because two guards both checked the same two files."""
    offenders = []
    for f in (ROOT / "src").rglob("*.py"):
        text = f.read_text()
        for token in ("set_piece_bonus", "set_piece_weight", "SET_PIECE_WEIGHT"):
            # A comment explaining the closure is the point; a live reference is not.
            for i, line in enumerate(text.splitlines(), 1):
                if token in line and not line.lstrip().startswith("#"):
                    offenders.append(f"{f.relative_to(ROOT)}:{i} {line.strip()[:70]}")
    assert not offenders, f"the set-piece price is closed but is still referenced in code: {offenders}"


def test_the_duty_is_still_shown_even_though_it_is_not_priced():
    """⚠️ **The regression this file is really guarding.** Closing the *price* must not close the *signal*:
    who takes the penalties is a fact the reader wants and the app still knows. It reaches them through
    `crowd.SET_PIECES` — which never depended on the xP term — and through the Scout board, which is now the
    only surface either withheld signal appears on.

    The honest end state, and the same one ADR-188's clean-sheet term is heading for: **the app tells you the
    fact and declines to tell you what it is worth.**
    """
    from src.analytics.crowd import SET_PIECES, set_piece_glyphs

    assert [g for _f, g, _s, _l in SET_PIECES] == ["⚽", "🚩", "🎯"]
    taker = {"penalties_order": 1, "corners_order": None, "freekicks_order": None}
    assert [g for g, _label in set_piece_glyphs(taker)] == ["⚽"], \
        "a penalty taker must still be marked on the pitch"
    assert set_piece_glyphs({"penalties_order": 2, "corners_order": None, "freekicks_order": None}) == [], \
        "…and only the first-choice taker, as before"


def test_removing_the_term_did_not_change_a_single_projection():
    """It was dormant at 0, so its removal must be a **no-op on the numbers** — the same invariance every
    dormant weight is held to (ADR-041), asserted at the moment the weight disappears rather than before it.

    A dead-code removal that quietly moved xP would mean the code was never dead.
    """
    players = [{"id": 1, "code": 100, "team_id": 1, "points_per_game": 5.0, "minutes": 900, "status": "a",
                "ep_next": 4.0, "web_name": "P", "position": "MID", "team": "ARS", "price": 6.0,
                "penalties_order": 1, "corners_order": 1, "freekicks_order": 1, "form": 0.0,
                "total_points": 20, "selected_by": 5.0, "cost_change_event": 0, "transfers_in_event": 0,
                "xgc": 1.0, "clean_sheets": 0}]
    fixtures = [{"event": 1, "team_h": 1, "team_a": 2, "home": "ARS", "away": "BUR",
                 "team_h_difficulty": 3, "team_a_difficulty": 3, "kickoff_time": None,
                 "home_team_strength": None, "away_team_strength": None}]
    # A full-evidence, no-history player at neutral difficulty projects his points-per-game.
    assert player_xp(players, fixtures)[0]["xp"] == 5.0
    assert decision_xp(players, fixtures, {})[0]["xp"] == 5.0
