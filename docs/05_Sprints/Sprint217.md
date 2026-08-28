# Sprint 217: Two tester fixes on the head-to-head (US-431)

**Dates:** 2026-08-28
**Status:** ✅ Complete. 1535 → 1537 tests, ruff clean.

> **Owner, on Cloud:** *"when you change player on head to head, the 'Read N squads' collapses down and you
> have to select it again."* · *"Pronouns should be neutral — 'What you have that he doesn't' should be
> 'What you have that they don't'."*

---

### 🔧 What shipped

**1. The load button latches.** `st.button` returns True only on the run it was clicked, so changing the H2H
rival re-ran the page, found False at the gate above, and collapsed the entire insight layer. Now the click
stores the **league id** and the gate compares against it.

Keying on the league id rather than a bare flag is the whole care here: loading is **N network calls**, one
per manager. A bare `loaded = True` would have carried across a league switch and spent them without anyone
asking — trading a visible annoyance for an invisible cost.

**2. Neutral pronouns, everywhere — not just where it was spotted.** The owner flagged one label. The same
error was in copy shipped the same day: the form windows (*"which way he's going"*, *"his last 3 gameweeks"*),
the price journey (*"he has dropped £0.1m"*), and five Risk Monitor column tooltips that predate both.

A manager id says nothing about who holds it, and neither does a player row. Fixed across the head-to-head,
the trend card, the Risk Monitor and Ask's follow-up example. **Left alone deliberately:** Cole Palmer, a
specific named person, in the module docstring that measured his effective ownership.

---

### 💡 The lesson

> **A flagged instance is a sample, not the bug.**

One label was reported. Grepping the same pattern found nine more, four of them in copy written that same day
— which means it was not a legacy habit being corrected but an active one still producing output. Fixing only
what was pointed at would have left the owner to find the rest one screen at a time.

Both fixes are pinned by tests, because copy corrections are exactly what a later edit reverts without knowing
it was a correction.

### 🧪 Tests

**+2.** The catch-up note carries no gendered pronoun; the Leagues page keeps the latching form and not the
collapse-on-rerun one it replaced.
