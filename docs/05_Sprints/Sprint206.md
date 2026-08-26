# Sprint 206: Resolving a player name in free text (ADR-152)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-152. 1435 → 1444 tests, ruff clean. Prerequisite for ADR-151 (extraction).

---

### 🔍 A duplicate row with three bugs behind it

Spike 206 noticed the buzz board listing **"Palmer" twice at 30 mentions each**. That looked like a display
duplicate. Measuring it found three faults on live data:

**Shared surnames — 14.** `Palmer` ×2, `Wilson` ×3, `Phillips` ×3. A bare "Palmer" credited both Cole Palmer
(14.2% owned) *and* Alex Palmer, a backup keeper. Not a duplicate row — a star's buzz attributed to a £4.0m
goalkeeper.

**A name inside another name — 90.** `James` inside "James Maddison"; `Keane` **and** `Lewis` both inside
"Keane Lewis-Potter"; `Hall` inside "Kiernan Dewsbury-Hall". *"James Maddison out for two weeks"* counted as a
mention of **Reece James**.

**And ambiguity was resolved silently** rather than dropped.

### 🔧 What shipped

`analytics/names.py`: one index of full names and surnames, **longest first**, with matched spans consumed so
a shorter pattern cannot match inside a longer one. Ambiguous surnames are credited only to a **clear
favourite** — owned ≥1% *and* ≥3× the next candidate — and dropped otherwise.

Both thresholds are measured. Across the 14 collisions, **9 have a clear favourite and in the other 5 nobody
owns any candidate**, so staying quiet costs nothing anyone would have read.

On the 112-headline corpus: Palmer once at 7 mentions, Maddison correctly credited, no duplicates.

---

### 💡 The lesson

> **When a display bug turns out to be a counting bug, the display is the least of it.**

The visible fault was one name listed twice. Underneath were **90** cases of one player's name hiding inside
another's, quietly miscounting a board that has shipped since Sprint 067. Nobody would have found those by
looking at the board — **a wrong count looks exactly like a right one.** The duplicate was simply the only
symptom with a face.

Worth pairing with the sprint that produced it: this came out of a *spike for a different feature*. ADR-151's
extraction needed a resolver, checking the resolver exposed the counter, and the counter had been wrong for
months. **Building something new is one of the more reliable ways to audit something old.**

### 🧪 Tests

**+9.** Each of the three faults pinned with its real case — the Maddison/Reece James headline, the two
Palmers, and a genuinely ambiguous surname that must resolve to silence; both thresholds required (an
infinite ratio over nobody is still nobody); short names left alone; repeats counted; empty inputs safe. Plus
a `community_buzz` test using the exact headlines that exposed the bug.
