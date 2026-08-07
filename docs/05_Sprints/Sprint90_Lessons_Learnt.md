# Lessons Learned

**Sprint:** Sprint 090 — A quick-stats summary on the My Squad banner

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Use the My Squad banner real estate for a team quick-view: projected XI xP over the chosen horizon, the
captain's (doubled) xP, bench strength, an availability snapshot (counts + who's flagged) — all above the
existing pitch.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Assembling a summary purely from data the view already holds** — no new fetch, no analytics change.
- Reusing helpers built in prior sprints so a small feature compounds (horizon, availability chance%).

### New Skills Acquired

- `st.columns(n)` + `st.metric` is the clean pattern for a scannable stats row; `AppTest` reads them via
  `at.metric` (`.label`/`.value`).
- A summary's "Projected XI" should use the **best legal XI** (declared bench if set, else `best_legal_xi`),
  not "all owned" — otherwise it sums 15 and mislabels it an XI.

---

# What Went Well ✅

- **Everything was already on hand** — horizon-aware `xp_by_id`, `is_unavailable`, `availability_flag`,
  `captain_id`; the sprint was assembly + layout.
- **It compounds** — the Projected-XI metric moves with the Sprint-089 *Gameweeks ahead* selector; the
  flagged line shows the Sprint-088 chance% on ❓.
- **A real correctness catch** — the first pass summed all 15 as "Projected XI"; switching to the best legal
  XI (11) made the split honest (XI + Bench = all 15).
- 627 → 629 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "Projected XI" summed all 15 | no declared bench → `xi` was everyone | Use `best_legal_xi` (like Health) for the summary; Bench = the rest |
| Testing the flagged line deterministically | the demo squad is all-available | Inject a session squad with a real injured player |
| `seed.db` showed dirty after a manual smoke | a SQLite file-open byte touch (content unchanged) | `git checkout -- data/seed.db`; confirmed pytest doesn't touch it |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Reuse the view's data | A summary is often just layout over values already computed |
| Best-XI, not all-owned | "Projected XI" must be the best 11, or the label lies |
| Metrics via AppTest | Assert `at.metric` label/value; drive the horizon selector and re-check the label |
| Benign seed touches | A manual AppTest smoke can byte-touch a DB file; check before staging |

---

# Development Lessons 💻

- Before adding a summary number, decide exactly what set it's over (best XI vs all owned) and label it so.
- Inject session state to test a branch the default/demo data can't reach.
- Keep the "check seed.db before staging" habit — it's caught stray touches repeatedly.

---

# AI Collaboration Lessons 🤖

- "Would love all those suggestions" → build the full summary generously, but still make each number honest
  (best XI, chance% on doubts) rather than just dumping stats.

### Notes _(for Tony)_

---

# Decisions Made 📋

No new ADR — a **display-only** My Squad summary that reuses existing decisions:
- the horizon (**ADR-077**) for the Projected-XI window,
- `availability_flag` (**ADR-074**, with the US-236 chance% on ❓) for the counts + the flagged line,
- `best_legal_xi` (**ADR-040**) for the XI split.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration — the projected numbers sharpen.
- Backlog still open: bench order (auto-sub priority); a season countdown/deadline banner; pronoun-aware
  chat; server-side squad persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep summaries honest: name the exact set a number is over, and reuse existing helpers over recomputing.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Squads → My Squad shows a metrics row + a who's-flagged line above the pitch
git checkout -- data/seed.db  # drop a benign seed byte-touch before staging
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Quick-stats summary | The metrics row + flagged line on My Squad |
| Projected XI | The best legal 11's projected xP over the chosen horizon (not all 15) |
| Bench strength | The bench's total projected xP |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/views/squads.py` (`render_my_squad`) | The summary metrics + flagged caption |
| `availability_flag` (ADR-074) | The flag vocabulary + chance% reused for the summary |

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

- US-239 My Squad summary metrics — Projected XI (N GW) · Captain (2×) · Bench · Unavailable · Doubtful
- US-240 Who's flagged — a caption naming the injured/suspended/doubtful players (with flags), else all-clear

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
