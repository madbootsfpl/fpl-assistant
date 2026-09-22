# ADR-232 — Signals, and a memory the web cannot have

**Date:** 2026-09-22
**Status:** Accepted
**Closes:** the Signals review (raised 2026-09-22, deferred, then asked for)
**Builds on:** ADR-150 (the page), ADR-225 (the draft store)

---

## Context

Signals was filed under *"on the web"* in ADR-228 and immediately recategorised: it answers **"what should
I know?"** — FPL's own news, reported moves, an unexplained sell-off, headlines — which is time-sensitive
and actionable before a deadline. ⭐ That is the **decision layer**, not research.

The checklist recorded the review with a sharper question than *"port Signals"*:

> ***"Does the phone need a what-changed view?"*** — the app already carries Signals' *conclusions* on your
> own players (the flags, the ✈) and none of its *news*.

## Decision

**`POST /api/v1/squad/signals` — squad-scoped, ordered by evidentiary strength.**

⭐ **Squad-scoped is the whole difference from the web page.** That browses the market; this answers the
question a manager opens a phone to ask: *what should I know about the fifteen I hold?*

### ⭐⭐ The ordering is the design

ADR-150 built the web page around one idea: these sources are **not equally reliable**, and putting them in
one list without saying so *"would present a Reddit rumour beside an injury FPL confirmed."*

| tier | kind | what it is |
|---|---|---|
| 1 | `official` | FPL's own `news`. **A fact** — it drives `status`, and therefore every xP in the app. |
| 2 | `departure` | the press and the crowd agreeing he is leaving (ADR-153/155). FPL still calls him available. |
| 3 | `exodus` | **our own inference** (ADR-146): a sell-off our fields cannot explain. |
| 4 | `headline` | one named outlet's reporting (ADR-093). |

⚠️ Each signal carries its `kind`, so a client **cannot** render them as one undifferentiated list without
deliberately discarding the distinction. ⭐ The exodus label is *"Unexplained"* — a statement about **our
own data**, which is the honest thing an inference can say about itself.

---

## ⭐⭐ The phone can do something the web cannot: remember

The server has no idea when you last looked. But every signal carries a **stable key**, and the device
already has a store (ADR-225's draft). So the app remembers which signals it has shown, and badges the rest
**new**.

⭐ **That is the *what-changed* view the checklist asked for, and it needed no new data at all** — only the
observation that the client is the thing with a memory of this user.

⚠️ Marked seen **on render**, not on fetch: saving before showing would mean the badge never appears. And
the set is **replaced, not merged** — a key that stops coming back is a signal that has passed, and keeping
it forever grows a list nobody reads until it slows the thing it was meant to speed up.

---

## ⚠️ Where it lives, and the better answer I did not build

Signals is in **More**, not the bar. ADR-230's rule: *frequency earns a slot, and the audit's §6 priority
decides* — and Signals is not in the first release either.

⭐ **But the right answer is probably neither.** The value of a signal is **being told**, not going to look
— which is precisely why a phone suits it. A badge on the pitch when something new appears would beat any
menu placement.

⚠️ **Not built, because it costs a round trip on the landing screen** — the one whose speed ADR-217/218
spent a day earning. Doing it properly means folding signals into `my-team` or accepting a second call, and
that is a measurement, not a guess. Recorded as the next step rather than assumed away.

---

## Also

**A quiet week is an answer.** `checked` reports how many players were examined, so *"nothing to report
across your 15"* reads as news rather than as a screen that failed to load.

⚠️ **`-2,762 managers sold him this week.`** `net` is negative by construction — transfers out minus in —
and the sign is already carried by the word *sold*. Caught on the first real render.

## Verification

* Suite **2,267 passed**; the shape sweep's completeness check demanded `signals` before going green.
* The ordering test is **constructed, not sampled**: a seed with one kind of signal cannot demonstrate an
  ordering, so a departure and an exodus are stubbed onto two different players.

## Consequences

**Good:** the phone answers *what should I know?* about your own squad, distinguishes a fact from an
inference, and knows what it has already told you.

**Costs:** ⚠️ two stores now use `shared_preferences` (drafts, seen signals). That is still one small
document each — but it is the point at which "a real database" starts becoming a question rather than a
premature one.
