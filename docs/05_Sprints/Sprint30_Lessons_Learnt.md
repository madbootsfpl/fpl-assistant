# Lessons Learned

**Sprint:** Sprint 030 — Analyser Enhancements (per-gameweek xP + sort by xP)

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Extend xP with a **per-gameweek breakdown** (decomposing the horizon total, DGW/BGW handled) and
surface it in `analyse` (and the `xp` command); add **`--sort xp`** to `analyse`. From Tony's
Sprint-29 retro note. FPL-native; no new dependency, no schema change, the xP total unchanged.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Extending an existing metric *additively* (extra keys) without disturbing it.
- Proving a decomposition sums to the original before building.
- Building dynamic table columns (a variable number of gameweek columns).

### New Skills Acquired

- Reacting at planning to live conditions (ClubElo recovered; season not started) by reordering.
- Keeping a total authoritative while rounding a breakdown for display (and footnoting the artifact).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **Built exactly the owner's retro ask** — per-GW xP + `--sort xp` — and closed a Sprint-006 backlog
  item (`xp` per-GW) in the same stroke, because one additive change served `analyse` *and* `xp`.
- **Additive, not invasive** — `by_gameweek` is extra keys on the result; existing consumers ignore
  them and **every existing xP test stayed green** (the total didn't move).
- **Maths proven before code** — the planning probe showed per-GW sums to the total; a test asserts it.
- **Planned against live conditions** — reordered away from a preseason-blocked sprint toward what was
  ready and wanted.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Breakdown must equal the total | Rounding per-GW then summing can drift | Total = sum of *unrounded* per-GW → byte-for-byte unchanged; a test asserts it |
| A row can read ±0.1 off its total | Per-GW cells rounded for display | Footnote it; the total is authoritative (don't fudge the total) |
| Variable number of GW columns | Horizon varies | Build columns dynamically; narrow widths; soft cap noted for large N |
| Data Hardening was next but blocked | Preseason (0 GWs) | Reorder: build the analyser asks now; Data Hardening → post-GW1 |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Faithful decomposition | Split a metric so the parts sum to the same total — legible, not a rewrite |
| Additive change | Extra keys don't disturb existing consumers or their tests |
| Display vs truth | Round for display, keep the total authoritative, footnote the artifact |
| Plan against reality | Reorder for what's buildable + wanted over what's blocked |

---

# Development Lessons 💻

- Prove the invariant (sum = total) before building; then a test locks it in.
- One well-placed analytics addition can serve several views (and close a backlog item).
- Be honest about a rounding artifact rather than faking a tidy sum.

---

# AI Collaboration Lessons 🤖

- The owner's own retro note was the spec — reading feedback closely set the sprint.
- Verifying live conditions at planning (ClubElo up, season not started) changed the plan for the better.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-032 | Per-gameweek xP: a faithful decomposition of the horizon total (DGW summed, BGW 0); additive (`by_gameweek` on the result, total unchanged); shown in `analyse`/`xp`; per-GW rounded, total authoritative; `analyse --sort xp` opt-in (default position) | Accepted |

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

- **Data Hardening** at/after GW1 (2026-08-21): full 567-player backfill + per-GW `history` +
  in-season xP form blending. Then xMins can retire bench-blindness in captain/transfer.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate + 3-part DoD; prove invariants before building; plan against live conditions.

---

# Key Commands Learned

```text
python app.py analyse --squad TS --sort xp       # XI ordered by xP, with per-GW columns
python app.py analyse --squad TS --next 3         # squad health + per-GW over 3 GW
python app.py xp --next 5 --by-gameweek           # players ranked, split per gameweek
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Faithful decomposition | Splitting a metric so the parts sum to the same total |
| Additive change | New output keys that don't disturb existing consumers |
| Authoritative total | The single-rounded total is the truth; the breakdown is display |
| Rounding artifact | A displayed row summing ±0.1 off its total, due to per-cell rounding |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-032 | The per-GW design + the total-unchanged guarantee |
| Handbook Ch 21 | Analytics — now with "making a metric legible without changing it" |
| ADR-006 / ADR-007 | The xP formula + horizon the breakdown decomposes |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Extending a metric additively | | |
| Proving invariants before building | | |
| Display rounding vs authoritative totals | | |
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

- US-089 Per-GW xP design + ADR-032 (gate)
- US-090 Per-GW xP analytics (total unchanged, unit-tested)
- US-091 Wire into `analyse` (+ `--sort xp`) and `xp --by-gameweek`

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
