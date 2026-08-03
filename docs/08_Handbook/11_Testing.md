# Chapter 11 — Testing

**Badges:** 📖 🧪 💻

---

## Purpose

Testing means writing code that checks other code does what we expect —
automatically, and repeatably.

---

## Why We Use It — and where it fits

Tests let us change code later with confidence that we haven't broken what already
worked. Just as important for this project: our tests run **offline**. They never
call the live FPL API, so they're fast, deterministic, and can't trip rate limits.

The trick is that our layered design *makes* things testable — because each layer
has one job and takes its inputs in, we can feed it fakes:

- the **client** is tested by replacing the network call with a saved sample;
- the **storage** is tested against a throwaway temporary database;
- the **display** is tested by passing in plain rows and checking the text.

---

## Concepts

- **`pytest`:** the test framework this project uses.
- **Test function:** a small function that runs some code and `assert`s the result.
- **Arrange → Act → Assert:** set up inputs, run the thing, check the outcome.
- **`monkeypatch`:** a pytest tool that temporarily swaps out a real call (e.g. the
  network) for a fake one.
- **`tmp_path`:** a pytest-provided temporary folder, so a test database never
  touches the real `data/fpl.db`.
- **Fixture (sample data):** a saved response (`tests/fixtures/...json`) used
  instead of a live call.

---

## Examples (from this project)

Testing the client without any network, by faking `requests.get`:

```python
def test_get_bootstrap_static_returns_parsed_json(monkeypatch):
    monkeypatch.setattr("src.api.client.requests.get", lambda *a, **k: FakeResponse(sample))
    data = FplClient().get_bootstrap_static()
    assert len(data["elements"]) == len(sample["elements"])
```

Testing storage against a temporary database and proving upsert is idempotent:

```python
def test_upsert_is_idempotent_and_refreshes_values(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_players([make_player(id=1, total_points=88)])
    store.save_players([make_player(id=1, total_points=120)])  # same id again
    assert store.count_players() == 1                    # no duplicate
    assert store.get_players()[0]["total_points"] == 120 # value refreshed
```

---

## Commands

```bash
pytest        # run all tests (verbose: pytest -v)
pytest -q     # quiet summary
```

Current suite: **9 tests** across client, models, storage and the table renderer.

---

## Common Mistakes

- **Tests that hit the real API** — slow, flaky, and rate-limitable. Fake the call.
- **Tests that write to the real database** — use `tmp_path` instead.
- **Testing too much at once** — one behaviour per test keeps failures easy to read.

---

## Best Practices

- Keep tests offline and independent.
- Test *behaviour* (the outcome), not internal wiring.
- A design that's hard to test is usually a design that's too tightly coupled —
  the test difficulty is a useful warning sign.

---

## Continuous Integration (Sprint 026)

The whole point of an **offline** test suite is that a machine can run it on every push.
`.github/workflows/ci.yml` (GitHub Actions) does exactly that: on each push/PR it installs
the deps, runs `ruff check .` (lint), then `pytest` — across Python 3.13 and 3.14. Because
the tests use fakes and an in-memory DB (no network), CI is fast and deterministic; a red
build means a real regression, not a flaky API. `.pre-commit-config.yaml` runs the same
lint locally on commit (opt-in: `pre-commit install`).

A judgement call worth remembering: the linter (`ruff`) is scoped to a **small, stable**
ruleset (errors, dead code, import order — `ruff.toml`), *not* every opinionated default.
`date.today()` is correct here, so we didn't enable the rule that dislikes it — a first CI
should catch real problems, not force churn on working code.

## Lessons Learned

- Testable code and good architecture are the same thing seen from two angles: our
  layers were easy to test *because* each one had a single, isolated job.
- An offline suite is what makes CI worth having — deterministic, fast, no flaky network.

---

## Related Documents

- [Sprint 001 (tests were part of US-002–US-004)](../05_Sprints/Sprint1.md)
- [Chapter 8 — APIs](./08_APIs.md) · [Chapter 10 — SQLite](./10_SQLite.md)
- Code: `tests/test_api_client.py`, `tests/test_storage.py`, `tests/test_table.py`
