# Architectural Decision Record: Act on the answer, don't move the tab

**Decision ID:** ADR-174
**Date:** 2026-09-02
**Status:** ✅ **Accepted — designed with the owner in conversation, built** (Sprint 235, 2026-09-02).
**1692 → 1696 tests, ruff clean.**
**Superseded By / Replaces:** Completes **ADR-171** (which put the recommendation on the golden page but not
the action). **Upholds ADR-115** rather than reversing it — the Transfer tab keeps every control it has.
**No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> *"We can't transfer on that page, we need to go to our sub-tab. Would like your thoughts as to whether that
> should change, or are we in danger of making our golden page too long?"*

**Both halves of the owner's question are right, and they point in opposite directions.** ADR-171 put the
week's answer on My Squad — including *which transfer to make* — and then made the reader cross to another
tab to do the thing they had just been told to do.

But the page is long. ADR-115 called My Squad *"the app's densest page — the golden page, but a wall"* at
**14 blocks**, and removed an in-page transfer expander as **"a real redundancy"**. Measured today it is
**41 blocks, 9 interactive** — roughly three times what was called a wall, because ADR-171 added three
sections with the owner's sign-off.

---

### 🔬 The reframe that resolved it

**The recommendation is already there; only the action was missing.** The block reads:

```
Transfer: Senesi (TOT) → De Cuyper (BHA)  (+2.5 XI xP next GW)  · Confidence 86/100
          Longer view: +10.4 XI xP and still ahead over the next 5 GWs
```

So the question is not *"should transfers live on the golden page"* — a sentence naming a specific swap
already does. It is *"should you be able to act on advice you are already reading"*. That is **one button,
not a tab**.

The Transfer tab is not small: dead-slot replacements, a free-transfer count, the watchlist, a coordinated
multi-move plan, a ranked swap list, a position filter and a manual out/in picker — **~10 more widgets**.
Folding it in would re-create precisely the redundancy ADR-115 removed, onto a page three times denser than
when it was removed.

---

### ✅ Decision

**One button in the *This week* block: `🔄 Apply: {out} → {in}`.**

**1. It applies the object the text was rendered from.** `AskResult` gains a `plan` field — mirroring
`squad`, which a build answer has carried since ADR-062 for exactly this reason — so the surface acts on the
same dict `render_gameweek_plan` printed. **Recomputing the swap at the surface would be a second search that
could legitimately return a different move**, leaving the button and the sentence above it naming different
players. A test pins that they match.

**2. It names both players.** The block is a wall of text on a phone; a bare *"Apply"* at the end of it is a
control whose effect you must scroll back up to remember.

**3. The Transfer tab loses nothing.** This is ADR-135's own division of labour applied to a recommendation
rather than a shirt:

> **The entity owns actions on things you have. The pickers own finding things you don't.**

The golden page owns *acting on the one move already named*; the tab owns *finding alternatives* — filters,
the manual picker, multi-move plans, the watchlist. A test asserts the tab still carries its picker, because
"we did not remove anything" is the kind of claim that quietly stops being true.

---

### 🔀 Alternatives Considered

- **Move the Transfer tab onto My Squad** (the literal reading of the ask). **Rejected on measurement:** ~10
  widgets onto a 41-block page, re-creating the redundancy ADR-115 named. The owner's own instinct — *"are we
  in danger of making our golden page too long?"* — was correct for this version.
- **Leave it; the tab is one tap away.** Rejected: the page tells you the move and then withholds the doing,
  which is the specific complaint. One tap is cheap; being told what to do and not being able to do it reads
  as an oversight.
- **A confirmation step.** Rejected for consistency — the Transfer tab's own *Apply this transfer →* has
  none, and adding a confirm here alone would imply this button is more dangerous than the identical one
  three tabs away. See the risk below; it is real but it is not *new*.
- **Show the top three moves with a button each.** Rejected: that is the Transfer tab, rebuilt inline. The
  answer block's job is to name **one** thing to do.

---

### 🧭 Consequences

**Positive** — closes the gap ADR-171 opened; one widget, not ten; reuses `apply_transfer` and its legality
check and budget warning unchanged; the tab is untouched; the button cannot disagree with the text.

**Negative / risks (mitigations)** — a consequential, unconfirmed action now sits near the top of the
most-visited page, more exposed than the same button three tabs deep (*mitigation:* it names both players so
it cannot be tapped blindly, the squad lives in the session and can be re-imported or re-downloaded, and the
legality check still refuses an illegal result). **The answer block becomes partly interactive** — it read as
advice and now contains a control, which is a real change in what it *is* (*mitigation:* stated here rather
than discovered; one action, on the one recommendation, and nothing else in the block moved). The page grows
by one more widget on a page already three times ADR-115's "wall" (*mitigation:* the owner asked and the
alternative was ten).

---

### 🧾 Follow-ups

- **The strip question is still open and deliberately not bundled here.** Bank + free transfers on the My
  Squad strip: we hold both numbers, but that strip was cut **5 → 3** (US-404) for slivering on mobile and
  ADR-163 rebuilt it to wrap. It wants its own gate.
- **Watch this one.** ADR-135 optimised this page's density, hit its number exactly, and was reverted the
  same day. If the button reads as clutter or gets mis-tapped, that is a legitimate reason to pull it — and
  the reason should be written down here, as ADR-135's was.
