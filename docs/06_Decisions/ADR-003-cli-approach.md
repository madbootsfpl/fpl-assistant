# Architectural Decision Record: Command-Line Interface Approach

**Decision ID:** ADR-003
**Date:** 2026-08-01
**Status:** Accepted
**Superseded By / Replaces:** N/A
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Sprint 001 produced an app that ran one fixed pipeline (fetch → store → display) on
every launch. Sprint 002 needs the app to do *different* things on demand — refresh
data, view a table, search, filter. That requires an interaction layer: a way for
the user to drive the app. We must decide how that interface works and where its
code lives, before building the four commands on top of it (US-006–US-008).

#### Decision Drivers (Key Requirements)
- **Console-first** (per [ADR-002](./ADR-002-ui-approach.md)) — no web UI yet.
- **Keep it simple / no unnecessary dependencies.**
- **Testable and scriptable** — commands should be easy to test offline.
- **Thin entry point** — keep modules small; don't bloat `app.py`.

---

### 💡 Options Considered

#### Option 1: argparse subcommands, in a dedicated `src/cli.py` *(Chosen)*
* **Description:** Python's built-in `argparse` with subcommands
  (`refresh`, `table`, `search`, `filter`). The parser and handlers live in
  `src/cli.py`; `app.py` becomes a ~3-line launcher.
* **Pros:**
  - ✅ Standard library — no new dependency to add or learn
  - ✅ Commands are easy to test (parse an arg list, assert the shape) and to script
  - ✅ Fits console-first; `app.py` stays a thin entry point
* **Cons:**
  - ❌ Slightly more verbose than a third-party library

#### Option 2: `click` (third-party CLI library)
* **Pros:** ✅ Nicer ergonomics / decorators
* **Cons:** ❌ Adds a dependency and a new thing to learn for little gain at this scale

#### Option 3: Interactive menu / prompt loop
* **Pros:** ✅ Feels "app-like"
* **Cons:** ❌ Harder to test and script; more complex than a single-user tool needs

---

### 🎯 Decision & Justification

**Chosen Option:** Option 1 — `argparse` subcommands in `src/cli.py`.

**Reasoning:** It meets every driver — stdlib (no dependency), console-first,
testable, and it keeps `app.py` thin by moving routing into a small interaction
layer. The alternatives add either a dependency (`click`) or complexity (menu loop)
without a benefit this project needs yet.

**Related placement decision:** analytics (starting with Points-per-£m in US-007)
will live in the `src/analytics/` package. The CLI calls analytics/storage; it
contains no FPL logic itself.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** New capabilities are added by adding a command handler at the edge,
  leaving the client/storage/display layers untouched. `python app.py` now shows
  help; commands drive behaviour.
* **Negative / Trade-offs:** `python app.py` no longer auto-fetches — the user must
  run `refresh` explicitly (this is intended: viewing shouldn't force a network call).
* **Risks & Mitigations:**
  - *Risk:* CLI grows complex. *Mitigation:* keep handlers thin; logic stays in layers.

---

### 🛠 Implementation & Migration
* **Components Affected:** Architecture (new interaction + analytics layers), Code, Docs
* **Action Items:**
  - [x] Add `src/cli.py`; slim `app.py` to a launcher (US-005)
  - [x] `table` command working; `refresh`/`search`/`filter` stubbed for their stories
  - [ ] Implement `refresh` (US-006), Points-per-£m (US-007), search & filter (US-008)

---

### 🔄 Review & Reconsideration
* **Review Date:** If/when a non-console interface is introduced
* **Triggers for Reconsideration:**
  - [ ] A web UI / FastAPI is introduced (would revisit ADR-002 first)
  - [ ] The command set grows large enough that argparse becomes unwieldy

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-005 (this), US-006/007/008 (build on it)
- **External Docs:** [ADR-002](./ADR-002-ui-approach.md) · [Architecture v0.1](../03_Architecture/Architecture.md) · [Sprint 002](../05_Sprints/Sprint2.md)
