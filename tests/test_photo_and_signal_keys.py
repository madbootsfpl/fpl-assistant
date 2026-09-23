"""A face on the card, and the badge's keys (ADR-255, ADR-256).

⭐⭐ **Two small things that had each been parked for the same wrong reason** — "that would need another
round trip". Neither does: a photo URL is derived from a code the app already holds, and the signal keys
cost ~50ms on a sweep the server was already capable of.
"""

import re
from pathlib import Path

import pytest

from src import service
from src.kits import photo_url
from src.service import answers
from src.storage import Storage

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def store():
    s = Storage()
    yield s
    s.close()


@pytest.fixture(scope="module")
def squad(store):
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in store.get_players():
        if need.get(p["position"], 0) and per_club.get(p["team"], 0) < 3 and len(picked) < 15:
            picked.append(p["id"])
            need[p["position"]] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return picked


# ── the photo ────────────────────────────────────────────────────────────────────────────────────

def test_a_photo_is_keyed_by_code_not_by_id(store):
    """⚠️⚠️ **`code` is stable across seasons; `id` restarts every August** (ADR-201). A photo built from
    the id would point at whoever inherited the number — ⭐ *and it would look entirely fine.*"""
    player = next(p for p in store.get_players() if p["minutes"])
    assert str(player["code"]) in photo_url(player["code"])
    assert photo_url(player["code"]) != photo_url(player["id"]), (
        "code and id produce the same URL for this player, so this test cannot tell them apart"
    )


def test_a_missing_code_gives_no_url_rather_than_a_broken_one():
    """⭐ Empty, so the client shows initials. A URL with `None` in it renders as a broken image, and a
    broken image reads as *"this app is broken"* rather than *"no photo"*."""
    assert photo_url(None) == ""
    assert photo_url(0) == ""


def test_the_named_cards_carry_a_face_and_the_pitch_does_not(store, squad):
    """⚠️⚠️ **ADR-084 chose the club kit on the pitch on purpose**: FPL's photo CDN lags a transfer by
    weeks while the kit updates instantly, so a just-transferred player would sit there wearing his old
    club's face. ⭐ *On a card his name is beside him and the staleness is a curiosity; on the pitch it is
    the app being visibly wrong about your team.*
    """
    card = service.player(service.PlayerRequest(player_id=squad[0], horizon=1), store=store)
    dna = service.player_dna(service.PlayerDnaRequest(player_id=squad[0]), store=store)
    assert card["photo"].startswith("https://")
    assert dna["photo"] == card["photo"]

    real = answers.fetch_manager_team
    answers.fetch_manager_team = lambda entry_id, players: (
        {"name": "X", "player_ids": squad, "bench_ids": squad[-4:],
         "captain_id": squad[0], "vice_captain_id": squad[1]}, "")
    try:
        team = service.my_team(service.MyTeamRequest(manager_id=1, horizon=1), store=store)
    finally:
        answers.fetch_manager_team = real
    assert "photo" not in team, "the pitch payload carries a mugshot — ADR-084 says the kit, not the face"
    for player in team["analysis"]["xi"]:
        assert "photo" not in player


def test_the_web_re_exports_rather_than_redefines():
    """⭐ `photo_url` moved out of the Streamlit package so the API could reach it. ⚠️ *The shirt template
    lost its `-66` in a move like this one and every kit on the pitch broke*, so this asserts the web's
    name is the **same object**."""
    from src.web_streamlit import badges

    assert badges.photo_url is photo_url


# ── the badge's keys ─────────────────────────────────────────────────────────────────────────────

def test_my_team_carries_the_signal_keys_not_the_signals(store, squad):
    """⭐⭐⭐ **The badge is a count, and a count does not need the things it counted.**

    ⚠️ Sending the signals themselves would put a full sweep's worth of player summaries on the one screen
    that has to be fastest.
    """
    real = answers.fetch_manager_team
    answers.fetch_manager_team = lambda entry_id, players: (
        {"name": "X", "player_ids": squad, "bench_ids": squad[-4:],
         "captain_id": squad[0], "vice_captain_id": squad[1]}, "")
    try:
        team = service.my_team(service.MyTeamRequest(manager_id=1, horizon=1), store=store)
    finally:
        answers.fetch_manager_team = real

    keys = team["signal_keys"]
    assert isinstance(keys, list)
    for key in keys:
        assert isinstance(key, str) and ":" in key, f"not a stable key: {key!r}"


def test_the_keys_are_the_same_ones_the_signals_screen_uses(store, squad):
    """⚠️⚠️ **The whole mechanism depends on these matching.** The device marks keys seen when the Signals
    screen renders them; if the pitch sent a differently-built key, the badge would never clear. ⭐ *Two
    generators for one identity is a badge that lies forever and never errors.*
    """
    real = answers.fetch_manager_team
    answers.fetch_manager_team = lambda entry_id, players: (
        {"name": "X", "player_ids": squad, "bench_ids": squad[-4:],
         "captain_id": squad[0], "vice_captain_id": squad[1]}, "")
    try:
        team = service.my_team(service.MyTeamRequest(manager_id=1, horizon=1), store=store)
    finally:
        answers.fetch_manager_team = real

    screen = service.signals(service.SignalsRequest(player_ids=squad, horizon=1), store=store)
    assert set(team["signal_keys"]) == {s["key"] for s in screen["signals"]}


def test_the_device_owns_what_is_new_and_the_server_does_not():
    """⭐ The server says what **exists**; only the device knows what is **new** — ADR-232's split, reused.

    ⚠️ Asserted as an absence: a `new_count` or `unseen` field would mean the server had guessed when you
    last looked, and it cannot.
    """
    main = (ROOT / "mobile" / "lib" / "main.dart").read_text()
    assert "_seenKeys" in main, "the device no longer keeps its own memory of what it has shown"

    answers_src = (ROOT / "src" / "service" / "answers.py").read_text()
    assert not re.search(r'"(new_signals|unseen|signal_count)"', answers_src), (
        "the service is claiming to know what the reader has already seen"
    )
