# Lessons Learned

**Sprint:** Sprint 041 — Show what you optimised (squad-table xP) + a "best players" `ask` intent

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Finish the "one metric" work *visually* — the `squad` table showed last-season points while optimising
xP — so it now shows **xMins + xP + a projected total** under `--objective xp`. And add a Phase 4
intent: `ask "best <position> [under £Xm]"`, ranked on the unified xP. No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Finishing a fix at the display, not just in the model.
- Composing a new intent from existing parts (xP + filter/sort + renderer + verifier).
- Ordering operations so the early exit is also the testable one.

### New Skills Acquired

- A position/price NL parser + a value (xP/£m) toggle.
- Conditional table columns in a shared renderer (Pts vs xMins/xP).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **Closed the loop the owner opened** — the squad now *shows* the metric it *optimises*; the
  Pts-vs-xP mismatch that started three sprints of "trust the numbers" is gone on screen.
- **Composition, seventh time** — the new intent is `decision_xp` + a filter/sort + the shared renderer
  + the verifier; no new data, no new dependency.
- **A real-vocabulary win** — "best value" means xP-*per-£m*, not raw xP; a one-line toggle.
- **Filter before compute** — reordering `_decide_shortlist` made the no-match path cheap and
  unit-testable without fixtures.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Squad optimised xP but showed Pts | The table only ever printed `total_points` | `render_squad` branches on `show_xp` → xMins/xP + projected total |
| "best value" ≠ "best" | Value = points per £m in FPL | A `by_value` toggle (sort by xP/£m) |
| No-match path needed fixtures to test | It called the xP calc before filtering | Filter the pool first → cheap + testable message |
| "forward"/"value" are common words | Routing is keyword-based | Accept for v0; route shortlist after build_squad |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Trust lives in the display | Finish a metric fix on screen, not just in the optimiser |
| Domain vocabulary | "value" = per-£m — matching the words reads as understanding |
| Order for the early exit | Filter before the expensive compute → cheaper and testable |
| Composition | A seventh intent, still zero new analytics — the unified xP keeps paying off |
| Conditional columns | One renderer, two column sets (Pts vs xMins/xP), branched cleanly |

---

# Development Lessons 💻

- A "loose end" in the display is worth closing — it's where the user's confusion actually lived.
- Reorder to make the cheap path the testable path; the test writes itself.
- Keep new intents thin: parse → reuse the shared decision + renderer + verifier.

---

# AI Collaboration Lessons 🤖

- The gate probe again shaped the design (the value toggle) before code.
- Seven intents on keyword routing still holds — but the retro flags a classifier as the next tidy.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-042 | A `shortlist` `ask` intent — `best <position> [under £X]` ranked by the unified xP (or xP/£m for "value"); routed after build_squad; grounded + a no-match message | Accepted |
| — | US-121 (squad-table xP) is a display completion of ADR-041 — no new ADR | — |

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

- An intent classifier if intents keep growing; an ownership/differentials intent. (GW1) partial-season
  baseline tuning; the full Phase-5 xMins. Or the web UI.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate probe broad; keep the 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --full                      # objective xp (default): now shows xMins + xP + projected total
python app.py ask "best midfielders under £8m"  # top players by xP (position + price filters)
python app.py ask "best value goalkeepers"      # ranked by xP per £m
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Shortlist intent | `ask "best <position> [under £X]"` — the top players for a filter |
| by_value | Rank by xP per £m instead of raw xP ("best value") |
| Show what you optimised | Display the metric the optimiser used (xP), not a proxy (last-season Pts) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-042 | The shortlist intent design |
| ADR-041 | The unified `decision_xp` this ranks on + the squad-table xP completion |
| ADR-025 | The shared table renderer both the squad table and the shortlist reuse |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Metric vs display | | |
| Composing NL intents | | |
| Ordering for testability | | |
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

- US-121 Squad table shows xMins + xP + projected total (finishes "one metric" visually)
- US-122 Gate — ADR-042 (the shortlist intent)
- US-123 `ask "best <position> [under £Xm]"` — the seventh intent

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
