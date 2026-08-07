# Lessons Learned

**Sprint:** Sprint 093 — Bench order polish (recommended on Build · sub numbers on the pitch)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Polish the bench-order feature: a freshly-built squad starts in the recommended (xP) sub order, and the My
Squad pitch labels each bench card with its sub number (1st / 2nd / 3rd / GK).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Finishing a feature across sprints** — start (Build) → see (pitch) → set (reorder), each a small,
  low-risk increment.
- Threading a new optional param through a display helper without disturbing its other callers.

### New Skills Acquired

- A card renderer can carry an optional role label (`sub_role`) that only appears for bench cards — the XI
  path is unchanged by defaulting it to `None`.
- Ordering a display row by a domain priority (`_ROLE_ORDER`) instead of position, gated on whether the
  caller supplies the roles.

---

# What Went Well ✅

- **Both stories were tiny** — US-245 one line (the helpers were already in scope); US-246 a `bench_roles`
  param on a My-Squad-only `render_pitch` + a `_card` caption.
- **The feature is now end-to-end** — a built squad starts sensible, the priority shows on the pitch, and
  it's fully reorderable (Sprints 091–093 compounding).
- **No drift** — display/edit only; the analytics still use `bench_ids` as a set.
- 634 → 636 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The pitch computed `bench_roles` *after* the pitch call | the bench-order block sat below `render_pitch` | Move the role computation above the pitch; keep the line/expander below |
| `AppTest.session_state.get(...)` fails | AppTest treats `get` as a key | Use `"squad" in at.session_state` / `[...]` |
| Ordering the bench row by role vs position | roles are optional | Order by `_ROLE_ORDER` when `bench_roles` given, else by position |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Optional label param | `sub_role=None` labels only bench cards; XI path untouched |
| Compute before you render | The pitch needs the roles first — hoist the computation above the call |
| Gate the ordering | Priority order only when roles are supplied; fall back to position |
| Reuse in-scope helpers | US-245 was one line because `bench_order`/`display_xp` were already there |

---

# Development Lessons 💻

- Small finishing touches (start-in-order, labels) make a feature feel complete — cheap, high perceived value.
- When a display needs derived data, compute it before the render call, not after.
- Keep new params optional + defaulted so existing callers/paths don't change.

---

# AI Collaboration Lessons 🤖

- Splitting a feature across sprints (see → set → polish) kept each change small and reviewable, and the
  owner steered the polish once the core landed.

### Notes _(for Tony)_

---

# Decisions Made 📋

No new ADR — both stories **extend** existing decisions:
- **US-245** extends **ADR-078/079** — Build seeds `bench_ids` in the recommended (xP) order.
- **US-246** extends **ADR-078/079** — the pitch labels bench cards with the sub role.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration.
- Backlog still open (season-timely): season countdown / deadline banner; GW1 readiness dry-run;
  pronoun-aware chat; server-side squad persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep finishing features with the cheap polish that makes them feel complete (start-in-order, on-card labels).

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Squads → Build starts the bench in xP order; My Squad pitch labels the subs
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| `bench_roles` | id → sub role ("1st"/"2nd"/"3rd"/"GK") passed to the pitch for card labels |
| `_ROLE_ORDER` | The sort order that lays the bench row out by sub priority |
| Recommended-on-build | Seeding a built squad's bench in the xP order so it starts sensibly |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/pitch.py` | `render_pitch(bench_roles=…)` + `_card(sub_role=…)` |
| `src/web_streamlit/views/squads.py` | Build seeding + the `bench_roles` computation |

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

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-245 Build → recommended bench order — a built squad's bench_ids start in xP order (outfield first, GK last)
- US-246 Pitch sub numbers — the My Squad pitch bench cards show 🔁 1st/2nd/3rd/GK sub

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
