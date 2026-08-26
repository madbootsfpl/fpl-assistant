# Sprint 204: The shared filter reaches Community Signals (ADR-149)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-149. 1429 → 1431 tests, ruff clean.

> **Owner:** *"Community signals should have a my squad filter."*

---

### 🔍 My triage was wrong in both directions

Logged the day before, it read: *"Trending builds its boards from the player pool without passing through that
filter, so this is wiring rather than new logic."* Reading the page instead of remembering it:

| surface | honours the shared filter? |
|---|---|
| Most owned · transferred in · out · In form | **yes**, since US-407b |
| 💬 Talked about / **Community Signals** | **no** |

The boards were already filtered. The one tab that was not is exactly the one the owner named — by its
on-screen heading, **Community Signals**, which I had read as a loose description of the page rather than the
name of the section.

**The feedback was more precise than my triage of it.**

And the gap mattered more there than on the boards. Leaderboards answer *"who is the crowd moving?"* — fine
league-wide. Community Signals answers *"who is the crowd talking about?"*, and the actionable version is
*"…of my players"*. The tab was missing the only filter that made it personal.

### 🔧 What shipped

`apply_filter` on the buzz list, so Team / Position / Player and **My squad only** all reach it.

Filtered **after** the scan rather than before, deliberately: the unfiltered total is what makes the filtered
number mean anything — *"**6** of 47 players mentioned match your filter"*. Six alone says nothing; six of
forty-seven says the crowd is busy and mostly not about you. The scan is cached 30 minutes, so keeping it is
free.

An empty result now says how to get out of it, because a filter living collapsed inside a popover (US-424)
that silently empties a page is indistinguishable from the feature being broken.

---

### 💡 The lesson

> **A triage note written from memory is a guess wearing the clothes of a decision.**

Mine named the faulty code path in a confident sentence without opening the file, was wrong about both halves,
and then sat in the Feedback_Log looking like an assessment. Anyone picking the item up would have started
from a false map — and the map was worse than none, because it was specific.

The rule that follows: **triage may record what the owner said and what it would touch; it may not assert how
the code behaves without looking.** That costs one `grep`.

Second, smaller but repeatable: **the owner used the on-screen heading and I read it as prose.** "Community
signals" is the literal bold label on that tab. Feedback that names something visible on screen is usually
naming *that* thing, not gesturing at the area.

### 🧪 Tests

**+2.** The filter narrows the buzz list, driven with a fake RSS feed so no test touches Reddit; and the page
states the full count beside the filtered one and offers a route back out of an empty result.
