# Lessons Learned

**Sprint:** Sprint 024 — Shared Table Renderer (tech-debt closer)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Extract one shared renderer for the five ranking views (`table`, `xg`, `overperf`, `defcon`,
`cleansheet`) — a `Col` spec + `render_rows` — paying down ~271 lines of near-duplicate table
code, with **byte-identical output**. A pure refactor; the existing tests pin it.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Refactoring safely behind a frozen baseline (capture → migrate → diff byte-for-byte).
- Keeping existing tests untouched as the definition of a clean refactor.
- Pushing variation to the edge so the shared core stays trivial.

### New Skills Acquired

- Designing a small declarative spec (`Col`) + one renderer to replace copy-paste.
- Proving format equivalence up front (`format(v,'.1f')` + pad == `{v:>6.1f}`).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **Provably output-preserving, not hopefully.** The one risk — a single changed byte — was
  retired *before* code (format-then-pad proven identical) and again at the gate (a prototype
  diffed against the real xg/defcon/overperf), then per-migration against frozen baselines.
- **The right seam:** `fmt` produces the finished cell string; `render_rows` only pads. Every
  quirk (ellipsis, `.2f`, signed `+.1f`, overperf's two-section/no-divider layout) stayed in the
  view; two flags (`rank`, `divider`) covered all the structural variation.
- **28 view tests passed unedited** — the definition of a clean refactor. Suite 220 → 227.
- DoD held for the 24th sprint: byte-diff + tests + live smoke on every view.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Output must not change by one byte | Five hand-tuned f-string tables | Prove format-then-pad == combined spec; diff every view vs a frozen baseline |
| Views differ (widths, truncation, formats) | Grown independently | Put the difference in a per-column `fmt`; the renderer only pads |
| `overperf` has two sections + no divider | A different layout | `render_rows(..., rank=True, divider=False)` per section; rank restarts each call |
| Line count went *up*, not down | The shared module is heavily documented | Recorded honestly — the win is one edit-point, not fewer lines |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Safe refactor | Freeze a baseline, migrate, diff byte-for-byte; keep tests untouched |
| The seam | Format at the edge (`fmt` per column); pad in the core — quirks never reach the core |
| Format equivalence | `format(v,'.1f')` then `{s:>6}` is identical to `{v:>6.1f}` (plain/neg/signed) |
| The right metric | Maintainability (one place to change), not raw line count |

---

# Development Lessons 💻

- A refactor that changes output — or needs its tests edited — isn't a refactor.
- Declarative beats copy-paste: a view becomes a list of `Col`s + a title + a footer.
- Be honest when a stated success criterion isn't met (the line count) — record it, don't spin it.

---

# AI Collaboration Lessons 🤖

- The gate (ADR-025) settled the one thing that mattered — *is this provably output-preserving?* —
  with a worked example against the real functions, before any migration.
- Baselines + untouched tests let each step be checked mechanically, not by eye alone.

### Notes _(for Tony)_

- I think we are closing in on completing Phase 1 and should make a decision on declaring that.
- We do need to compare achievements versus the original Roadmap, update roadmap to show actual phase 1 complete and push any remaining, viable items into future phases or nice to have backlog.
- lets revie wif there is anything else to do before closing phase 1.

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-025 | Shared table renderer: a `Col` spec + `render_rows(rows, columns, rank=, divider=)`; the *fmt-formats / render_rows-only-pads* seam keeps output byte-identical; scope = the five ranking views; rejected a general table framework (keep widths explicit) | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

- How impressive Claude Code is - remarkable

---

# Improvements for Next Sprint 🚀

## Project Improvements

- The build phase is feature-complete and the tech debt is paid down. Next: open a new phase
  (a web view per ADR-002; live current-season data) or take the remaining small closers
  (availability flags in the ranking views; a shared *squad* renderer).

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate + 3-part DoD; re-check ClubElo while it's down (502s as of 2026-08-03).

---

# Key Commands Learned

```text
# a view is now just its columns + render_rows:
#   _COLS = [Col("Player", 17, "<", lambda r: str(r["web_name"])[:17]), Col("xGI", 6, ">", ...)]
#   lines = render_rows(rows[:limit], _COLS, rank=True)
python app.py xg --limit 5        # unchanged output, now via the shared renderer
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Output-preserving refactor | Changes structure, not a single byte of output (tests pin it) |
| Column spec (`Col`) | Declarative header + width + alignment + cell formatter for one column |
| The seam | Where responsibility splits: `fmt` formats the cell, `render_rows` only pads |
| Frozen baseline | Captured pre-change output, diffed after, to prove nothing changed |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-025 | Records the renderer design + the output-preserving seam |
| Handbook Ch 20 | CLIs — now with the shared-renderer / safe-refactor lesson |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Refactoring safely (baseline + diff) | | |
| Declarative specs vs copy-paste | | |
| Choosing the right success metric | | |
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

- US-070 Shared-renderer design + ADR-025 (gate)
- US-071 `ui/_table.py` (`Col` + `render_rows`) + migrate `table` + `xg`
- US-072 Migrate `overperf` + `defcon` + `cleansheet`

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
