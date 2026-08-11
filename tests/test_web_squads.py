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


def test_parse_uploaded_accepts_a_valid_captain():
    sq = _valid_squad()
    sq["captain_id"] = sq["player_ids"][0]
    squad, err = web_squads.parse_uploaded(_Upload(sq))
    assert err is None and squad["captain_id"] == sq["player_ids"][0]


def test_parse_uploaded_rejects_a_captain_not_in_the_squad():
    sq = _valid_squad()
    sq["captain_id"] = 900_099                            # not one of the squad's players
    squad, err = web_squads.parse_uploaded(_Upload(sq))
    assert squad is None and "captain" in err


# --- apply_transfer (ADR-055): a validated, session-only swap ------------------------------------

def _market():
    """15 owned synthetic players (2/5/5/3, distinct clubs) + 2 unowned (a MID, a GK)."""
    players, i = [], 1
    for pos, n in {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}.items():
        for _ in range(n):
            players.append({"id": i, "web_name": f"P{i}", "position": pos, "price": 5.0, "team": f"T{i}"})
            i += 1
    owned = [p["id"] for p in players]                        # ids 1..15 (MIDs are 8..12)
    players.append({"id": 100, "web_name": "NewMid", "position": "MID", "price": 5.0, "team": "TX"})
    players.append({"id": 200, "web_name": "NewGK", "position": "GK", "price": 5.0, "team": "TY"})
    return players, owned


def _squad(owned, **extra):
    return {"name": "T", "player_ids": list(owned), "player_names": [f"P{i}" for i in owned],
            "bench_ids": [], "cost": 75.0, **extra}


def test_apply_transfer_applies_a_legal_swap():
    players, owned = _market()
    ok, issues, warning, new = web_squads.apply_transfer(_squad(owned), 8, 100, players)
    assert ok and not issues and warning is None
    assert 8 not in new["player_ids"] and 100 in new["player_ids"]
    assert new["cost"] == 75.0                                # 15 × £5.0m, same-price swap


def test_apply_transfer_refuses_an_illegal_swap():
    players, owned = _market()
    ok, issues, warning, new = web_squads.apply_transfer(_squad(owned), 8, 200, players)  # MID→GK
    assert not ok and new is None
    assert any("GK" in i for i in issues)                     # 3 GK / 4 MID — an illegal split


def test_apply_transfer_clears_a_transferred_out_captain():
    players, owned = _market()
    _, _, _, new = web_squads.apply_transfer(_squad(owned, captain_id=8), 8, 100, players)
    assert new["captain_id"] is None                          # the captain (8) left → cleared


def test_apply_transfer_keeps_a_captain_who_stays():
    players, owned = _market()
    _, _, _, new = web_squads.apply_transfer(_squad(owned, captain_id=9), 8, 100, players)
    assert new["captain_id"] == 9                             # 9 is untouched


def test_apply_transfer_warns_over_budget_but_still_applies():
    players, owned = _market()
    dear = next(p for p in players if p["id"] == 100)
    dear["price"] = 31.0                                      # 75 − 5 + 31 = £101m → £1 over
    ok, _, warning, new = web_squads.apply_transfer(_squad(owned), 8, 100, players)
    assert ok and new["cost"] == 101.0 and warning and "over" in warning


# --- apply_transfer_plan (US-354): accept a coordinated multi-transfer plan ----------------------

def _move(players, out_id, in_id, gain=1.0):
    """One plan move in the `suggest_transfer_plan` shape (the fields `apply_transfer_plan` reads)."""
    by_id = {p["id"]: p for p in players}
    o, i = by_id[out_id], by_id[in_id]
    return {"position": o["position"], "gain": gain,
            "out": {"id": o["id"], "web_name": o["web_name"], "price": o["price"]},
            "in": {"id": i["id"], "web_name": i["web_name"], "price": i["price"]}}


def test_apply_transfer_plan_applies_all_moves():
    players, owned = _market()                                # unowned: 100 (MID), 200 (GK)
    plan = [_move(players, 8, 100), _move(players, 1, 200)]   # MID 8→100 and GK 1→200 (both same-position)
    ok, issues, warning, new = web_squads.apply_transfer_plan(_squad(owned), plan, players)
    assert ok and not issues and warning is None
    assert 8 not in new["player_ids"] and 1 not in new["player_ids"]
    assert 100 in new["player_ids"] and 200 in new["player_ids"]
    assert new["cost"] == 75.0                                # 15 × £5.0m, same-price swaps


