"""The committed API samples still describe what the API returns.

⭐⭐ **The samples exist because the audit's plan does not work yet.** §5 planned to *generate* the Flutter
models from FastAPI's OpenAPI schema — *"one contract, no hand-written duplicates."* Every route is typed
`-> dict`, so the schema advertises each response as an untyped object; a generator would emit
`Map<String, dynamic>` and every response model would be hand-written after all. Until responses are typed,
`spikes/018-flutter-read-slice/api-samples/` is what a Dart author reads.

⚠️ **Which makes them a liability without this test.** A sample nobody checks is worse than no sample: it
looks authoritative and ages silently, and the client written from it fails at runtime on a phone.

⭐ **Shape, never values.** The seed is refreshed constantly, so asserting `projected_xp == 258.9` would fail
every data update and teach everyone to regenerate without reading. Keys and types are what a model depends
on; a number moving is not a contract change and must not read as one.
"""

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "spikes" / "018-flutter-read-slice" / "api-samples"
sys.path.insert(0, str(ROOT / "spikes" / "018-flutter-read-slice"))


#: ⭐⭐⭐ **Fields that are MAPS, not records** — their keys are *data*, so they are not structure.
#:
#: ⚠️⚠️⚠️ This distinction is the whole reason CI could not go green. `shape` kept dict keys, so
#: `club_counts` — keyed by club code — described *which clubs this squad happens to own* rather than
#: `Map<String,int>`. The committed samples were generated from the live cache and CI has only the seed, so
#: **the sample said `BOU` and the response did not, for ever**: ⭐ *a guard whose correctness depends on the
#: data it happened to see is a guard that cannot pass twice.*
#:
#: ⭐ Collapsed to one representative entry, which is exactly what a Dart author needs — a map of club code
#: to kit is `Map<String, Kit>` no matter how many clubs are in it. ⚠️ A **record** (fixed keys a model
#: declares as fields) must NOT be listed here; losing those keys is the drift this file exists to catch.
_MAP_FIELDS = frozenset({
    "by_gameweek",    # gameweek number → value; the range moves every week
    "cells",          # gameweek number → value
    "club_counts",    # club code → how many of them you own
    "fixtures",       # club code → that club's run
    "kits",           # club code → kit colours
    "prices",         # player id → price
})

#: ⭐ The sentinel that stands in for "any key". Distinct from a real key, so a record can never match a map.
ANY_KEY = "<key>"


