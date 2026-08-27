# Architectural Decision Record: Bench a departing player — but only while a window is open

**Decision ID:** ADR-154
**Date:** 2026-08-27
**Status:** ✅ **Accepted — owner-gated, built** (Sprint 209, 2026-08-27). **1460 → 1466 tests, ruff clean.**
**Superseded By / Replaces:** Completes ADR-153, which recommended replacing a departing player *and* would
still have started him. Adds the window gate the owner asked for. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

ADR-153 left one thing open deliberately: the plan recommended replacing Watkins **and would still pick him in
the XI**, because `best_legal_xi` ranks on `decision_xp` — which rates him 4.3, since FPL still calls him
available. Coherent (he is in the squad until transferred) and odd to read.

Fixing it means letting a **headline** move a team-selection decision, which is a line this project had not
crossed. The owner's gate, and the condition attached to it:

> Yes, do it scoped to reported-leaving only — I don't think it's a huge risk as it will only apply during
> transfer windows. **That said we could get a reported-to-be-leaving outside the window and we should not
> react in that case.**

That caveat is the more valuable half. A club can only sell a player while a window is open, so a September
story about a January move **changes nothing about this gameweek** — he plays on Saturday regardless. Acting
on it would cost a real transfer for a move that cannot happen yet.

---

### ✅ Decision

**1. A reported leaver is ranked as if he scores nothing — for selection only.** A **local copy** of the xP
map, zeroed for those players, passed to `best_legal_xi` and nowhere else. `decision_xp` is untouched, the
stored value is unchanged, and every other surface still shows his real projection.

**2. He is removed from the captain pool too.** Same reasoning, worse outcome if it happened — a captained
player who is not there costs double.

**3. …and only while an English transfer window is open.** `fpl_rules.transfer_window_open(today)`, with the
windows as **data** rather than a buried condition:

```python
TRANSFER_WINDOWS = (("06-10", "09-01"),   # summer
                    ("01-01", "02-02"))   # winter
```

Verified both ways on the live squad:

```
window OPEN  (27 Aug):  Watkins in the XI? False  ·  replacements: ['Watkins']
window SHUT (15 Oct):   Watkins in the XI? True   ·  replacements: none
```

**4. The gate is computed once, at the top of `gameweek_plan`.** It changes three answers — captain, lineup,
transfer — and working it out three times is how they drift apart.

### ⚠️ A known incompleteness, written down rather than discovered

**Other countries' windows do not match England's.** The Saudi Pro League has repeatedly stayed open for weeks
after the Premier League shut — which is *exactly* the Watkins → Al-Hilal case this was built for. So in early
September this gate can suppress a **true** signal.

That is the right direction to be wrong in: a suppressed signal costs silence, an acted-upon one costs a
transfer. And it is why `TRANSFER_WINDOWS` is a list of ranges that can gain a row, rather than a hard-coded
pair. A test asserts the false negative on purpose, so nobody "fixes" it without reading why.

- **Dates shift by a day or two each season**, so they live in one named place.
- **A free agent can sign outside a window.** Rare enough to ignore, and it fails safe (we stay quiet).

### 🧪 Definition of Done

1. **Tests: +6.** The window boundaries; a leaving report outside one changes nothing; omitting the date skips
   the check; the documented Saudi false-negative; and — through `gameweek_plan` — that a leaver is zeroed
   **for selection only** while nobody else is touched and he is never captained, versus treated completely
   normally in October.
2. **Manual smoke** — the live squad, both dates, verified above.
3. **Docs** — this ADR, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**The owner's caveat was worth more than the feature.** The ask — bench a departing player — was three lines.
The condition attached to it, *"we should not react outside the window"*, is the part that stops the feature
being wrong for ten months of the year: transfer stories run constantly, and without the gate every October
rumour would have benched a player who was going nowhere.

Generalising: **when a new signal changes a decision, the first question is not "is the signal true?" but
"is there anything anyone can do about it right now?"** A true fact that cannot be acted on is noise wearing
a fact's clothes.
