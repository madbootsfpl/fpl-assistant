# Lessons Learned

**Sprint:** Sprint 069 — Data Hardening prep: per-GW history + a dormant form blend

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Front-load the two season-start foundations — **per-GW history ingestion** and an **in-season form blend** —
so **GW1 (2026-08-21)** is a *switch-flip*, not a scramble. Build both **now, wired but dormant**, verified
on real data, with **zero** behaviour change until the weight is raised.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Verifying a design on **real data** before building (the live `element-summary` probe).
- Extending a layered pipeline (model → storage → ingest → analytics) additively.
- Protecting an invariant (the one xP metric, ADR-041) while adding a new term.

### New Skills Acquired

- **Dormant-by-default** feature design: wire a whole feature end-to-end behind a weight/flag that defaults
  to inert, so it ships early, is exercised by tests, and activates with a one-line change later.
- Reusing a fetch's *whole* payload — one `element-summary` call yields both `history_past` and per-GW
  `history`, so a new ingest rides an existing walk with no second network pass.

---

# What Went Well ✅

- **Real-data-first** twice over: the probe confirmed `history` is empty preseason (so "dormant" is honest)
  **and** surfaced that the past-season walk already carries per-GW data — no extra fetch.
- **The invariant held by construction** — folding form into the *one* `decision_xp` recipe (mirroring the
  precomputed `baseline_by_code`) meant the existing 530 tests passing unchanged *is* the invariance proof.
- **A build-time snag improved the design** — per-GW rows carry no season name, so keying `(code, round)`
  (a current-season working set) dropped a magic `CURRENT_SEASON` constant instead of adding one.
- **GW1 is genuinely one switch** — every `decision_xp` caller (cli/ask/web) was wired, so activation is
  `backfill + raise FORM_WEIGHT`, nothing else.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Can't see the live per-GW row shape | `history` empty preseason | Design against known FPL keys; additive schema + idempotent upsert → an extra field is a one-line migration |
| Per-GW rows lack a season name | The FPL payload omits it | Key `(element_code, round)` — a current-season working set (re-backfill overwrites); no magic constant |
| Per-GW rows carry `element`, not the stable `code` | FPL uses the per-season id | Pass the code in via an id→code map (`get_player_codes`) |
| A dormant feature could rot unnoticed | It's inert until GW1 | An **activation** test (weight > 0 shifts the rate) + a real-DB smoke exercise the live path now |
| 11 `decision_xp` call sites to wire | Form data must be threaded (pure core) | Mechanical, uniform edits; the full suite + invariance test guard against drift |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Dormant wiring | A feature can ship *complete but inert* behind a weight-0 flag — de-risking a deadline (GW1) in calm time |
| One recipe | New signals (form) belong *inside* `decision_xp`, precomputed-and-passed like the baseline — never a parallel path (that's the inconsistency ADR-041 killed) |
| Ride the payload | One `element-summary` call already holds per-GW `history`; a second walk would have been waste |
| Additive schema | `CREATE IF NOT EXISTS` + idempotent upsert on `(code, round)` lets an old and a fresh cache converge, and shrugs off an unexpected field |
| Invariance as a test | "weight 0 ⇒ identical" pinned by a test means the dormant guarantee is enforced, not hoped for |

---

# Development Lessons 💻

- Probe the real source before designing — it confirmed the premise *and* handed over an efficiency (one
  payload, two ingests).
- Let build-time friction simplify the design (drop the season key) rather than paper over it.
- When threading a new arg through many callers, keep the edits uniform and lean on the test suite to catch
  a missed site.

---

# AI Collaboration Lessons 🤖

- The owner's steer — *computed rolling pp90* (not FPL's `form` field) and *both, wired + dormant* — set a
  clear, honest target; the plan's real-data gate then de-risked it before a line was written.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-060 | **Data Hardening step 1** — a per-GW `player_history` table (keyed `code+round`, additive/idempotent) filled by the *existing* throttled `element-summary` walk (empty preseason → live GW1); a **dormant** in-season **form blend** in the one `decision_xp` recipe (a minutes-aware rolling **pp90**, not FPL's `form`) behind `FORM_WEIGHT = 0` → xP unchanged today; the one-xP invariant (ADR-041) preserved, pinned by an invariance test; GW1 flip = backfill + set the weight | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **At GW1 (2026-08-21):** run `history --backfill` (now also per-GW), raise `FORM_WEIGHT` (start ~0.3),
  verify the shift, and **calibrate** the weight + window on real form. Then the **crowd-vs-xP / form-vs-xP
  backtest** (Tier 3) to check form actually helps. Also unlocked by per-GW data: rolling trend/"history"
  views. The full probabilistic xMins model stays a later, data-gated phase.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the real-data gate before building; keep new signals inside the one recipe; keep dormant features
  exercised by an activation test so they don't rot.

---

# Key Commands Learned

```text
python -m pytest tests/test_form.py tests/test_history.py -q   # the form blend + per-GW ingest
python app.py history --backfill --limit 4                     # smoke: "N season rows + 0 per-GW rows" (preseason)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Dormant feature | Built + wired end-to-end but inert (weight 0 / no data) until a one-line flip activates it |
| Per-GW history | This-season, one-row-per-player-per-gameweek data (`element-summary['history']`) — empty preseason |
| Rolling pp90 (form) | A recency- + minutes-weighted points-per-90 over the last N gameweeks |
| Invariance test | A test pinning "under condition X, output is byte-identical to before" (here: weight 0) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-060 | The per-GW + dormant-form design and the dormant-until-GW1 contract |
| `src/analytics/form.py` | The pure `form_rate` / `blend_form` — the form maths in one place |
| `src/analytics/xp.py` `decision_xp` | Where every signal (baseline · fallback · xMins · form) folds into the one rate |

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

- US-196 Per-GW history ingestion — a `player_history` table filled by the existing `element-summary` walk
  (empty preseason, live GW1)
- US-197 Dormant form blend — a rolling-pp90 form term in `decision_xp` behind `FORM_WEIGHT = 0`

**Stories Carried Forward:**

- None. GW1 flip pending (backfill + raise the weight + calibrate).

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
