# Architectural Decision Record: Saved / Persistent Squad (user state)

**Decision ID:** ADR-024
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (new persistence layer; reuses ADR-023 availability)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Everything stored so far is **reference data** — FPL players/teams/fixtures, cached in
`data/fpl.db` and *overwritten* on every `refresh`. A manager wants to **save their chosen
squad** and reload it later. That's a different kind of data — **the user's own state** — with
a different lifecycle: it must **survive a refresh** and must never be committed.

A probe confirmed the flow with no new dependency: save ids → JSON → load → re-price + flag
availability + note departures.

#### Decision Drivers
- **Persistence with the right lifecycle** — user state outlives the disposable cache.
- **Reload should be *useful*** — re-price + injuries, not a stale snapshot.
- **Keep it simple** — stdlib JSON, a small store, no accounts/sync.

---

### 💡 Decisions

**1. Store the picks, not the numbers.** Persist player **ids** + which are bench (plus the
saved cost and date for comparison). **Not** prices or availability — those are reference data
that goes stale; they're derived **fresh** from current data on load. That's what makes reload
valuable.

**2. A separate store — user state ≠ reference cache.**

```
data/fpl.db      ← reference cache (refreshed, disposable)     [gitignored: data/*.db]
data/squads.json ← user state (saved squads, persistent)       [gitignore: add data/squads.json]
```

A small `SquadStore` (JSON-backed, injectable path — like `Storage`) owns `data/squads.json`,
kept apart from `Storage` so the two lifecycles never mix. `refresh` only touches `fpl.db`, so
saved squads survive it. The file is **gitignored** (user data, not source).

**3. `--save` persists; `--load` reconstructs.** `squad … --save <name>` computes a squad as
normal and stores its ids + bench. `squad --load <name>` is a **display-only** mode — no
optimising — that rebuilds the squad from current data.

**4. On load — derive fresh.** Re-price against current prices (show *saved → now*), flag
availability (reusing ADR-023's `is_unavailable` / inline flags), and **note departed players**
(a saved id no longer in the game) rather than crashing or silently dropping them. An unknown
name errors and lists the saved names.

**Honest re-price note:** the re-priced "now" total covers only players still in the game — so
when someone has **departed**, the departed note explains any gap (their price is unknown). The
saved-vs-now comparison is cleanest when nobody has left.

**Not in scope:** multiple users / accounts; editing a saved squad in place; syncing to the
real FPL account/API.

---

### 🧪 Worked example (pressure-testing — run on real data)

Full cycle through a throwaway `squads.json`:

| Step | Result |
|---|---|
| Save | computed squad → 15 ids, cost £100.0m, written to `squads.json` |
| Load | reconstruct from current data — re-priced + availability re-checked |
| Departed | a saved id no longer in the game → noted (`[999999]`), not crashed |
| Re-price | saved £100.0m → now £94.0m (the £6m gap = the departed player here) |
| Unknown name | would error and list saved names (`['my-team']`) |

Confirms the round-trip, re-price, availability re-check, and departed handling before code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** A manager can save and reload their team; reload re-prices and flags injuries —
  "what's changed since I saved?". A clean new *user-state* layer, separate from the cache; no
  new dependency (stdlib JSON).
* **Negative / Trade-offs:** JSON is single-user and unversioned (fine for this tool). A departed
  player makes the saved-vs-now cost comparison approximate (noted). No editing-in-place (re-save
  to change).
* **Risks & Mitigations:**
  - *User data committed / wiped* → separate `data/squads.json`, gitignored; refresh only
    touches `fpl.db`.
  - *A player has left* → detect and note; don't crash or silently drop.
  - *Corrupt/missing file* → read → empty dict; atomic save.

---

### 🛠 Implementation & Migration
* **Components Affected:** a new `SquadStore` (`src/squads.py`, JSON), `config.SQUADS_PATH`, CLI
  (`squad --save` / `--load`), display (reuse the squad table + availability flags), `.gitignore`,
  Docs. `Storage` and `select_squad` are untouched.
* **Action Items:**
  - [x] Record the design + worked example + the re-price note (US-067)
  - [ ] `SquadStore` (save/load/names) + `--save` + gitignore (US-068)
  - [ ] `--load` reconstruct + re-price + availability + departed (US-069)
  - [ ] (Backlog) edit-in-place; multiple named slots UX; export to FPL

---

### 🔄 Review & Reconsideration
* **Review Date:** If users want many squads / richer management, or cross-device sync.
* **Triggers for Reconsideration:**
  - [ ] Need concurrent/multi-user state → a real store, not a JSON file.
  - [ ] Want to diff two saved squads, or edit one without re-computing.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-067 (this), US-068/069
- **External Docs:** [ADR-023 (availability)](./ADR-023-player-availability.md) · [ADR-008 (squad selector)](./ADR-008-squad-selector.md) · [Sprint 023](../05_Sprints/Sprint23.md)
