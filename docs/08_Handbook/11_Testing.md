# Chapter 11 — Testing

**Badges:** 📖

*(Not started. Will be filled in Sprint 001 when we add the first `pytest` test for
the API client.)*

---

## Purpose

Testing means writing code that checks other code does what we expect —
automatically, and repeatably.

---

## Why We Use It

A learning goal in the Charter, and part of the Definition of Done ("tests pass
where appropriate"). Tests let us change code later with confidence that we haven't
broken what already worked.

---

## Concepts (to expand when we build it)

- **`pytest`:** the test framework chosen for this project.
- **Test function:** a small function that runs some code and `assert`s the result.
- **Fixtures / sample data:** using a *saved* API response so tests don't hit the
  live FPL API (avoids rate limits — Sprint 001 risk table).
- **Arrange → Act → Assert:** the shape of a good test.

---

## Status in this project

**Not yet used.** The first test (`tests/test_api_client.py`, run against a saved
sample response) is a Sprint 001 task. This chapter will show that first real test
and how to run the suite.

---

## Related Documents

- [Sprint 001 (Technical Tasks)](../05_Sprints/Sprint1.md)
- [Chapter 8 — APIs](./08_APIs.md)
