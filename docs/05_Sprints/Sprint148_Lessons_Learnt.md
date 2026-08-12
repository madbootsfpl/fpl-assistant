# Lessons Learned

**Sprint:** Sprint 148 — MADBOOTS vocabulary (Edge · Risk · Radar)

**Dates:** 2026-08-12

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Turn the last generic analytics labels into a small MADBOOTS lexicon (ADR-107) — **clean, not gimmicky**.
Adopt **Edge** (the reasons heading, was "Why") + **Risk** (reconcile "Risks"→"Risk") in the explanation block,
and **🎯 Radar** (was "Target by fixtures") for players-to-watch. **Display-only** — no analytics/`decision_xp`/
code identifiers. "AI Tips" and "Captain" left as-is (owner's call; "Pick" deferred).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Scope from the real surfaces, then verify the scope is complete.** An Explore pass mapped the labels — but it
  found only *two* of the *four* places the explanation block renders. Building it (and grepping `src/`) surfaced the
  other two. The lesson: a planning map is a starting point, not a guarantee; confirm "everywhere it appears" against
  the code before calling a label-sweep done.
- **Gate a display change with an ADR anyway.** It's "just labels", but the *principle* (clean, not gimmicky; a
  rename must be at least as clear) is the reusable decision — ADR-107 is now the reference for future brand words,
  with "Pick"'s deferral as the worked example.

### New Skills Acquired

- **One output, one word.** `gameweek.py` renders the plan-summary through the shared explanation block *and* had its
  own inline `Why:` labels — so renaming only the block would have made the *same* AI Tips output read both "Edge"
  and "Why". A label rename has to follow the concept across every renderer that emits it, not just the canonical one.
- **Display string vs grounding key.** The `explain` output's heading ("Why"→"Edge") is display; the `facts["why"]`
  dict key is a grounding identifier that `verify_grounding` checks — a code identifier, left untouched. Renaming the
  first without the second is correct *because* grounding matches fact **values**, not keys.

---

# What Went Well ✅

- **Tiny, surgical diffs** — four label swaps + one caption + the Help/nav mentions; no logic touched.
- **Green throughout** — 972 tests stayed green (assertions updated to the new wording); ruff clean.
- **Consistency caught** — the four-surface sweep + the `Risks`→`Risk` reconciliation removed a pre-existing
  inconsistency (the captain card said "Risks", everything else "Risk").

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The planning map missed 2 of 4 surfaces | Explore focused on the web + `explain.py`; `ui/captain.py` + `ui/gameweek.py` also render the block | Grepped `src/` for the heading strings before finishing; swept all four |
| A rename that half-touches one output | `gameweek.py` mixes the shared block + its own inline `Why:` | Renamed the inline labels too so the AI Tips output reads "Edge" consistently (owner OK'd) |
| Don't rename code by accident | The tab string is also a branch condition; `facts["why"]` is a grounding key | Renamed display strings only; left `render_ai_tips`, `target_by_fixtures`, the `target_*` keys, the branch strings, and the fact-keys |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Label sweeps | Follow the *concept* across every renderer; a shared block can be duplicated in CLI + web + a plan view |
| Display vs code | Grounding verifies fact **values**, so a display heading can be renamed without touching the `facts` key |
| ADR for a "small" change | The value is pinning the *principle* (clean, not gimmicky), not the diff — future brand words reference it |

---

# Development Lessons 💻

- After a label sweep, `grep src/ tests/` for the old string — the safety net that caught the internal comment and
  the AppTest assertion still on "Target by fixtures".
- Reconcile inconsistencies while you're in there — "Risks"/"Risk" had drifted; one word now.

---

# AI Collaboration Lessons 🤖

- Display-only, so the read-only invariant and every sanctioned server write are unchanged; no engine/xP change.
  The brand vocabulary is a *light signature* (Edge/Risk/Radar), not "MadBoots" glued onto every label — the owner's
  design principle held the line (it's why "Pick" was deferred rather than forced onto the whole-week "AI Tips" plan).

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-107 — MADBOOTS vocabulary.** A small brand lexicon for the tool labels, governed by *clean, modern, not
gimmicky* (a rename must be at least as clear). Adopt **Radar** (Target by fixtures) + **Edge** (the "Why"); keep
**Risk** (reconcile Risks→Risk) + **Captain**; **defer "Pick"** (AI Tips is a whole-week plan). Display-only.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **The "another pass to tweak later"** the owner flagged — revisit the lexicon once it's seen in the browser
  (e.g. whether "AI Tips" earns a brand name, or a right-sized "Pick" surface appears).
- **Still on the 2026-08-12 intake (`docs/Backlog.md`):** mascot/brand-in-tools (UX A4); per-GW xP display (A5);
  the player-actions consolidation (A6).
- **GW1 (2026-08-21, ~9 days):** the dormant-weight calibration remains the data-gated thread (ADR-101).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- For any find/replace of a label, `grep` the whole `src/` for the string first — renderers duplicate.

---

# Key Commands Learned

```text
grep -rn "Target by fixtures" src/ tests/     # confirm a label sweep left nothing behind
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| **Edge** | The advantage / the reasons ("why") — the explanation block's ✓ heading (was "Why") |
| **Risk** | The downside — the explanation block's ⚠ heading (reconciled from "Risks") |
| **Radar** | Players to watch — the Fixtures shortlist (was "Target by fixtures") |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-107-madboots-vocabulary.md` | The lexicon + the "clean, not gimmicky" principle (the reference for future brand words) |
| `src/ui/explain.py` · `src/ui/captain.py` · `captain_card.py` · `src/ui/gameweek.py` | The four surfaces that render the Edge/Risk block |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---
