# Lessons Learned

**Sprint:** Sprint 078 — Team-level squad fixtures (the ADR-049 deferral)

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Close the ADR-049 deferral: let `ask`/`chat` rank a squad's **teams** (with player-counts) by their fixture
run, not just one row per player — reusing `team_fdr`.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Adding a new mode to a keyword-routed intent by building the **sibling** of an existing handler.
- Verifying the data shape at planning (group-by-team + `team_fdr` join) before writing code.

### New Skills Acquired

- Cue-based sub-routing inside an intent branch: a **plural/`by team`** cue distinguishes the team-level
  lens from the player-level one without a new intent — and without false-triggering on "my team's".

---

# What Went Well ✅

- **Sibling pattern** — `_decide_squad_team_fixtures` mirrors `_decide_squad_fixtures` (same inputs, grouped
  by team), so it's small, consistent, and grounded/verified for free.
- **Reuse** — `team_fdr` already gives per-team avg difficulty + opponents; the new work is just grouping +
  a renderer.
- **No disturbance** — the player-level view and the other three fixtures modes are untouched (a routing
  test pins both directions).
- **Probe-first** — the demo-squad grouping (15 players → 12 teams, CRY ×2) confirmed the lens at planning.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Distinguish team-level from player-level | both are "squad fixtures" | Route on a **plural** cue (`teams`/`clubs`/`by team`/`by club`); default player-level |
| "my team's players" mustn't route to team-level | it contains "team" | Require the plural/`by team` form — "team's" ≠ "teams"; a test guards it |
| Grounding a team-code view | subjects are team codes, not player names | The verifier gates player-name mentions + numbers, so team codes are fine |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Sibling handlers | A new intent-mode is cheapest as a sibling of the closest existing handler |
| Cue sub-routing | A small plural/`by X` cue can split a mode cleanly, no new intent needed |
| Reuse the analytic | `team_fdr` served three fixtures modes; the 4th is just a different grouping + renderer |
| Grounding scope | The verifier keys on player names + numbers, so a team-code answer verifies naturally |

---

# Development Lessons 💻

- Build a new mode as the sibling of the nearest one — same inputs, different shape.
- Probe the data grouping at planning; the code then writes itself.
- Keep routing cues specific enough not to catch adjacent phrasings (plural vs possessive).

---

# AI Collaboration Lessons 🤖

- The owner picked a well-scoped deferred item; the plan's real-data probe made the build a formality.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-067 | **Team-level squad fixtures** — a 4th `fixtures` ask mode ranking a squad's **teams** (player-counts) by `team_fdr`; a **`teams`/`clubs`/`by team`** cue routes to it within the squad branch (else player-level); a dedicated `render_squad_team_fixtures`; grounded; reuses `team_fdr`; other modes unchanged | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Open items: pronoun-aware chat; small decision-support gaps (bench order, availability flags in the
  ranking views); and — post-GW1 (2026-08-21) — the Data Hardening flip + calibration and the
  crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the probe-first, sibling-handler approach for new intent modes.

---

# Key Commands Learned

```text
python app.py ask "which of <squad>'s teams have the best fixtures?"   # the team-level lens
python -m pytest tests/test_ask_fixtures.py -q                          # all four fixtures modes
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Team-level squad fixtures | A squad's distinct teams ranked by their FDR run, with a player-count each |
| Sibling handler | A new mode built as a near-copy of the closest existing handler |
| Cue sub-routing | Choosing a sub-mode inside an intent branch from a keyword cue |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-067 (+ ADR-048/049) | The fixtures ask intent and its four modes |
| `src/ask.py` `_decide_squad_team_fixtures` | The team-level handler + the cue routing |
| `src/ui/fixtures.py` `render_squad_team_fixtures` | The Team · #Players · Avg FDR renderer |

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

- US-214 Team-level squad fixtures — "which of \<squad>'s teams have the best fixtures?" (ranked teams with
  player-counts, reusing `team_fdr`); a `teams`/`by team` cue routes to it; a dedicated renderer

**Stories Carried Forward:**

- None. (The ADR-049 deferral is closed.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
