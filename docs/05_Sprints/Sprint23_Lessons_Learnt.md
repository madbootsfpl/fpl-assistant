# Lessons Learned

**Sprint:** Sprint 023 — Saved / Persistent Squad (user state)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let a manager save their chosen squad and reload it later — `squad --save <name>` persists the
picks; `squad --load <name>` reconstructs them against current data, re-prices, flags
availability, and notes anyone who's left the game. A new user-state layer, no new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Separating user state from a reference cache (different homes, lifecycles).
- Persisting the minimum (ids + names) and deriving the rest fresh.
- Mirroring an existing store's shape (`Storage`) for an instantly-testable new one.

### New Skills Acquired

- A JSON-backed store with atomic writes and corrupt-file tolerance.
- Reconstructing + re-pricing state against changing reference data.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- A genuinely new concept (user state) done cleanly — its own file, store, lifecycle; gitignored.
- Store the picks, derive the numbers — makes reload useful (re-price + injury flags).
- The killer use case works live: reload flags a since-injured pick and names a departure.
- Robust by design (atomic write, corrupt→empty, departed→noted); DoD held (23rd sprint).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| User data must survive a refresh + not be committed | It's not reference data | Own file `data/squads.json`, gitignored; `Storage` untouched |
| A departed player can't be looked up | Not in current data | Store the name at save time; note it by name on load |
| A partial write could corrupt the file | Non-atomic save | Write temp + `os.replace` (atomic) |
| Load display differs from the optimiser's | No objective/budget; needs saved→now | A dedicated `render_loaded_squad` (small dup — shared-renderer backlog) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| User state ≠ reference cache | Different data needs different homes and lifecycles |
| Persist the minimum | Store ids + names; recompute price/availability fresh |
| Atomic writes | temp + replace so a crash can't corrupt existing data |
| Mirror to test | An injectable-path store (like `Storage`) is trivially testable |

---

# Development Lessons 💻

- Keep user data out of the cache and out of git (its own file + a gitignore rule).
- Store the name of anything you'll need to show even after it disappears from the source.
- Reuse a helper (`_avail_flag`) across renderers; defer a full shared renderer to the backlog.

---

# AI Collaboration Lessons 🤖

- The gate settled the storage boundary before code — the one decision that mattered.
- A probe proved the round-trip + reload value (re-price, injury flag, departed) up front.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-024 | Saved squad: store picks (ids + names + bench), not prices/status; a separate JSON `SquadStore` (user state ≠ cache, gitignored); `--save`/`--load`; re-price + availability + departed on load | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

-

---

# Improvements for Next Sprint 🚀

## Project Improvements

- A shared table renderer; availability flags in the other views; combined defensive value —
  the remaining small/tech-debt closers, or declare the build phase complete.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate + 3-part DoD; re-check ClubElo while it's down.

---

# Key Commands Learned

```text
python app.py squad --full --save my-team   # persist your squad
python app.py squad --load my-team          # reload: re-priced + current availability + departures
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| User state | Data the *user* creates (their squad), vs FPL reference data |
| Reference cache | Cached FPL data, overwritten on refresh (disposable) |
| Atomic write | temp file + replace, so a crash can't corrupt the target |
| Derive, don't store | Recompute price/availability from current data on load |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-024 | Records the user-state boundary + store-picks-not-numbers |
| Handbook Ch 22 | Optimisation — now with the saving-a-squad / user-state section |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| User state vs reference data | | |
| JSON persistence / atomic writes | | |
| Deriving vs storing | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-067 Saved-squad design + ADR-024
- US-068 `SquadStore` + `squad --save`
- US-069 `squad --load` (re-price + availability + departed)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
