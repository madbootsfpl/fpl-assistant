# Chapter 9 — JSON

**Badges:** 📖

*(Not started. Will be filled in Sprint 001 / US-002 when we parse FPL API
responses.)*

---

## Purpose

JSON (JavaScript Object Notation) is a structured text format for exchanging data.
The FPL API returns its data as JSON.

---

## Why We Use It

It's the format the FPL API speaks. We read JSON, pick out the fields we need, and
turn them into simple Python objects (Architecture §5, "Map" step).

---

## Concepts (to expand when we build it)

- **Objects `{}`** — key/value pairs (like a Python dict).
- **Arrays `[]`** — ordered lists (like a Python list).
- **Values** — strings, numbers, booleans, null, or nested objects/arrays.
- Python's built-in **`json`** module (stdlib) converts JSON text ↔ Python objects.

---

## Status in this project

**Not yet used in code.** When US-002 lands, this chapter will show a real trimmed
example of an FPL `elements[]` (player) object and how we map it to our `players`
table (Architecture §6).

---

## Related Documents

- [Chapter 8 — APIs](./08_APIs.md)
- [Chapter 10 — SQLite](./10_SQLite.md)
- [Architecture v0.1 §6 (Data model)](../03_Architecture/Architecture.md)
