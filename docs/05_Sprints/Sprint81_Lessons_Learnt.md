# Lessons Learned

**Sprint:** Sprint 081 — Pool layout · refresh clarity · an AI gameweek recommendation

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Close three tester items: the Players **Pool leads with the table**; the app makes its data **freshness
obvious** and gives a **one-command** way to update the deployed snapshot; and a grounded **"this week"**
recommendation (captain · lineup · a transfer · flags) that the AI narrates, verified.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Turning a **bug report into both a signal and a fix** — the "572 vs 569" confusion became a visible player
  count (the signal) *and* a `reseed` command (the fix), not just a written explanation.
- Adding a feature as an **assembler over trusted primitives** — new capability, no new analytics, no drift.

### New Skills Acquired

- The grounded `ask` pipeline is **composable**: a new intent = decide (assemble facts) → `assemble`
  narrates + `verify_grounding` checks; the web gets it "for free" by routing through `ask.answer`.
- **`subjects` is how you stop the verifier crying wolf** — a whole-squad answer must name every owned
  player (plus the transfer buy) as subjects, or a legitimately-named starter gets flagged.
- Mixing **two horizons in one answer** is fine and correct — captain is a one-week bet (next-GW xP),
  lineup/transfer look at the 5-GW run.
- **Intent ordering is precedence**: place a new phrase-based intent *after* the specific ones so a pointed
  keyword ("captain") still wins, and keep its phrases distinctive ("this week", "what should i do").

---

# What Went Well ✅

- Three tester items delivered in one sprint; the sequence (trivial reorder → visibility fix → the big
  grounded feature) kept momentum and risk low.
- US-220 reused `captain_picks` / `best_legal_xi` / `suggest_transfers` / availability verbatim — so the
  weekly plan *is* the standalone tools, assembled; it can't disagree with them.
- Verified end-to-end on real data (routing both ways; a degraded plan; a grounded narrator → the ✓ line).
- Test count 585 → 598; every check green; ruff clean.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Tester saw 569–570 players, CLI showed 572 | the app serves the committed **seed**, not their live cache; `DB_PATH` is frozen at import | Show the **count** in the freshness caption + a cloud snapshot note; add `reseed` |
| `reseed` must target `fpl.db` even when it doesn't exist yet | `DB_PATH` falls back to the seed pre-refresh | New `config.LIVE_DB_PATH` — `reseed` refreshes it explicitly, then copies to the seed |
| A new "this week" intent could steal pointed questions | keyword routing returns the first match | Place `gameweek` **after** the specific intents; distinctive phrases; a test pins "captain this week" → captain |
| The verifier could flag a named starter | a whole-squad narration names owned players | `subjects` = all owned names + the transfer buy |
| The freshness test asserted the old "Data as of" text | the caption now leads with the count | Update the assertion to `players · data as of` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Assemble, don't reinvent | A weekly recommendation is a *composition* of existing decisions, not new analytics — reuse keeps it trustworthy |
| One pipeline, two surfaces | Routing the web view through `ask.answer` gives narration + the ✓/⚠ trust line without duplicating anything |
| Grounding needs subjects | `verify_grounding` flags known names not in `subjects`; a squad answer must list them all |
| Freshness = a visible count | A number in the caption reveals *which* DB is being served far better than a date alone |
| Import-time config is a footgun | `DB_PATH` resolves once; name the live path explicitly so a command isn't at the mercy of that snapshot |

---

# Development Lessons 💻

- Order stories by rising risk (reorder → visibility → new grounded feature) so each lands before the next.
- When a report is really a mental-model mismatch (snapshot vs live), make the truth *visible*, then make
  the fix *one command*.
- Verify a new intent's routing in both directions (it fires when wanted, and yields when a specific intent
  should win) before trusting it.

---

# AI Collaboration Lessons 🤖

- The analytics-decide / LLM-narrates / verify contract paid off again: the "AI recommendation" the tester
  asked for is still fully grounded — the model only phrases a plan the analytics already made.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-070 | **AI gameweek recommendation ("this week")** — an assembler `gameweek_plan` over the existing primitives (captain · lineup vs the declared bench · one self-funding transfer · flags); a phrase-routed `ask`/`chat` **gameweek** intent that narrates + verifies (ADR-037); a `render_gameweek_plan` block; a **Squads → This week** view (routes through `ask.answer`, degrades without Ollama); no new analytics, no server writes | Accepted |

(US-218 and US-219 needed no new ADR — a UI reorder and an extension of ADR-053/056.)

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Post-**GW1 (2026-08-21)**: the Data Hardening flip (`history --backfill` + raise `FORM_WEIGHT`) + xP
  calibration — the gameweek plan gets sharper for free once form/momentum light up.
- Later: fold **chip advice** (Triple Captain / Bench Boost / Wildcard timing) into the "this week" plan
  (roadmap's chip optimisers).
- Consider a **captain/lineup/transfer confidence** cue once in-season data supports it.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the "new `ask` intent" recipe: an assembler in `analytics/`, a `render_*` in `ui/`, a `_decide_*`
  (facts + task + subjects) in `ask.py`, a keyword group placed by precedence, and a thin web view that
  routes through `ask.answer`.

---

# Key Commands Learned

```text
python app.py reseed                 # refresh fpl.db, copy -> seed.db (then commit + push to update Cloud)
python app.py ask "what should I do this week for <squad>?"   # the grounded gameweek plan (CLI)
# Web: Squads -> This week            # the same plan + the ✓/⚠ trust line
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Gameweek plan | The one-week assembled recommendation: captain · lineup · a transfer · flags |
| Assembler | A function that orchestrates existing decision primitives, adding no new analytics |
| Reseed | Refresh the live cache then copy it to the committed seed (the one-step deploy-data update) |
| Data snapshot | The committed `seed.db` the Cloud serves — updates on redeploy, not on a local refresh |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-070 | The gameweek-recommendation decision (assemble · route · narrate · verify) |
| `src/analytics/gameweek.py` | The `gameweek_plan` assembler — the pattern for future composed decisions |
| `src/ask.py` (`_decide_gameweek`) | How a new grounded intent is wired end-to-end |
| `docs/DEPLOY.md` (After it's live) | The cloud (reseed) vs local (button/restart) refresh story |

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

- US-218 Pool: table first — reorder `render_pool` so the table + pagination precede the top-15 bar
- US-219 Refresh clarity — player count in the freshness caption + a cloud snapshot note + a `reseed`
  command + the cloud/local refresh story (DEPLOY + Help); `config.LIVE_DB_PATH`
- US-220 AI gameweek recommendation (ADR-070) — a grounded "this week" plan (captain · lineup · a transfer ·
  flags): `gameweek_plan` assembler, a `gameweek` ask intent (narrated + verified), a Squads "This week" view

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
