# Lessons Learned

**Sprint:** Sprint 120 — Fixtures for planning: target players by run + a "my squad" lens

**Dates:** 2026-08-21

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the Fixtures page a **planning aid** for a new squad / wildcard (owner feedback). Turn "which teams have a
good run" into "**who to buy**" (a 🎯 Target-by-fixtures shortlist), and let you scope the ticker to **your own**
teams. Display lenses only, reusing `team_fdr`/`fixture_ticker` + the one `decision_xp` metric; no analytics
change.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Compose, don't re-derive** — a new view from two existing analytics (`team_fdr` × `decision_xp`), no new math.
- **Verify the design on real data first** — it locked a decision *and* caught an already-shipped item.

### New Skills Acquired

- **A "planning" view is a join, not a new metric.** "Best players from the easiest-run teams" = rank teams (have
  it) × rank players by xP (have it) × a group-by-team pick. The value was the *composition*, so it lived in one
  small pure function (`target_by_fixtures`) with a thin page edge.
- **Lock a metric choice with evidence, not taste.** The gate ("rank by xP vs points?") was settled by *looking*:
  preseason, `decision_xp` and `total_points` diverge on new signings (Isak xP 16.9 vs 41 pts) — xP is right, and
  it keeps the whole app consistent (ADR-041). A one-probe decision beat an argument.
- **Planning-first catches "already done".** Probing the availability backlog bullet showed the CLI Fit column +
  the doubtful chance% were *already* shipped (US-276/US-236). The gate saved a wasted sprint slot.
- **Two complementary lenses read better than one clever one.** Target-by-fixtures (buy) stays all-teams; the My
  squad ticker (hold/sell) scopes to your teams. Keeping them separate made each obvious.

---

# What Went Well ✅

- **One pure assembler + a thin edge** — `target_by_fixtures` is unit-testable; the page just renders it.
- **No analytics drift** — `team_fdr`/`fixture_ticker`/`decision_xp` untouched; the read-only web guardrail holds.
- **Real data to verify against now** — FDR is populated preseason, so the shortlist wasn't a preseason no-op.
- **A backlog bullet closed for free** (CLI Fit + chance%, found already done at planning).
- 766 → 771 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Rank targets by xP or points? | both plausible preseason | Probe real data → xP diverges on new signings; pick `decision_xp` (ADR-041) |
| Where does the join live? | it mixes fixtures + players | A new small `analytics/targets.py` (not `fdr.py`, which is team-only) |
| A doubtful target — show it? | `is_unavailable` excludes only 🚑/🚫/⛔ | Keep doubtful, carry its `fit_flag` (`❓ 75%`) |
| My squad, no squad loaded | `active_squad()` is None on a fresh session | A note + fall back to all teams (never an empty page) |
| The ticker test asserted exactly 1 table | US-301 adds a 2nd (targets) | Loosen to `>= 1`; index the ticker `[0]`, targets `[-1]` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Composition over new metrics | A planning view = join existing rankings, not a new model |
| Evidence-led gates | Settle a metric choice by probing real data, not debate |
| Module boundaries | Keep `fdr.py` team-only; a player-join gets its own module |
| Availability nuance | Doubtful ≠ unavailable — a valid target that carries its Fit |
| Test the new shape | A 2nd dataframe on a page → update the count-based assertions |

---

# Development Lessons 💻

- Put a cross-analytics join in its own small pure module; keep the page a thin renderer.
- Decide a design fork by looking at the data it will run on, then record the reason at the gate.
- When adding a second table/section to a page, fix the existing tests' shape assumptions in the same change.

---

# AI Collaboration Lessons 🤖

- The Target list ranks by the **same `decision_xp`** every recommendation uses — the fixtures view can't disagree
  with captain/transfer/build on a player's value. The lens re-*orders* by fixture ease; it never invents xP.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-301/302 are display lenses. US-301 adds `analytics/targets.py::target_by_fixtures` (a composition
of `team_fdr` + `decision_xp`, ADR-041); the ranking metric was locked at the gate to `decision_xp`. US-302 brings
the **ADR-049** team-lens idea — already shipped for `ask`/`chat` via **ADR-067** (`render_squad_team_fixtures`) —
to the **web fixture ticker** as a My-squad scope._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A price / affordability filter on the Target shortlist** — reuse the Sprint-119 bank idea (buy within budget).
- **A "widen" control** (top-N teams / per-team count) if the fixed 6×3 feels tight in practice.
- **An FDR source toggle** (fpl / custom / elo) on the Fixtures page.
- Post-**GW1 (2026-08-21)**: FDR + form sharpen; the target xP gains the in-season form blend automatically.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep leading each sprint with a real-data probe — it locks design forks and catches already-done work.

---

# Key Commands Learned

```text
python -m src.web_streamlit     # Fixtures → 🎯 Target by fixtures (Position filter) + Show: My squad
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Target by fixtures | The best players to buy from the easiest-run teams (a planning shortlist) |
| Ticker scope | All teams vs My squad — focus the difficulty grid on your own teams |
| Composition lens | A view built by joining existing analytics, adding no new metric |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/targets.py` | The pure fixtures→players join (`target_by_fixtures`) |
| `src/analytics/fdr.py` (`team_fdr`, `fixture_ticker`) | The easiest-first team ranking the lens builds on |
| `src/web_streamlit/pages/2_Fixtures.py` | The ticker + Target section + the My squad scope |
| `src/web_streamlit/squads.py` (`active_squad`) | The session squad the ticker scope reads |

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

- US-301 🎯 Target by fixtures — best players from the easiest-run teams, by xP (+ a position filter); a new
  `analytics/targets.py` (composition of the fixtures + xP families, ADR-041)
- US-302 A "My squad" lens on the fixture ticker — scope to your teams + a player-count (the ADR-049 team lens →
  the web ticker; cf. ADR-067's `ask` version)

**Stories Carried Forward:**

- None. (A price filter + a "widen" control on the targets are follow-ups.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
