"""Cloud-squad state for the Streamlit edge (ADR-054, US-169).

Covers the `web_squads` helper (validate an uploaded squad), the committed **demo seed**
(`data/seed_squads.json` + the `SQUADS_PATH` fallback), and the **no-server-writes** guardrail — the web
edges must never call `SquadStore.save`, so persistence stays the user's own file.
"""

import json
import os
import pathlib

from src import config
from src.squads import SquadStore
from src.storage import Storage
from src.web_streamlit import squads as web_squads

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SEED = _ROOT / "data" / "seed_squads.json"


class _Upload:
    """A stand-in for Streamlit's UploadedFile — only `.getvalue()` is used by `parse_uploaded`."""

    def __init__(self, data):
        self._b = data.encode() if isinstance(data, str) else json.dumps(data).encode()

    def getvalue(self):
        return self._b


def _valid_squad():
    """A squad whose ids are guaranteed to exist in the *current* DB (not the seed's snapshot)."""
    store = Storage()
    try:
        ids = [p["id"] for p in store.get_players()][:15]
    finally:
        store.close()
    return {"player_ids": ids, "bench_ids": ids[11:], "cost": 100.0}


# --- the committed demo seed + the SQUADS_PATH fallback ------------------------------------------

def test_seed_squads_is_committed_and_loadable():
    assert _SEED.exists(), "the demo squad must be committed so cloud pages aren't empty"
    store = SquadStore(str(_SEED))
    names = store.names()
    assert names, "seed_squads.json must contain at least one demo squad"
    squad = store.load(names[0])
    assert 11 <= len(squad["player_ids"]) <= 15 and squad.get("cost")


def test_squads_path_resolves_to_an_existing_file():
    # live squads.json when present, else the committed demo — either way a real file exists
    assert os.path.exists(config.SQUADS_PATH)


def test_squads_path_falls_back_to_seed_when_live_absent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)                      # a fresh clone / cloud: no live squads.json
    resolved = "data/squads.json" if os.path.exists("data/squads.json") else "data/seed_squads.json"
    assert resolved == "data/seed_squads.json"


# --- parse_uploaded validation --------------------------------------------------------------------

def test_parse_uploaded_accepts_a_bare_squad_dict():
    squad, err = web_squads.parse_uploaded(_Upload(_valid_squad()))
    assert err is None and squad["name"] == "Uploaded squad"
    assert len(squad["player_ids"]) == 15


def test_parse_uploaded_accepts_a_named_squadstore_file():
    squad, err = web_squads.parse_uploaded(_Upload({"My team": _valid_squad()}))
    assert err is None and squad["name"] == "My team"     # the file key becomes the squad name


def test_parse_uploaded_rejects_non_json():
    squad, err = web_squads.parse_uploaded(_Upload("not json at all"))
    assert squad is None and "JSON" in err


def test_parse_uploaded_rejects_wrong_shape():
    squad, err = web_squads.parse_uploaded(_Upload({"foo": "bar", "baz": 1}))
    assert squad is None and "player_ids" in err


def test_parse_uploaded_rejects_a_bad_size():
    squad, err = web_squads.parse_uploaded(_Upload({"player_ids": [1, 2, 3]}))
    assert squad is None and "11" in err


def test_parse_uploaded_rejects_unknown_player_ids():
    squad, err = web_squads.parse_uploaded(_Upload({"player_ids": list(range(900_001, 900_016))}))
    assert squad is None and "current data" in err


# --- the guardrail: the web never writes squads server-side --------------------------------------

def test_web_edges_never_call_squadstore_save():
    # persistence is the user's downloaded file (ADR-054) — no web page may write squads.json
    for edge in ("web", "web_streamlit"):
        for path in (_ROOT / "src" / edge).rglob("*.py"):
            assert ".save(" not in path.read_text(), f"{path} must not write via SquadStore.save"
