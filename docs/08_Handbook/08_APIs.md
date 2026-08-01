# Chapter 8 — APIs

**Badges:** 📖

*(Not started. Will be filled in Sprint 001 / US-002 when we build the FPL API
client.)*

---

## Purpose

An API (Application Programming Interface) is a way for one program to ask another
program for information. This project uses the **official FPL API** to fetch player,
team and fixture data.

---

## Why We Use It

The FPL API is our **source of truth** for prices, points and fixtures
(see Architecture §2). Everything the app analyses starts as an API response.

---

## Concepts (to expand when we build it)

- **Endpoint:** a specific web address the API answers on, e.g.
  `/bootstrap-static/` (all players/teams) — see the Glossary.
- **HTTP GET:** the request type used to *read* data.
- **Response:** the data sent back, here as JSON (see [Chapter 9](./09_JSON.md)).
- **Rate limiting (429):** being blocked for asking too often — mitigated by caching
  to SQLite (Architecture §5).

---

## Status in this project

**Not yet used.** The API client is the next implementation step (US-002). Once
built, this chapter will hold the real endpoints, example requests/responses, the
fields we map, and any quirks discovered.

---

## Related Documents

- [Architecture v0.1](../03_Architecture/Architecture.md)
- [Sprint 001 — US-002](../05_Sprints/Sprint1.md)
- [Chapter 9 — JSON](./09_JSON.md)
