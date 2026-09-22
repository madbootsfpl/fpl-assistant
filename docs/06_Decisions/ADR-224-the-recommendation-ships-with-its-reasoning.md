# ADR-224 — The recommendation ships with its reasoning

**Date:** 2026-09-22
**Status:** Accepted
**Builds on:** ADR-089 (Confidence · Edge · Risk), ADR-182 (the mantra), ADR-223 (the tabs)

---

## Context

ADR-223 built a **This week** tab: captain, lineup change, transfer, timing. Four cards, four verdicts. The
owner's response was to paste the web app's version of the same answer — and it is four times as long,
because almost all of it is *why*:

```
Confidence: 77/100 (High)
  Why 77? 85 for your captain, minus 8 for 1 flagged player.
    · Worth 8: João Pedro is flagged — bench or replace him — benching him fields Kusi-Asare (0.0 xP)
    Ceiling this week is 85 — your captain's own number; lifting it means a different captain, not a
    different week.
```

⭐⭐ **A recommendation without its reasoning is a different product.** ADR-182 settled the mantra as
*"Analytics decide. Logic explains. You make the call."* — chosen because it **names the two halves of the
system in the order they run** rather than describing a feeling. A screen showing only the first clause has
quietly dropped the other two, and the third clause is the one that tells a manager the decision is still
theirs.

## Decision

**`explain_gameweek`'s output ships with the plan**, under one `explanation` key.

Returned as its own key rather than merged into the plan, for two reasons: a caller wanting only the
decision can ignore it, and nothing inside it can be mistaken for a number the engine computed.

The phone now renders the whole block — the confidence and its band, **what each flag is worth**, the
**ceiling and why it is the ceiling**, Edge, Risk, per-recommendation reasons on the captain and transfer
cards, and the model note.

### The ceiling is the part most confidence displays leave out

`levers.fixed` says: *"your captain's own number (75/100); lifting it means a different captain, not a
different week."*

⭐ A score with no stated limit invites a manager to chase it. The honest answer is often that it **cannot
rise this week** — and that is not a thing to fix, it is a fact about the week. Showing 59/100 with no
ceiling implies 100 is available.

### The model note is not boilerplate

*"Confidence is a heuristic from the signals, not a probability."* ⚠️ An app that prints a number out of 100
and omits that line is inviting it to be read as a probability, which it is not.

---

## What building it found

### ⚠️ A wrong horizon here is a wrong *sentence*, not a wrong number

`explain_transfer` writes its reason as *"+2.3 to your starting XI over 1 GW"*. Hard-code the window and the
app states, **in words**, a span it did not rank over.

⭐ **The recommendation would be right and its justification false** — worse than either alone, because a
reader checking the working would be misled by the working. Found by mutation: replacing `request.horizon`
with a literal `5` passed every other test in the file.

### Commentary must not take down the match

The explanation is a *reading* of a decision already made. If the sentence cannot be built, the plan is
still the plan. ⚠️ Without that guard the richest screen in the app is also the most fragile, and it would
fail for a reason that changes no recommendation.

### ⚠️ `explain_gameweek` returns dataclasses

Handing those to `json.dumps` raises, so the endpoint would 500 **on the happy path** — a failure that
appears only over HTTP and never in process. ⭐ Exactly the class of bug ADR-219's two-transport test exists
to catch, arriving in a new key.

---

## Also in this change: the pitch markings were drawn from guesses

ADR-223's markings used literal arc angles — `0.46`, `2.22` — chosen because they looked about right on one
screen. ⚠️ **Those are not a property of the drawing; they are a property of the phone it was drawn on**, so
at any other aspect ratio the penalty D swept most of a circle and cut through the cards. The owner saw it
as *"some distortion on rendering"*.

⭐ The fix is geometry rather than a better guess: the arc crosses the box edge at `asin((edge − spot) / r)`,
so the angles **fall out of the shape** and are correct at every size. The centre circle is now clamped to a
share of the **shorter** axis, so it stays a circle that fits rather than one that swallows the midfield on
a narrow phone.

*A constant that encodes the conditions it was measured under* is this project's recurring finding —
ADR-209's tie-break band, ADR-210's exodus threshold, and now a sweep angle.

## Consequences

**Good:** the phone shows the same reasoning the web does, from the same function. The confidence carries
its ceiling and its caveat. The pitch is correct at any size.

**Costs:** the gameweek-plan response grew from ~13 KB to ~18 KB. ⚠️ That is the largest payload in the API
and it is the screen most likely to be opened on mobile data — worth watching, and worth remembering that
`analysis` is 7 KB for the same squad.

**Open:** ⚠️ **nothing in the app can change the team yet.** Captain and Chips remain unbuilt because they
are the first screens that *write*, and FPL publishes no way to do it — see the transfers note below.
