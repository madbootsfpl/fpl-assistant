# Sprint 213: The tap leaves the pitch (ADR-158)

**Dates:** 2026-08-27
**Status:** ✅ Complete — ADR-158. 1496 → 1504 tests, ruff clean. Preview signed off before commit.

> **The roadmap, written by the sprint that failed:** *"a row tap that selects is ADR-133's shape and is still
> wanted; a row tap that opens a menu is this ADR again."*

---

### 🔧 What shipped

The Team DNA league scan (20 clubs, ADR-134) rendered as a strip you could read but not act on — picking the
club you had just read about meant leaving the rows and finding it again in a dropdown. Now a row tap selects
it, writing the same state the dropdown writes, so the DNA card below is reused entirely unchanged.

The row element **is** the anchor: `.yt-row` is a four-column grid, and an `<a>` inside it would become the
single grid item and collapse the layout. There is a test for that.

The picker stays permanently — `AppTest` still drives the page, keyboard users keep a path, and a missing
component degrades to exactly the old page. The caption offers the gesture **only when the gesture works**,
which is ADR-133's finding that an invisible fallback is right for users and wrong for diagnosis.

The identical-looking Health strip taps too. Same renderer; a gesture that worked on one and not the other
would read as a bug rather than a boundary. Raised as a scope call, signed off with the preview.

---

### 💡 The lesson

> **A reverted sprint is only wasted if it doesn't leave a rule behind.**

ADR-135 built an action menu on the shirt, hit its density target exactly (6-7 widgets → 3), and was still
worse on desktop *and* iPhone — so it was reverted the same day. What it left behind was a sentence naming
which half was worth keeping. This sprint was largely the act of reading that sentence and doing what it said,
a month later, on a surface ADR-135 was never about.

A smaller one, from the refactor: generalising `render_tappable_pitch` surfaced a bug fix sitting inside it —
the replayed-click guard, which stops the component's last click being re-applied on every rerun and is why
the picker can override a tap at all. Nothing about it was pitch-specific, and whoever built the second
tappable surface would have had to rediscover it. **Code that is copied loses its bug fixes; code that is
shared keeps them.**

### 🧪 Tests

**+8.** A row tap selects that club; a replayed click can't overwrite the picker; unknown, stale and
wrong-prefix ids ignored; a missing component selects nothing and draws nothing; the clickable row *is* the
anchor and the plain strip has no anchors at all; only the selected row is outlined; plus an `AppTest` pass
asserting the page offers the gesture when live, hides it when not, and keeps the picker either way.
