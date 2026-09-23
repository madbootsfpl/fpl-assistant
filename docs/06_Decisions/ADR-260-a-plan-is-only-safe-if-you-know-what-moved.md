# ADR-260 — A plan is only safe if you know what moved under it

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"how do we get changes to persist in the app — people like to manipulate their
teams, wait till near deadline and then make the changes **if nothing else external has happened that
might influence change**."*
**Builds on:** ADR-225 (drafts persist), ADR-232 (the device remembers), ADR-255 (the signal keys)

---

## Context

The question has two halves and they had very different answers.

✅ **Persistence already worked.** ADR-225's draft survives closing the app and carries the three things a
manager actually changed — the **transfers**, the **bench order** and the **armbands** — with a `savedAt`
stamp, validated on return against the manager, the gameweek and the base squad.

⚠️ **The second half did not exist at all.** *"If nothing else external has happened"* is the condition the
whole workflow turns on, and the app had no way to answer it. ⭐ *A plan you come back to is only safe to
execute if you know what changed underneath it* — and the app knew, and never said.

## Decision

**A plan records what was known about your players when it was made.**

`Draft.signalKeys` holds the signal keys current at the moment of saving. Coming back, *what has happened
since* is a **set difference**.

⭐⭐⭐ **No clock and no server-side memory.** Signal keys have been stable since ADR-232, so the device can
answer a question the server structurally cannot — it has no idea when you last looked. This is the third
feature built on that split, and the cheapest.

### The reassurance is the feature, not the warning

> ✅ *Nothing has happened to your players since you planned this, 3 days ago.*
> ⚠️ *2 things have happened to your players since you planned this, 3 days ago.*

⭐ **Both are shown.** An app that spoke up only when something *had* happened would leave silence meaning
two different things — *nothing happened* and *nobody checked* — and only one of those is safe to act on.
⚠️ The message names **what** was checked, because *"nothing has changed"* without a subject invites
*"nothing about what?"*

It replaces the general signals nudge while a plan is live: the same news, asked as the sharper question —
not *"is there news?"* but *"is the plan I am about to execute still the plan I made?"*

### ⚠️ Two directions that had to be chosen deliberately

**An older plan treats everything as new.** A draft saved before this shipped has no record, which reads
as *"nothing was known"*. ⭐ *Over-reporting a change invites a second look; under-reporting one lets a plan
be executed blind.*

**Editing a plan does not silence it.** ⚠️⚠️ A transfer or substitution **carries** the original keys
rather than re-reading the current ones — otherwise *the act of editing the plan would empty the warning
the plan needs on its way back*, and it would do it silently. There are tests for both paths.

**And the difference runs one way only**: what is here now that was not then. A signal that has since gone
quiet is not news about your plan.

## Consequences

📌 **This is device-local, and that is correct** — not a limitation waiting on accounts (ADR-259). *"New
since you last looked"* is a fact about a screen, not about a person, and a draft is a scratchpad rather
than a document.

⭐ It also answers the *"what persists?"* question honestly for a tester: **your plan does, on this phone,
until the gameweek turns or you make the move for real.**

## Verification

* **9 Dart tests** across three groups: that a plan comes back whole days later; that a plan for a gone
  gameweek is refused; and the change report — nothing new, something new, something gone quiet, an older
  plan, and both editing paths.
* **5/5 mutations killed**: the plan not recording what it knew; a transfer resetting it; the difference
  computed backwards; the difference reporting everything always; and an old plan treated as fully
  informed.
