# Chapter 12 — FastAPI

**Badges:** 📖

*(Deferred by ADR-002. Not started — will be filled in a later sprint when we serve
data over HTTP.)*

---

## Purpose

FastAPI is a Python framework for building web APIs — it would let the project serve
its data and analytics over HTTP (and later power a web UI).

---

## Why We Use It

Named in the Project Charter as the intended backend. **But not yet:** ADR-002
decided to display data in the console first and introduce FastAPI only once there
is data worth serving. The layered architecture means adding it later won't require
a rewrite.

---

## Concepts (to expand when we build it)

- **Route / endpoint:** a URL the app responds to.
- **Path & query parameters:** inputs passed in the URL.
- **JSON responses:** FastAPI returns Python objects as JSON automatically.
- **ASGI server (e.g. uvicorn):** what actually runs the app.

---

## Status in this project

**Deliberately deferred** (see [ADR-002](../06_Decisions/ADR-002-ui-approach.md)).
This chapter stays a stub until the sprint that introduces an HTTP interface.

---

## Related Documents

- [ADR-002 — UI Approach](../06_Decisions/ADR-002-ui-approach.md)
- [Architecture v0.1 §8 (Technology choices)](../03_Architecture/Architecture.md)