def test_apply_transfer_plan_refuses_an_illegal_result():
    players, owned = _market()
    plan = [_move(players, 8, 200)]                           # MID → GK → 3 GK / 4 MID, illegal
    ok, issues, warning, new = web_squads.apply_transfer_plan(_squad(owned), plan, players)
    assert not ok and new is None and any("GK" in i for i in issues)


def test_apply_transfer_plan_warns_over_budget_but_applies():
    players, owned = _market()
    next(p for p in players if p["id"] == 100)["price"] = 31.0   # 75 − 5 + 31 = £101m → £1 over
    ok, _, warning, new = web_squads.apply_transfer_plan(_squad(owned), [_move(players, 8, 100)], players)
    assert ok and new["cost"] == 101.0 and warning and "over" in warning


def test_apply_transfer_plan_clears_a_sold_captain():
    players, owned = _market()
    plan = [_move(players, 8, 100)]
    _, _, _, new = web_squads.apply_transfer_plan(_squad(owned, captain_id=8), plan, players)
    assert new["captain_id"] is None                          # the captain (8) was sold in the plan → cleared


# --- rename / set_bench (ADR-055) ----------------------------------------------------------------

def test_rename_sets_the_name():
    assert web_squads.rename({"name": "A", "player_ids": [1]}, "B")["name"] == "B"


def test_rename_blank_keeps_the_old_name():
    assert web_squads.rename({"name": "A", "player_ids": [1]}, "   ")["name"] == "A"   # never nameless


def test_set_bench_preserves_the_given_order():
    # ADR-079: bench_ids order IS the sub priority, so set_bench keeps the given order (not player_ids order)
    squad = {"player_ids": [5, 3, 9, 1], "bench_ids": []}
    assert web_squads.set_bench(squad, [9, 5])["bench_ids"] == [9, 5]


def test_move_bench_sub_reorders_outfield_and_keeps_the_gk_fixed():
    # ADR-079: swap an outfield sub in priority; the bench GK (keeper-only) is excluded + kept last
    by_id = {1: {"position": "GK"}, 2: {"position": "DEF"}, 3: {"position": "MID"}, 4: {"position": "FWD"}}
    squad = {"bench_ids": [2, 3, 4, 1]}                        # outfield priority 2,3,4 + GK 1
    assert web_squads.move_bench_sub(squad, 3, "up", by_id)["bench_ids"] == [3, 2, 4, 1]   # 3 (2nd) → 1st
    assert web_squads.move_bench_sub(squad, 2, "down", by_id)["bench_ids"] == [3, 2, 4, 1]  # 2 (1st) → 2nd
    assert web_squads.move_bench_sub(squad, 2, "up", by_id)["bench_ids"] == [2, 3, 4, 1]    # already 1st → no-op
    assert web_squads.move_bench_sub(squad, 1, "up", by_id)["bench_ids"] == [2, 3, 4, 1]    # GK excluded → no-op


# --- substitute (US-351): a lineup change (starter ↔ bench), legality-checked -----------------------

def _benched(owned):
    # bench a GK + one of each line → the XI is a legal 4-4-2 (GK 1, DEF 3-6, MID 8-11, FWD 13-14)
    return _squad(owned, bench_ids=[2, 7, 12, 15])            # GK2 · DEF7 · MID12 · FWD15


def test_substitute_swaps_a_legal_outfield_pair():
    players, owned = _market()
    by_id = {p["id"]: p for p in players}
    new, issues = web_squads.substitute(_benched(owned), 3, 7, by_id)   # DEF 3 (XI) ↔ DEF 7 (bench)
    assert not issues                                         # 4-4-2 preserved (still 4 DEF)
    assert new["bench_ids"] == [2, 3, 12, 15]                 # off (3) takes on's (7) bench/priority slot
    assert new["player_ids"] == owned                         # the 15 are unchanged — only the XI/bench split moved


def test_substitute_allows_a_legal_formation_change():
    players, owned = _market()
    by_id = {p["id"]: p for p in players}
    new, issues = web_squads.substitute(_benched(owned), 3, 12, by_id)  # DEF 3 off, MID 12 on → 3-5-2
    assert not issues and new["bench_ids"] == [2, 7, 3, 15]


