# Chapter 10 — SQLite

**Badges:** 📖

*(Designed in Architecture v0.1 but not yet built. Will be filled in Sprint 001 /
US-003 when we persist players.)*

---

## Purpose

SQLite is a tiny database stored in a single local file. It's how the project will
store player and team data locally instead of re-fetching from the API every time.

---

## Why We Use It

Zero setup, single file, and part of Python's standard library (`sqlite3`) — chosen
in Architecture v0.1 §6. The schema is designed so a later move to PostgreSQL is a
swap of the storage layer, not a rewrite.

---

## Concepts (to expand when we build it)

- **Table:** rows and columns (we'll have `teams` and `players`).
- **Primary key:** a column that uniquely identifies a row (FPL `id`).
- **Upsert:** insert a row, or update it if it already exists — so re-running the
  fetch refreshes data instead of duplicating it.
- **`sqlite3`:** the stdlib module we'll use — no install needed.

---

## Status in this project

**Designed, not yet built.** The planned schema already lives in Architecture v0.1
§6 (`teams`, `players`). This chapter will hold the real `CREATE TABLE` statements,
the upsert query, and any gotchas once US-003 is implemented.

---

## Related Documents

- [Architecture v0.1 §6 (Data model)](../03_Architecture/Architecture.md)
- [Sprint 001 — US-003](../05_Sprints/Sprint1.md)
