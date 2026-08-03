"""Tests for the SquadStore — the user-state (saved squads) layer (ADR-024)."""

from src.squads import SquadStore


def test_save_and_load_round_trips(tmp_path):
    store = SquadStore(path=str(tmp_path / "squads.json"))
    store.save("my-team", [1, 2, 3], bench_ids=[3], cost=100.0)

    loaded = store.load("my-team")
    assert loaded["player_ids"] == [1, 2, 3]
    assert loaded["bench_ids"] == [3]
    assert loaded["cost"] == 100.0
    assert "saved_at" in loaded          # the date is recorded


def test_save_stores_player_names_for_departed_display(tmp_path):
    store = SquadStore(path=str(tmp_path / "squads.json"))
    store.save("t", [1, 2], player_names=["Raya", "Saka"], bench_ids=[2], cost=50.0)
    assert store.load("t")["player_names"] == ["Raya", "Saka"]


def test_names_lists_saved_squads_sorted(tmp_path):
    store = SquadStore(path=str(tmp_path / "squads.json"))
    store.save("beta", [1])
    store.save("alpha", [2])
    assert store.names() == ["alpha", "beta"]


def test_load_unknown_name_returns_none(tmp_path):
    store = SquadStore(path=str(tmp_path / "squads.json"))
    assert store.load("nope") is None


def test_save_overwrites_same_name(tmp_path):
    store = SquadStore(path=str(tmp_path / "squads.json"))
    store.save("t", [1, 2])
    store.save("t", [3, 4])
    assert store.load("t")["player_ids"] == [3, 4]
    assert store.names() == ["t"]        # not duplicated


def test_missing_file_reads_as_empty(tmp_path):
    store = SquadStore(path=str(tmp_path / "does_not_exist.json"))
    assert store.names() == []
    assert store.load("anything") is None


def test_corrupt_file_reads_as_empty(tmp_path):
    path = tmp_path / "squads.json"
    path.write_text("{ not valid json")
    store = SquadStore(path=str(path))
    assert store.load("t") is None       # no crash
    # and a save still works (overwrites the garbage)
    store.save("t", [1])
    assert store.load("t")["player_ids"] == [1]