def test_substitute_refuses_removing_the_only_gk():
    players, owned = _market()
    by_id = {p["id"]: p for p in players}
    _new, issues = web_squads.substitute(_benched(owned), 1, 7, by_id)  # GK 1 off, DEF 7 on → 0 GK
    assert any("GK" in i for i in issues)                     # illegal → the caller must not commit it


def test_substitute_allows_a_gk_for_gk_swap():
    players, owned = _market()
    by_id = {p["id"]: p for p in players}
    new, issues = web_squads.substitute(_benched(owned), 1, 2, by_id)   # GK 1 (XI) ↔ GK 2 (bench)
    assert not issues and 2 not in set(new["bench_ids"]) and 1 in set(new["bench_ids"])


def test_set_captain_accepts_an_owned_player():
    assert web_squads.set_captain({"player_ids": [1, 2, 3]}, 2)["captain_id"] == 2


def test_set_captain_rejects_a_non_owned_player():
    assert web_squads.set_captain({"player_ids": [1, 2, 3]}, 99)["captain_id"] is None


def test_captain_bonus_is_the_next_gw_double_only_for_a_starting_captain():
    # ADR-083: the captain adds one extra copy of their NEXT-GW xP — and only when in the XI
    by_gw = {7: {1: 5.9, 2: 6.3}, 8: {1: 2.0}}     # id 7 = captain, next GW (1) xP = 5.9
    assert web_squads.captain_bonus(7, {7, 8, 9}, by_gw, next_gw=1) == 5.9   # captain starting → next-GW xP
    assert web_squads.captain_bonus(7, {8, 9}, by_gw, next_gw=1) == 0.0      # captain benched → no bonus
    assert web_squads.captain_bonus(None, {7, 8}, by_gw, next_gw=1) == 0.0   # no captain set → 0
    assert web_squads.captain_bonus(7, {7, 8}, by_gw, next_gw=None) == 0.0   # no gameweeks → 0 (empty-safe)


# --- the guardrail: the web never writes squads to the *local* DB/files -------------------------
# (ADR-094 revises the ADR-053/054 invariant: the ONE deliberate server write is the opt-in,
#  secret-gated `cloud_store` squad save — a named exception, pinned as secret-gated below.)

def test_web_edges_never_call_squadstore_save():
    # local persistence is the user's downloaded file (ADR-054) — no web page may write squads.json
    for edge in ("web", "web_streamlit"):
        for path in (_ROOT / "src" / edge).rglob("*.py"):
            assert ".save(" not in path.read_text(), f"{path} must not write via SquadStore.save"


def test_cloud_store_squad_write_is_secret_gated(monkeypatch):
    # ADR-094: the cross-device store is OFF by default — without its secrets it can't read or write, so the
    # public deploy stays read-only until the owner opts in.
    from src.web_streamlit import cloud_store

    monkeypatch.delenv("FPL_STORE_URL", raising=False)
    monkeypatch.delenv("FPL_STORE_KEY", raising=False)
    assert cloud_store.is_configured() is False        # feature hidden by the UI when this is False
    assert cloud_store.load_squad("anyone") is None    # no read without secrets

    called = False

    def boom(*a, **k):                                 # any HTTP write here would be a leak
        nonlocal called
        called = True
        raise AssertionError("cloud_store must not POST without secrets")

    monkeypatch.setattr("requests.post", boom)
    try:
        cloud_store.save_squad("anyone", {"name": "x"})
    except RuntimeError:
        pass                                           # refused before any request — correct
    assert called is False


def test_web_edges_never_persist_chat_context():
    # ADR-091: the persisted chat context is local, single-user CLI state — the multi-user web keeps
    # per-session st.session_state (a key it happens to name "chat_context") and must never import or call
    # the shared-file store. Scan for the module import + its calls, not the session_state key.
    for edge in ("web", "web_streamlit"):
        for path in (_ROOT / "src" / edge).rglob("*.py"):
            text = path.read_text()
            assert "import chat_context" not in text and "from src.chat_context" not in text, \
                f"{path} must not import the CLI chat_context store"
            for call in ("chat_context.save_context", "chat_context.load_context", "chat_context.clear_context"):
                assert call not in text, f"{path} must not persist chat context ({call})"
