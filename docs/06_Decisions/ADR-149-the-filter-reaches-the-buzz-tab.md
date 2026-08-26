# Architectural Decision Record: The shared filter reaches Community Signals

**Decision ID:** ADR-149
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 204, 2026-08-26). **1429 → 1431 tests, ruff clean.**
**Superseded By / Replaces:** Completes US-407b, which added *"My squad only"* to Trending's four leaderboard
boards but not to the Community Signals tab beside them. No analytics change.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner: *"Community signals should have a my squad filter."*

**My triage of this was wrong in both directions**, and it is worth writing down why. Logged the day before,
it read: *"Trending builds its boards from the player pool without passing through that filter, so this is
wiring rather than new logic."*

Reading the page instead of remembering it:

| surface | honours the shared filter? |
|---|---|
| Most owned · Most transferred in · out · In form | **yes** — `apply_filter(...)` on every board, since US-407b |
| 💬 Talked about / **Community Signals** | **no** |

So the boards were already filtered, and the one tab that was not is precisely the one the owner named — by
its own on-screen heading, *Community Signals*, which I read as a loose description of the page rather than
the name of the section. **The feedback was more precise than my triage of it.**

**And the gap mattered more there than on the boards.** The leaderboards answer *"who is the crowd moving?"*,
a question that is interesting league-wide. Community Signals answers *"who is the crowd talking about?"* —
and the version of that a manager can act on is *"…of my players"*. The tab was missing the only filter that
made it personal.

---

### ✅ Decision

**1. `apply_filter` is applied to the buzz list**, so Team / Position / Player and **My squad only** all reach
it, exactly as they reach the four boards.

**2. Filtered _after_ the scan, not before — deliberately.** Filtering the input would be cheaper, but the
unfiltered total is what makes the filtered number mean anything:

> **6** of 47 players mentioned match your filter

*"6"* alone says nothing. *"6 of 47"* says the crowd is busy and mostly not about you, which is the actual
finding. The scan is cached for 30 minutes, so keeping it costs nothing per view.

**3. An empty result says how to get out of it.** *"None of the 47 players mentioned match your filter —
clear it, or untick **My squad only**, to see the rest."* A filter that silently empties a page, when it lives
collapsed inside a popover (US-424), is indistinguishable from the feature being broken.

### ⚠️ Risks

- **The "Top discussions" list is not filtered**, and should not be: those are *posts*, not players, and there
  is nothing to match a squad against.

### 🧪 Definition of Done

1. **Tests: +2.** The filter narrows the buzz list (driven with a fake RSS feed — no test touches Reddit), and
   the page states the full count beside the filtered one and offers a way back out of an empty result.
2. **Manual smoke** — Trending renders; the buzz button is present and gated as before.
3. **Docs** — this ADR, the Roadmap entry, the Feedback_Log row corrected, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**A triage note written from memory is a guess wearing the clothes of a decision.** Mine said which code path
was at fault, in a confident sentence, without opening the file — and it was wrong about both halves. It then
sat in the Feedback_Log looking like an assessment. Anyone picking the item up would have started from a false
map.

The cheap fix is a rule: **triage may record what the owner said and what it would touch; it may not assert
how the code behaves without looking.** The difference costs one `grep` and saves whoever builds it from
starting somewhere wrong.

Second, smaller: **the owner used the on-screen heading and I read it as prose.** *"Community signals"* is the
literal name of the section, printed in bold on that tab. Feedback that names a thing on the screen is usually
naming *that* thing.
