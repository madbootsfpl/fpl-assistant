# ADR-228 — "More" is for the app, not for everything else

**Date:** 2026-09-22
**Status:** Accepted
**Revises:** ADR-223's bottom bar

---

## Context

> *"Do we need a more option on the bottom right too? We have lots of other functionality that users can
> access."*

The web app has **eight** pages. The phone had four tabs, one of them a greyed placeholder.

## The answer is yes — but not for the reason in the question

⭐⭐ **"We have lots of other functionality" is the argument *against* a More drawer, not for it.** The
mobile audit §6 is explicit: *the mobile app is the decision layer; the web app stays the exploration
layer.* A More list that grew to eight items would undo that positioning on the smaller screen.

⚠️ This project has already learned it the other way round. **ADR-166** cut the web sidebar from twelve to
nine, ordered by frequency. **ADR-167/170** answered *"we need another board"* with a **reader** instead. A
phone is the wrong place to reverse both.

### The real reason: the app had nowhere to put a setting, and one of them was lying

🔴 **`_freeTransfers` was `final int = 1`.** No control, no way to change it.

That is **ADR-191's exact failure, reintroduced.** ADR-191 exists because the app once hard-coded free
transfers and bank to 1 and £0.0m while the Transfer tab collected them three tabs away — *"the surface a
manager reads was advising a position he was not in."* I built the endpoint to accept the number, then gave
the manager no way to say it. ⭐ *Because there was nowhere to put it.*

The manager id had the same problem from the other end: it was jammed into the **title bar**, which made a
setting look like a title.

## Decision

**The bar is `My team · Transfers · This week · More`**, and More holds the app's own housekeeping:

* **Your team** — manager id, and **free transfers 0–5**, with the reason it must be asked for.
* **This gameweek** — bank, squad value, chip, deadline, each labelled *from FPL*. ⭐ Two of the three
  numbers in the header are FPL's and one is yours; a reader cannot tell by looking, so it says so.
* **Not here yet** — Chips and Players, named with **why**, not greyed.
* **On the web** — what lives there, and ⭐ **the positioning said out loud**: someone who cannot find Team
  DNA should learn it is a decision, not an oversight.
* **About** — the mantra and the disclaimer (ADR-103's legal hygiene).

### ⚠️ This reverses ADR-223's own argument, deliberately

ADR-223 kept Chips in the bar greyed rather than hidden, arguing *"a bar that grows items later moves
everything under the user's thumb."*

⭐ **That argument held while the fourth slot was a placeholder. It stops holding when there is a real
fourth item.** Four working tabs beat three plus a dead one — and the move is cheapest now, before anyone
has built muscle memory for a button that does nothing. Chips is named in More until it is built and earns
a slot back.

*A prior ADR is a fact about a version, not a law* (ADR-180) — and the version it was a fact about had no
fourth screen.

---

## Consequences

**Good:** free transfers is settable, so the week's plan stops assuming; the manager id is a setting rather
than a title; every tab in the bar works, so nothing is greyed and nothing is a promise.

**Costs:** ⚠️ More is now the easiest place to put anything, which is exactly what makes it dangerous. The
positioning note inside it is aimed as much at whoever adds the next item as at the reader.

**Open:**

* **Feedback has no path on the phone.** The web form POSTs to `FPL_FEEDBACK_WEBHOOK`, a secret the client
  must not hold — so it belongs behind the API, not in the app. ⚠️ Worth solving: a beta tester on a phone
  is *more* likely to notice something and *less* likely to be near a laptop.
* **Players** is in the audit's first release and is the next thing to port.
* **Chips** remains the one squad question with no answer here.
