"""Ask stops recommending chips you have already played (ADR-317).

⚠️⚠️⚠️ **`get_entry_history` has carried the list since ADR-234, and its own docstring says why:** *"a chip
advisor recommends a wildcard that has already been spent — which is not a rough edge, it is a wrong answer
delivered confidently."*

⭐⭐ The **Chips screen** passed a manager id and knew. `ask` had no field to carry one, so the same engine
was **blind on one path and sighted on the other** — and the blind one is the one that answers in words.
"""

from __future__ import annotations

import pytest

from src.ui.chips import render_chip_advice

#: What `chips_available` returns: played, still held, and could-not-check.
PLAYED = {"3xc": {"available": False, "played_in": 3},
          "bboost": {"available": True, "played_in": None},
          "freehit": {"available": True, "played_in": None},
          "wildcard": {"available": True, "played_in": None}}
UNKNOWN = {name: {"available": None, "played_in": None} for name in PLAYED}

#: ⭐ **Taken from the engine's own output**, not invented — a first attempt guessed the keys and every
#: renderer test died on `KeyError: 'player_xp'`. ⚠️ *A fixture that models less than reality confirms a
#: broken mechanism* (this project's own lesson, eighth time).
ADVICE = {
    "triple_captain": {"gameweek": 7, "player": {"web_name": "Haaland", "team": "MCI"},
                       "player_xp": 7.6, "extra_points": 7.6, "margin": 0.4},
    "bench_boost": {"gameweek": 10, "squad_total": 60.7, "bench_points": 8.7, "margin": 1.2},
    "free_hit": {"gameweek": 9, "xi_total": 49.2, "margin": 3.1},
    "wildcard": {"gain": 126.6, "overlap": 2, "squad_size": 15, "avg_xi": 52.4,
                 "gameweeks": [7, 8, 9], "window": [7, 9], "current": 475.3, "rebuilt": 677.9,
                 "idle_spend": 0.0, "margin": 0.0},
}


def test_a_spent_chip_is_marked() -> None:
    out = render_chip_advice(ADVICE, "TS", horizon=5, status=PLAYED)

    assert "ALREADY PLAYED" in out
    assert "GW3" in out


def test_only_the_spent_one_is_marked() -> None:
    """⚠️ A mark on every line is a mark that says nothing — ⭐ *and three of these four are still yours.*"""
    out = render_chip_advice(ADVICE, "TS", horizon=5, status=PLAYED)

    assert out.count("ALREADY PLAYED") == 1


def test_a_spent_chip_keeps_its_timing_advice() -> None:
    """⭐ *When it would have been best* is still true, and hiding the line would leave a reader wondering
    whether the app knew about the chip at all. ⚠️ The card is marked, **not removed** — the recommendation
    stops being an instruction."""
    out = render_chip_advice(ADVICE, "TS", horizon=5, status=PLAYED)

    assert "Triple Captain" in out
    assert "Haaland" in out, "the advice vanished instead of being marked"


@pytest.mark.parametrize("status", [UNKNOWN, None, {}])
def test_unknown_is_never_read_as_available(status) -> None:
    """⚠️⚠️⚠️ **The rule this whole feature turns on.** A failed lookup must print **nothing** — never a
    mark, and never an implication that a chip is in hand. ⭐ *"We could not check" and "you still hold it"
    are different facts, and only one of them is safe to act on* (ADR-234)."""
    out = render_chip_advice(ADVICE, "TS", horizon=5, status=status)

    assert "ALREADY PLAYED" not in out


def test_the_request_can_carry_a_manager_id() -> None:
    """⭐ The field whose absence was the whole bug."""
    from dataclasses import fields

    from src.service import AskRequest

    assert "manager_id" in {f.name for f in fields(AskRequest)}


def test_ask_marks_a_spent_chip_end_to_end(monkeypatch) -> None:
    """⚠️⚠️ **The path that was broken**, driven through the service with a stubbed FPL history — ⭐ *the
    renderer being right proves nothing if the status never reaches it.*"""
    from src.service import AskRequest, answers, ask_question
    from src.storage import Storage

    monkeypatch.setattr(
        answers, "_chip_status",
        lambda manager_id, gameweek: PLAYED if manager_id else UNKNOWN,
    )

    store = Storage()
    try:
        ids = [p["id"] for p in store.get_players()[:15]]
        marked = ask_question(AskRequest(question="whats the best chip strategy?", player_ids=ids,
                                         bench_ids=ids[-4:], manager_id=1013841), store=store)
        blind = ask_question(AskRequest(question="whats the best chip strategy?", player_ids=ids,
                                        bench_ids=ids[-4:]), store=store)
    finally:
        store.close()

    assert "ALREADY PLAYED" in (marked.get("detail") or ""), "Ask still recommends a spent chip"
    assert "ALREADY PLAYED" not in (blind.get("detail") or ""), "a caller with no id was told something"
