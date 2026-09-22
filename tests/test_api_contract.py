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


def shape(value, depth=0):
    """A value reduced to its structure: keys and types, no data.

    ⚠️ A list collapses to the shape of its **first** element and its emptiness. Comparing every element
    would make the test fail whenever a squad happened to contain one flagged player and not another —
    ⭐ *noise that trains a reader to regenerate rather than look.*
    """
    if isinstance(value, dict):
        return {k: shape(v, depth + 1) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return ["empty"] if not value else [shape(value[0], depth + 1)]
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


ENDPOINTS = ["analysis", "transfers", "captain", "gameweek-plan", "route", "build", "my-team"]


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
    assert shape(stored) == shape(live[name]), (
        f"the committed sample for `{name}` no longer describes the response. Run\n"
        f"    venv/bin/python spikes/018-flutter-read-slice/regenerate_samples.py\n"
        f"and check what moved — a Dart model probably has to move with it."
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
