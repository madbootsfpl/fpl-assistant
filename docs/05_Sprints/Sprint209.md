# Sprint 209: Bench a departing player — but only inside a window (ADR-154)

**Dates:** 2026-08-27
**Status:** ✅ Complete — ADR-154. 1460 → 1466 tests, ruff clean.

> **Owner:** *"Yes, do it scoped to reported-leaving only… **That said we could get a reported to be leaving
> outside the window and we should not react in that case.**"*

---

### 🔧 What shipped

A reported leaver is ranked as if he scores nothing — **for selection only**. A local copy of the xP map,
zeroed for those players, handed to `best_legal_xi` and nowhere else. He is dropped from the captain pool too,
because a captained player who is not there costs double.

And it applies **only while an English transfer window is open**, with the windows as data:

```
window OPEN  (27 Aug):  Watkins in the XI? False  ·  replacements: ['Watkins']
window SHUT (15 Oct):   Watkins in the XI? True   ·  replacements: none
```

The gate is computed once, at the top of `gameweek_plan` — it changes captain, lineup *and* transfer, and
working it out three times is how three answers drift apart.

---

### ⚠️ The incompleteness we chose

**Other countries' windows do not match England's.** The Saudi league has repeatedly stayed open for weeks
after the Premier League shut — which is *exactly* the Watkins → Al-Hilal case this was built for. So in early
September this gate can suppress a **true** signal.

Right direction to be wrong in: a suppressed signal costs silence, an acted-upon one costs a transfer. There
is a test asserting the false negative deliberately, so nobody "fixes" it without reading why.

---

### 💡 The lesson

> **The owner's caveat was worth more than the feature.**

The ask — bench a departing player — was three lines of code. The condition attached to it is what stops the
feature being wrong for ten months of the year: transfer stories run constantly, and without the gate every
October rumour would have benched a player going nowhere.

Generalising: **when a new signal changes a decision, the first question is not "is the signal true?" but "is
there anything anyone can do about it right now?"** A true fact that cannot be acted on is noise wearing a
fact's clothes — and it is more dangerous than an obvious error, because it survives review.

Worth noting where this came from: the owner supplied the constraint, unprompted, in the same sentence as the
approval. Three of the last four sprints have been improved by something in the feedback rather than something
in the plan.

### 🧪 Tests

**+6.** The window boundaries; a leaving report outside one changes nothing; omitting the date skips the check
(the gate belongs in one place, not three); the documented Saudi false-negative, asserted on purpose; and —
driven through `gameweek_plan` — a leaver zeroed **for selection only** with nobody else touched and never
captained, versus treated completely normally in October.