def shape(value, depth=0, field=""):
    """A value reduced to its structure: keys and types, no data.

    ⚠️ A list collapses to the shape of its **first** element and its emptiness. Comparing every element
    would make the test fail whenever a squad happened to contain one flagged player and not another —
    ⭐ *noise that trains a reader to regenerate rather than look.*

    ⚠️ A **map** (`_MAP_FIELDS`) collapses to a single `ANY_KEY` entry for the same reason, one level up:
    ⭐ *its keys are data, and data is what this function exists to throw away.*
    """
    if isinstance(value, dict):
        if field in _MAP_FIELDS:
            first = next(iter(sorted(value.items())), None)
            return {} if first is None else {ANY_KEY: shape(first[1], depth + 1, ANY_KEY)}
        return {k: shape(v, depth + 1, k) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return ["empty"] if not value else [shape(value[0], depth + 1, field)]
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if value is None:
        # ⚠️ Deliberately its own shape rather than folded into the type. A field that is sometimes null is
        # a nullable type in Dart, and a client that assumed otherwise crashes on the first flagged player.
        return "null"
    return type(value).__name__


def incompatible(sample, live, path=""):
    """Every place a sample's shape contradicts the response's — `[]` when the sample still describes it.

    ⭐⭐ **Why not `==`.** Two reasons, and the second is the one that matters:

    ⚠️ The failure it printed was unreadable — pytest's dict diff truncates with *"Omitting 10 identical
    items"* and names no path, so the message said something moved without saying what. ⭐ *A guard that
    cannot say where it failed gets regenerated rather than read*, which this file's own docstring warns
    against.

    ⚠️⚠️⚠️ **And `null` cannot be compared for equality across datasets.** `chance` is `int` for a flagged
    player and `null` for everyone else, so the sample says `int` and the seed-built response says `null`.
    ⭐⭐ *Nullability is not knowable from one dataset*, and the honest consequence is that this check must
    not pretend it is: `null` is compatible with any scalar, because **a field that is sometimes null needs
    `int?` in Dart either way** — which is what the shape already told the reader.

    ⚠️ The cost, stated: a field that becomes *permanently* null is no longer caught here. That is the right
    trade for a cross-dataset check — a key appearing, vanishing or changing from `str` to `int` still is,
    and those are the changes that break a Dart model.
    """
    here = path or "."
    if isinstance(sample, dict) and isinstance(live, dict):
        if set(sample) != set(live):
            gone, added = sorted(set(sample) - set(live)), sorted(set(live) - set(sample))
            return [(here, f"keys changed — gone from the response: {gone or '—'}; "
                           f"new in the response: {added or '—'}")]
        return [bad for k in sorted(sample)
                for bad in incompatible(sample[k], live[k], f"{path}.{k}")]
    if isinstance(sample, list) and isinstance(live, list):
        if bool(sample) != bool(live):
            return [(here, f"one is empty: sample={sample}, response={live}")]
        return incompatible(sample[0], live[0], f"{path}[]") if sample else []
    if sample == live or "null" in (sample, live):    # ⭐ nullable — see above
        return []
    return [(here, f"type changed: sample={sample!r}, response={live!r}")]


ENDPOINTS = ["analysis", "transfers", "captain", "gameweek-plan", "route", "build", "my-team",
             "players", "player", "compare", "ticker", "trending", "leagues", "league", "h2h", "worth-a-look", "worth-noticing", "player-dna"]


@pytest.fixture(scope="module")
def live():
    """Every endpoint's answer right now, against the same store the samples were built from."""
    from regenerate_samples import responses

    from src.storage import Storage
    store = Storage()
    try:
        return {k: json.loads(json.dumps(v)) for k, v in responses(store).items()}
    finally:
        store.close()


def test_every_endpoint_has_a_sample():
    """⭐ A seventh endpoint with no sample is the failure this catches — the Dart author would simply not
    know it exists, and nothing else would say so."""
    on_disk = {p.stem for p in SAMPLES.glob("*.json")}
    assert on_disk == set(ENDPOINTS), f"samples {sorted(on_disk)} != endpoints {sorted(ENDPOINTS)}"


@pytest.mark.parametrize("name", ENDPOINTS)
def test_the_sample_still_matches_what_the_endpoint_returns(name, live):
    """⚠️ **Regenerate, then read the diff** — do not regenerate to make this green. A changed shape means a
    Flutter model needs changing too, and this test is the only place that would have said so before a
    phone did."""
    stored = json.loads((SAMPLES / f"{name}.json").read_text())

    drift = incompatible(shape(stored), shape(live[name]))

    assert not drift, (
        f"the committed sample for `{name}` no longer describes the response:\n"
        + "\n".join(f"    {p:44} {why}" for p, why in drift)
        + "\nRun\n    venv/bin/python spikes/018-flutter-read-slice/regenerate_samples.py\n"
        "and check what moved — a Dart model probably has to move with it."
    )


@pytest.mark.parametrize("name", ENDPOINTS)
def test_a_sample_carries_no_integer_keys(name):
    """⭐ The samples are dumped through JSON exactly as the wire carries them, so `by_gameweek` appears
    keyed `"6"` — the shape a Dart author must actually parse (ADR-219).

    ⚠️⚠️ **An earlier version of this test asserted nothing.** It read
    `'"by_gameweek"' not in text or '": {\n' in text` — a hedge that happened to pass, and that went red
    only when a legitimately empty `by_gameweek` appeared. ⭐ *A hedge is not a weaker assertion, it is the
    absence of one* (ADR-180) — so this now walks the decoded structure and checks the keys themselves.
    """
    def gameweek_maps(value, found=None):
        found = [] if found is None else found
        if isinstance(value, dict):
            for key, inner in value.items():
                if key in {"by_gameweek", "by_gameweek_exact", "games_by_gameweek"} \
                        and isinstance(inner, dict):
                    found.append(inner)
                gameweek_maps(inner, found)
        elif isinstance(value, list):
            for inner in value:
                gameweek_maps(inner, found)
        return found

    text = (SAMPLES / f"{name}.json").read_text()
    # ⚠️ Parses at all — nothing hand-edited it into something Dart's `jsonDecode` would reject.
    decoded = json.loads(text)

    for weeks in gameweek_maps(decoded):
        for key in weeks:
            assert isinstance(key, str), f"{key!r} is a {type(key).__name__}, and JSON has no such key"
            assert key.isdigit(), (
                f"{key!r} is not a gameweek number. ⭐ A client parses these to int before sorting, "
                f"because as text \"10\" comes before \"6\"."
            )


# ⭐⭐ **A number written in prose is an untested claim** (ADR-212, learned on a README that said "121 ADRs"
# while the repo held 212). `players_view.dart` tells a reader the board is fetched once because it is
# small enough to be — a claim about a **payload**, made in a **comment**, three thousand lines from the
# payload. So the payload asserts it.
#
# ⚠️ The threshold is a **ceiling with room**, not today's figure: a test pinned to the exact size fails
# every time a player is added and teaches people to re-run it without reading. It fires when the response
# has changed *kind*, not when the league has changed.
PAYLOAD_CEILING_KB = 150


def _wire_kb(name):
    """What the client downloads — ⚠️ **not** `stat().st_size`.

    ⭐⭐ The committed sample is indented and key-sorted for a human to read, which makes it **76% larger
    than the response it documents** (169 KB on disk, 96 KB on the wire). Measuring the file and calling it
    the payload is how this test's first draft talked me into "correcting" a comment that had been right —
    *a measurement of the wrong artefact is confidently wrong, not noisily wrong.*
    """
    compact = json.dumps(json.loads((SAMPLES / f"{name}.json").read_text()), separators=(",", ":"))
    return len(compact.encode()) / 1024


def test_the_players_board_is_small_enough_to_fetch_whole():
    kb = _wire_kb("players")
    assert kb < PAYLOAD_CEILING_KB, (
        f"players.json is {kb:.0f} KB, over the {PAYLOAD_CEILING_KB} KB ceiling. The app downloads this "
        f"board in one go and filters on the device (ADR-236) — past a certain size that stops being the "
        f"right design, and the comment saying it is becomes wrong."
    )


def test_the_comment_quotes_the_size_the_payload_actually_is():
    """⭐ The claim and the thing it describes, compared — not two numbers that agree by luck.

    ⚠️ `players.json` is indented and sorted for a human reader; the wire carries neither. Comparing the
    file's size to a comment about the *download* would be comparing the wrong number, so this measures
    the compact encoding the client actually receives.
    """
    import re

    wire_kb = _wire_kb("players")
    text = (ROOT / "mobile" / "lib" / "players_view.dart").read_text()
    claimed = re.search(r"market is ~(\d+) ?KB", text)
    assert claimed, "players_view.dart no longer states the payload size — say it, or drop this test"
    stated = int(claimed.group(1))
    assert abs(stated - wire_kb) <= 20, (
        f"the comment says ~{stated} KB; the wire carries {wire_kb:.0f} KB. Update whichever is wrong."
    )


# ── the guard's own behaviour ─────────────────────────────────────────────────
#
# ⚠️⚠️ **Changing a guard without guarding the change is how a guard quietly stops guarding.** `shape` and
# `incompatible` were altered to make this file pass on **either** dataset (the live cache or the committed
# seed), and the risk in that change is over-tolerance: ⭐ *a comparison that accepts everything is green for
# the same reason a deleted test is.*

@pytest.mark.parametrize(
    ("what", "sample", "response"),
    [
        ("a record loses a key", {"a": 1, "b": 2}, {"a": 1}),
        ("a record gains a key", {"a": 1}, {"a": 1, "b": 2}),
        ("a scalar is retyped", {"a": "Haaland"}, {"a": 1}),
        # ⭐ The map rule drops KEYS, never the value type — `Map<String,int>` → `Map<String,String>` is
        # exactly the change a Dart model cannot survive.
        ("a map's value is retyped", {"club_counts": {"ARS": 1}}, {"club_counts": {"BOU": "x"}}),
        ("a list empties", {"a": [{"x": 1}]}, {"a": []}),
    ],
)
def test_real_drift_is_still_caught(what, sample, response):
    assert incompatible(shape(sample), shape(response)), f"{what} was not caught"


def test_a_map_can_never_match_a_record():
    """⭐ The sentinel earns its keep here: if `ANY_KEY` were a plausible key, a field that stopped being a
    map would slip through as *"the keys changed a bit"*."""
    as_map = shape({"club_counts": {"ARS": 1}})
    as_record = {"club_counts": {"ARS": "int"}}      # what a fixed-key record shapes to

    assert incompatible(as_map, as_record)


@pytest.mark.parametrize(
    ("what", "sample", "response"),
    [
        # ⚠️⚠️ The two the old `==` could not tolerate, and the reason CI could not pass with only the seed.
        ("a nullable field that is null in one dataset", {"chance": 7}, {"chance": None}),
        ("a map whose keys differ between datasets", {"kits": {"ARS": 1}}, {"kits": {"BOU": 2}}),
    ],
)
def test_dataset_noise_is_tolerated(what, sample, response):
    assert not incompatible(shape(sample), shape(response)), f"{what} should not be drift"


def test_the_failure_names_the_path():
    """⭐ *A guard that cannot say where it failed gets regenerated rather than read* — which is precisely
    what this file's own docstring warns against, and what the old `==` diff did."""
    drift = incompatible(shape({"squad": {"bench": [{"chance": 1}]}}),
                         shape({"squad": {"bench": [{"chance": "doubtful"}]}}))

    assert drift and drift[0][0] == ".squad.bench[].chance", drift
