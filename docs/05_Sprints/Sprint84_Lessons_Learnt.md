# Lessons Learned

**Sprint:** Sprint 084 — Fix the xG rating flaw · rename This week → AI Tips · Ask examples

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the xG board's quality rating honest (only where xGI is a real signal, clearly labelled as xGI), and
land two small tester UI asks — rename the Squads gameweek tab to **AI Tips**, and show a few **example
prompts** on the Ask tab.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Treating a "looks fine" feature as a hypothesis and checking it on real data** — the ADR-071 rating was
  correct for xGC/90 but wrong for xGI on goalkeepers; only the data made that obvious.
- Fixing by **scoping inputs**, not touching the shared helper — the smallest correct change.

### New Skills Acquired

- A rating is only honest **where the metric is a genuine signal for that player** — xGI means nothing for a
  keeper, so the honest output is a blank `—`, not a colour.
- **Rate against the meaningful pool**, not "all shown rows" — including 172 zero-minute players (and, when
  filtered, only keepers) skewed the quintiles into nonsense.
- A UI **label** and the **content** it shows can legitimately differ — the tab is "AI Tips", the plan it
  renders still reads "This week — squad X" (it *is* this gameweek's plan).

---

# What Went Well ✅

- **The tester caught a real bug** ("how can 0 be good and 56 be good?"), and grounding it (GK xGI max 0.22;
  172 zero-minute players; median outfield xGI 4.12) pointed straight at the fix.
- **Surgical fix** — the `quality_band` maths, the analytics, and Clean sheets were untouched; only the xG
  board's `_rate_xgi` predicate + pool changed, plus a clearer column name/placement.
- **Cheap UI wins** — the rename and the Ask examples were small, static, and low-risk.
- 612 → 613 tests; ruff + CI-parity green; seed.db kept clean.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Keepers rated "🟢 excellent" on xGI | xGI is ~0 for GKs; the pool included all zeros; filtered-to-GK made 0.04 "top 19%" | Rate xGI only for outfield ≥900-min players, against that pool; blank `—` otherwise |
| The single "Rating" read as ambiguous vs xGC | the column sat last, after xGC | Renamed "xGI rating" and moved it right after xGI |
| Renaming "This week" risked breaking the plan content | the plan block + tests reference "This week" | Renamed the **label/dispatch/function/help** only; kept the plan content + NL phrasing |
| `data/seed.db` looked modified again | a one-off write earlier in the session (not a test — verified) | Restored to HEAD; confirmed a full `pytest` leaves it clean |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Rate only where meaningful | A metric that doesn't apply (xGI for a GK) should be blank, not bucketed |
| Pool choice matters | Rating "vs all shown" breaks when most rows are zeros; rate vs the qualifying pool |
| Scope the inputs, not the helper | Reused `quality_band` untouched — changed only which rows/pool feed it |
| Label vs content | A friendly tab label ("AI Tips") can front unchanged content ("This week — squad X") |
| Verify the seed each commit | A stray data-file write is easy to miss; `git diff --quiet data/seed.db` settles it |

---

# Development Lessons 💻

- When a rating/label "feels off" to a user, check the distribution before defending it — they're often
  right, and the data shows why.
- Prefer a blank/"not applicable" over a confidently-wrong value.
- Keep a rename to the label surface; don't churn the content or the routing it depends on.

---

# AI Collaboration Lessons 🤖

- The owner's "rate only meaningful players" + "name it xGI rating, put it by xGI" calls were exactly the
  two fixes the data pointed to — presenting the real distribution up front made those decisions quick.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-073 | **Rate the xG board only where xGI is meaningful** (refines ADR-071) — rate `xGI` only for outfield players with ≥900 mins, against that pool; GKs / low-minutes / no-data show a blank `—`; column renamed "xGI rating" and moved beside `xGI`. `quality_band` + the analytics + Clean sheets unchanged | Accepted |

(US-226 rename and US-227 Ask examples were UI/content only, no ADR.)

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Reseed the deploy** (`python app.py reseed` → commit → push) so testers see Sprints 081–084 on fresh
  data — the Cloud seed is still the 570-player snapshot.
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration; revisit the ≥900-min rating bar for
  early-season play.
- Possible: make the Ask example prompts **clickable** (populate the box) rather than copy-paste.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep grounding every "this looks wrong" report in the real distribution before choosing a fix.

---

# Key Commands Learned

```text
python -m src.web_streamlit      # Players → xG shows an "xGI rating" (outfield ≥900 mins only); GKs blank
git diff --quiet data/seed.db    # confirm the committed seed snapshot is untouched before staging
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| xGI rating | The attacking quality rating on the xG board (outfield ≥900 mins only) |
| Meaningful pool | The subset a metric is a genuine signal for — what a relative rating should rank against |
| Label vs content | A tab's display name ("AI Tips") vs the plan text it renders ("This week — squad X") |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-073 | The xG-rating fix + the real-data evidence (GK xGI ≈ 0; zero-minute players) |
| `src/web_streamlit/views/players.py` | `render_xg` `_rate_xgi` predicate + the rated pool |
| `src/web_streamlit/pages/4_Ask.py` | The Ask example-prompts expander |

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

- US-225 Fix the xG-board rating — rate xGI only for outfield ≥900-min players, blank `—` otherwise; column
  renamed "xGI rating" and moved beside xGI (ADR-073, refines ADR-071)
- US-226 Rename the Squads "This week" tab → "AI Tips" (engine unchanged)
- US-227 Ask example prompts — an expander of 7 copy-paste questions on the Ask page

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
