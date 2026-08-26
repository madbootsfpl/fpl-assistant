# Architectural Decision Record: Resolving a player name in free text

**Decision ID:** ADR-152
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 206, 2026-08-26). **1435 → 1444 tests, ruff clean.**
**Superseded By / Replaces:** Fixes the mention counting in `community_buzz` (ADR-059). **Prerequisite for
ADR-151** — extraction is only as safe as the resolver underneath it.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Spike 206 noticed the buzz board listing **"Palmer" twice, at 30 mentions each**. It looked like a display
duplicate. It was not — it was the resolver, and measuring it found **three** distinct faults on live data:

**1. Shared surnames — 14 of them.** `Palmer` ×2, `Wilson` ×3, `Phillips` ×3. Each player was regexed
independently, so a bare "Palmer" credited **both** Cole Palmer (14.2% owned) *and* Alex Palmer, a backup
goalkeeper. The board did not just show a duplicate row; it attributed a star's buzz to a £4.0m keeper.

**2. A name inside another name — 90 of them.** A `web_name` appears inside a *different* player's full name:

| pattern | matched inside |
|---|---|
| `James` | "James Maddison" · "James Trafford" · "James Justin" |
| `Keane` **and** `Lewis` | "Keane Lewis-Potter" |
| `Hall` | "Kiernan Dewsbury-Hall" |
| `Silva` | "Emersonn Correia da Silva" |

So *"James Maddison out for up to two weeks"* counted as a mention of **Reece James**.

**3. Ambiguity resolved silently rather than dropped** — the counter simply credited everyone who matched.

This was worth fixing on its own, and it is also the floor ADR-151 stands on: extracting *"Watkins → Al-Hilal"*
from a headline is worthless if the name lands on the wrong player.

---

### ✅ Decision

**1. `analytics/names.py` — longest-match-first, with span consumption.** Full names and `web_name`s go into
one index sorted longest-first; a matched span is blanked so a shorter pattern cannot match inside it. "Cole
Palmer" claims those eleven characters, so the `Palmer` pattern never sees them, and "James Maddison" stops
being a Reece James sighting.

**2. Ambiguity resolves to silence, not to a guess.** A bare surname shared by several players is credited
only to a **clear favourite**: owned ≥ **1.0%** *and* ≥ **3×** the next candidate. Otherwise the mention is
dropped.

Both thresholds are measured, not chosen. Across the 14 live collisions:

| | |
|---|---|
| a clear favourite exists | **9** — Palmer 14.2 vs 4.5 (3.2×), Hughes 11.1 vs 0.1 (111×), James 10.1 vs 0.1 |
| nobody owns any candidate | **5** — Kamara, King, Patterson, Dasilva, Johnson |

So the rule loses **nothing anyone was going to read**: where it stays quiet, no candidate is owned by 1% of
managers. Ownership is the proxy because in r/FantasyPL "Palmer" means the midfielder a seventh of the game
owns, not the goalkeeper — but only when the gap is stark enough to be a fact rather than a hunch.

**3. Both thresholds are needed, and the test says why.** A player nobody owns is never a favourite however
far ahead he is (an infinite ratio over nothing is still nothing), and two well-owned players close together
stay ambiguous. Palmer at 3.2× sits just over the line — noted, because it is the case the rule was written
for and the one most likely to move.

### ⚠️ Risks

- **Ownership shifts through the season.** A favourite today may be a coin-flip in October. The constants sit
  beside the measurement that produced them — the same GW4-6 re-check as the other four.
- **A full name absent from the text still falls back to the surname rule.** Deliberate: most headlines say
  "Palmer", not "Cole Palmer" (measured — 7 bare vs 4 full in the corpus).

### 🧪 Definition of Done

1. **Tests: +9.** Each of the three faults pinned with its real case; both thresholds required; short names
   left alone; repeats counted; empty inputs safe. Plus a `community_buzz` test that the board can no longer
   list a shared surname twice, using the exact headlines that exposed it.
2. **Manual smoke** — the 112-headline corpus: Palmer now appears **once** at 7 mentions, Maddison is credited
   correctly, and no duplicates remain.
3. **Docs** — this ADR, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**A duplicate row is a symptom; "counting mentions" is where the bug lived.** The visible fault was one name
listed twice. Underneath were 90 cases of one player's name hiding inside another's, silently miscounting a
board that has been shipping since Sprint 067 — and nobody would have found them by looking at the board,
because a wrong count looks exactly like a right one.

The general form: **when a display bug is a counting bug, the display is the least of it.** The duplicate was
the only symptom with a face; the other 90 were invisible by construction.
