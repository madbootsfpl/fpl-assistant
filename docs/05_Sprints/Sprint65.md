# Sprint 065: Hold & gather feedback (until GW1)

**Dates:** 2026-08-06 →
**Status:** ✅ Closed — trigger hit (a 🔴 tester-feedback bug → Sprint 066)
**Capacity:** Minimal — owner-run calendar time (share, gather, triage); revisit at GW1 or on feedback
**Carried Over:** None (Sprint 064 shipped Phase 6 Tier-2 start)

> **Direction (owner):** *"wait / gather more feedback."* Much of the high-value forward work is
> **GW1-gated** (2026-08-21, ~2 weeks out), and the app is feature-rich + green (514 tests). So this sprint
> is an intentional **hold**: keep the tester-feedback loop turning and let **GW1** trigger the parked
> season work. **No feature code** this cycle.

---

### 🎯 Goal

Stay ready without building: **capture + triage** any tester feedback (into `docs/00_Project/Feedback_Log.md`),
and keep a clean, recorded handoff to a **GW1 sprint**. Act when there's signal — feedback that warrants a
fix, or the season starting — not before.

#### Success Criteria
- [ ] Any tester feedback that lands is **logged + triaged** in `Feedback_Log.md` (severity → backlog?)
- [ ] **No feature code** ships this cycle (the app stays as it is at Sprint 064 close)
- [ ] The **parked GW1 work** stays recorded (below) so a GW1 sprint can start cleanly
- [ ] Exit the hold when there's a trigger: a feedback item worth fixing, or **GW1 (2026-08-21)**

---

### ⏸️ Parked until GW1 (2026-08-21) — the next sprint's likely backlog

These need the season to actually start (in-season / post-deadline data):
- **Live manager-import check** — confirm the by-ID import pulls a real squad once picks unlock (the picks
  endpoint 404s until the GW1 deadline).
- **Trends `ask`/`chat` intent (US-185)** — most transferred in/out · risers/fallers · in-form (momentum is
  0 preseason).
- **Calibrate the momentum thresholds** — `TRENDING_NET` / `FORM_MIN` on real transfer/form data.
- **Data Hardening** — per-GW `history` ingestion + in-season form blending (empty preseason).
- **A reseed + redeploy** so the live app reflects in-season data (momentum flags, news, prices).

### 🧊 Deferred (later, gated)
- **Tier-2b keyed social** — Reddit r/FPL sentiment (needs a Cloud secret + infra) / pundit NLP.
- **Tier 3** — a crowd-vs-xP backtest (needs in-season results).
- **Chip optimisers** — Triple Captain / Free Hit / Wildcard (buildable preseason, but deferred by this
  hold; a candidate if we want a non-GW1 build sooner).

---

### 📋 Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| — | **(No build stories.)** Ongoing: triage incoming feedback into `Feedback_Log.md`; exit on a trigger | — | 🕓 Holding | — |

---

### ✅ Definition of Done (this cycle)

Not a build DoD. The hold "completes" when a **trigger** arrives:
1. **A feedback item worth fixing** → plan a small feedback sprint (like Sprint 063).
2. **GW1 (2026-08-21)** → plan a GW1 sprint from the *Parked* list above.

Until then: the app stays green + unchanged; feedback is captured; nothing is over-built.

---

### 📝 Session Progress Log

- **Hold opened (2026-08-06)** — owner chose to wait / gather feedback. No build. Feedback intake via
  `Feedback_Log.md`; the parked GW1 work is recorded above. Next trigger: a feedback fix, or GW1.
- **Hold closed (2026-08-06)** — trigger hit: a 🔴 feedback bug (the web **Ask** tab ignored the loaded
  session squad — "captain/analyse RoboTS" fell back to "(all players)"). → **Sprint 066** fixes it. The
  parked GW1 work carries to a GW1 sprint.

---

### 🏁 Sprint Review & Retrospective

_(to be completed when the hold ends — at the trigger)_
