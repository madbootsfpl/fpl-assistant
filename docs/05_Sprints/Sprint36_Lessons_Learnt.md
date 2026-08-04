# Lessons Learned

**Sprint:** Sprint 036 — Fix the `ask analyse` table + assess xMins

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make `ask "analyse <squad>"` show the full squad-analysis table (per-GW xP + weak links) above its
narration — matching the transfer plan — by reusing the command's own renderer. And assess + place
**xMins** (a lightweight v0 and a full ML model) on the Backlog/Roadmap. No new ADR, no new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Closing a gap by *composition* — wiring two surfaces to the same renderer instead of growing a second.
- Writing a backlog entry that's a *decision* (two steps, needs, placement), not a wish.

### New Skills Acquired

- Threading already-computed data (per-GW xP) through a decision that was discarding it.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **The fix was a join, not a rebuild.** The retro gap was pure omission — `_decide_analyse` discarded
  the per-GW data it already held and returned a one-liner. Reusing `render_squad_analysis` (the
  command's own table) closed it in a few lines.
- **The trust line kept working untouched** — the narration's named weak links all trace to the table
  above, so the ✓ line still verifies.
- **Consistency as a feature** — `ask`'s transfer and analyse intents now both show the exact table
  above the narration.
- **An honest, staged xMins plan** — a lightweight v0 (most of the value, now-ish) + the full ML model
  (rigorous, post-GW1) beats a vague "someday".

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `ask "analyse"` showed no table | The decision discarded per-GW data + returned a one-line headline | Thread per-GW into `analyse_squad`; return `render_squad_analysis(...)` as `detail` |
| The one-line headline became redundant | The table's header already shows projected XI xP | Dropped it — detail-only, like the transfer plan |
| xMins is big and data-hungry | Full ML needs in-season + external data | Split: a lightweight FPL-native v0 now, the ML model as a later gated phase |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Reuse over rebuild | When two surfaces should agree, wire them to the *same* renderer |
| Don't discard, thread | The data the fix needed was already in hand — just unused |
| Staged assessment | Split a heavy feature into a lightweight-now step + a rigorous-later step |
| Honest scope | v0 is an estimate from chance% + history, not the full probabilistic model — say so |

---

# Development Lessons 💻

- A "missing feature" is sometimes an omission, not new work — check what's already computed first.
- A backlog entry earns its place when it states the two steps, what each needs, and where it fits.

---

# AI Collaboration Lessons 🤖

- The retro note *was* the spec — the exact terminal output Tony pasted made the gap unambiguous.
- The composition pattern (one renderer, two intents) keeps the grounding verifier honest for free.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| — | No new ADR. US-107 applies **ADR-036** ("`ask` returns structured detail") to the analyse intent; US-108 is a Backlog/Roadmap placement (xMins), not an architectural decision | — |

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

- **xMins v0** is now assessed and shovel-ready — a strong near-term Phase 3 candidate. Or Data
  Hardening (~GW1), more Phase 4, or the web UI.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate + 3-part DoD. When a retro pastes exact output, treat it as the acceptance test.

---

# Key Commands Learned

```text
python app.py ask "analyse TS"    # now shows the full squad table (per-GW xP + weak links) + ✓ line
python app.py analyse --squad TS  # the same table, from the command
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| xMins | Expected minutes — a player's likely playing time, to weight xP by |
| xMins v0 | The lightweight, FPL-native estimate (chance% × historical minutes ratio; no ML) |
| Structured detail | A pre-rendered table an `ask` answer shows above the narration (ADR-036) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-036 | The "`ask` returns structured detail" pattern US-107 reused |
| Backlog → Expected minutes (xMins) | The two-step assessment + placement |
| Roadmap Phase 3 / Phase 5 | Where v0 and the full ML model sit |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Reuse vs rebuild | | |
| Staged feature assessment | | |
| The `ask` composition | | |
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

- US-107 `ask "analyse"` structured detail table (per-GW + weak links) — reuse `render_squad_analysis`
- US-108 Assess + place xMins (v0 + full ML) on the Backlog + Roadmap

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
