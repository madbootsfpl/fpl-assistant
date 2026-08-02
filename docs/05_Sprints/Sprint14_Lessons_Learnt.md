# Lessons Learned

**Sprint:** Sprint 014 — Expected Goals (xG / xA / xGI)

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Bring FPL's expected-goals data (xG, xA, xGI, xGC) into the tool — ingest and store it,
rank players by it (an `xg` view), and add `--objective xgi` so the squad optimiser can
chase underlying attacking threat, beside points / value / xp.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Checking a data *source* before committing to a pipeline (FBref vs the FPL feed).
- Adding a new data dimension through existing seams (model, migration, objective).
- Coercing missing values at the read site so old databases keep working.

### New Skills Acquired

- A schema migration for a real, populated database (columns added in place).
- Reading a full-stack slice end-to-end: API → model → storage → analytics → view.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- The planning probe flipped the risk: FBref is 403-blocked; FPL already has the data.
- `--objective xgi` was one dict entry + one choices value — the ADR-011 promise held.
- Every seam already existed (`_to_float`, `_migrate`, `SELECT p.*`) — no new machinery.
- The gate proved a 9/11 squad swap before code; the 3-part DoD held (14th sprint).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| FBref unusable here | 403 (scraping blocked) + heavy dep + name-matching | Use FPL's own expected-* fields, keyed by id |
| Old databases lack the columns | Feature added after they were created | Generic `_migrate()` adds them in place on open |
| xGI can be None (unrefreshed/absent) | Migration leaves `NULL` until refresh | Coerce `None → 0.0` in the objective and the view |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Check the source | The data you want may already be in a feed you fetch |
| Pluggable objective | A 4th objective was a dict entry, not a solver change (ADR-011) |
| Generic migration | `ALTER TABLE ADD COLUMN` upgrades a live DB without a rebuild |
| Coerce at use | Store `None`-able; make the reader tolerate `NULL` |

---

# Development Lessons 💻

- Probe feasibility with a throwaway request before planning a whole integration.
- `SELECT p.*` means new columns surface without touching the read path.
- Add an objective's honesty note in the output, not just the ADR.

---

# AI Collaboration Lessons 🤖

- The feasibility probe (run at planning) re-routed the whole sprint away from a dead end.
- The gate's worked example proved the field reaches a decision before any feature code.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-015 | Expected goals from the **FPL API** (FBref rejected — 403 + dependency); ingest xG/xA/xGI/xGC via a migration; an `xg` view; `--objective xgi` (one `objective_scores` entry); attacking bias stated | Accepted |

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

- Rebuild xP on xG (expected points from expected goals) — the data is now in place.
- A defensive (xGC) metric; a per-90 involvement view.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep probing feasibility at planning; keep the gate + 3-part DoD.

---

# Key Commands Learned

```text
python app.py xg --pos FWD            # players by expected goal involvement (xG + xA)
python app.py squad --objective xgi   # optimise the squad on attacking involvement
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| xG / xA | Expected goals / assists — the quality of chances, not the outcome |
| xGI | Expected goal involvements = xG + xA (attacking threat) |
| xGC | Expected goals conceded — a rough defensive measure |
| Schema migration | Adding columns to an existing table without a rebuild |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-015 | Records the FPL-over-FBref decision + the four fields |
| Handbook Ch 24 | Expected goals — what xG/xA/xGI mean and how they flow through |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Checking a data source first | | |
| Schema migrations | | |
| Full-stack data flow | | |
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

- US-044 Expected-goals design + ADR-015
- US-045 Ingest & store xG/xA/xGI/xGC + migration
- US-046 The `xg` view + `--objective xgi`

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
