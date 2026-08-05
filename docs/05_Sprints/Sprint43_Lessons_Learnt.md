# Lessons Learned

**Sprint:** Sprint 043 — The differential archetype (ownership data + a ≤5% constraint)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Finish the archetype feature with the **differential**: ingest ownership (`selected_by_percent`), define
it so a differential build actually tilts the squad (≤5% owned, pinned on data), add a
`min_differentials` constraint, and surface it (`squad --full --differential N` + NL). No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Pinning a threshold on what *changes the output*, not a textbook heuristic.
- Adding a new datum by mirroring an existing field's ingest path end-to-end.
- Reusing a min-count ILP pattern for a new attribute (ownership).

### New Skills Acquired

- An ownership-based differential constraint on a squad optimiser.
- A walk-through that surfaced the definition flaw before code.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **The walk-through changed the definition — and saved a silent no-op.** ≤10% would have left "≥3
  differentials" already satisfied (the optimal squad has 6 low-owned enablers); the probe → ≤5%
  (optimal has 2) → it bites.
- **The ingest was a copy** — `selected_by` mirrored `chance` line-for-line (model + storage +
  migration + `SELECT *`).
- **The constraint was one ILP line**, combinable with `--cheap`/`--premium`, byte-identical when absent.
- **The tilt is honest and visible** — `--differential 5` trades 305.8 → 301.7 xP for 2 → 5
  off-template picks.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| ≤10% is a silent no-op | The optimal squad already has 6 low-owned enablers | Pin ≤5% (optimal has 2) so "≥3 differentials" bites |
| Ownership wasn't stored | Never ingested | Add `selected_by` (a `chance`-style ingest) |
| Differential = a new attribute, not price | The bands were price-only | A separate `min_differentials` count + a `_selected_by` accessor |
| Rows are sqlite Rows or dicts | `.get` differs | A try/except `_selected_by` accessor |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Pin on the output | A threshold is right only if it *changes* the squad — ≤10% looked right, did nothing |
| Cheap new datum | Mirror an existing field's path (model → storage → migration → SELECT) |
| Objective does quality | Force a *count*; the xP objective picks the *best* qualifiers |
| Generalise the pattern | The ADR-043 min-count constraint took ownership with one line |
| Walk through first | Explaining the design surfaced the definition flaw before any code |

---

# Development Lessons 💻

- Validate a definition by asking "does the output actually change?" — not just "is it a reasonable rule?".
- Adding a column is low-risk when every step copies a proven one.
- Keep the interesting failures (constraint combinations) in mind; the single-constraint path is easy.

---

# AI Collaboration Lessons 🤖

- The "walk me through it first" turned into the sprint's pivot — the probe + a shared decision beat a
  confidently-wrong default (≤10%).
- The gate probe pinned the threshold *and* the ILP insertion point, so the build was mechanical.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-044 | The differential archetype: ingest `selected_by`; a differential = `selected_by_percent ≤ 5%` (tunable, no floor — the xP objective picks the best qualifiers); `select_squad(min_differentials=N)`; CLI `--differential N` + NL; combinable; over-ask/no-data → a clear message | Accepted |

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

- Per-position / effective-ownership differentials; ownership *trends*. A build-narration prompt polish
  (reduce ⚠, from Sprint 042). (GW1) the full Phase-5 xMins. Or the web UI.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the walk-through-before-gate habit; keep the 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --full --differential 3                          # ≥3 off-template picks (≤5% owned)
python app.py squad --full --cheap 3 --premium 1 --differential 2    # the full archetype trio
python app.py ask "build me a squad with 3 differentials"
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Differential | A low-owned pick (≤5% here) taken instead of the popular template option |
| selected_by | A player's ownership % (from `selected_by_percent`) |
| Template | The highly-owned players most managers have; a differential deliberately avoids them |
| Tilt cost | The small xP given up to gain off-template exposure |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-044 | The differential definition + the ownership ingest |
| ADR-043 | The min-count constraint pattern this reuses |
| ADR-023 | The `chance` field whose ingest path this mirrored |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Pinning a threshold on data | | |
| Ingesting a new field | | |
| ILP constraints | | |
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

- US-127 Gate — ADR-044 (the differential; ≤5% pinned via a walk-through)
- US-128 Ownership ingest (`selected_by`, a `chance`-style mirror)
- US-129 `min_differentials` constraint + `--differential N` + NL wiring

**Stories Carried Forward:**

- None (the archetype trio — low-cost / premium / differential — is complete)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
