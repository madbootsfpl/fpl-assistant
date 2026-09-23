# ADR-274 — The API speaks text, not Streamlit

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"your trending comment is not correct"*, with a screenshot
**Fixes:** ADR-269/271 (the boards)

---

## What was actually on screen

The caveat at the top of Trending rendered as:

> `**12 players**` stand out on two or more of these boards at once. That is a reason to look, `**not a
> points projection**` …

**Literal asterisks**, at the top of the screen the owner had just asked to be made prominent.

⭐ The engine's notes (`scout_note`, `watch_note`) were written for a page that **renders** markdown. The
phone renders none. ⚠️ *A string formatted for one renderer is a string formatted for one renderer* — and
the transport is where that gets undone, exactly as ADR-271's *"boards below"* wording was, because the
Streamlit page it was written for still renders it correctly.

## ⚠️⚠️ And I had explained the report away

Told the headings were missing, I replied that they were present and suggested which tab he must have
tapped. He sent a screenshot showing he was exactly where I said, with a visible defect in it that I had
not looked for.

⭐ **A report about a screen is evidence about that screen; a theory about what the reporter did is not.**
The widget test I had written was real and passed — it just was not testing the thing he was looking at.

## Decision

`plain()` strips emphasis in the service layer. ⚠️ **Bold before italic**, or `**x**` reads as an italic
`*` wrapping `*x*`.

## ⚠️⚠️ The sweep I wrote to catch this did not catch it

A guard was added to walk every endpoint's answer and fail on markdown. Re-broken to check it, **only the
named test fired** — the sweep passed, because the shape sweep it borrows builds **one** trending board
and the markdown was on two others.

⭐⭐ *A sweep that covers the surfaces it was pointed at is the exact failure a sweep exists to prevent*
(ADR-184) — found only by re-breaking a guard after writing it, which is now the third time that step has
paid for itself this week. The fixture derives **every** board from the service.

📌 `_` is deliberately not treated as markdown: it appears inside `web_name` and `by_gameweek`, and ⭐ *a
rule that fires on real data is a rule someone turns off.*

## Verification

* **4 Python tests** — the full-API sweep, the two notes by name, the bold-before-italic ordering, and one
  asserting the sweep can fail at all (⭐ *a guard never shown to fail is a guard nobody has tested*).
* **Re-broken twice**: once to discover the sweep's blind spot, once to confirm the widened fixture closes
  it.
* 2,570 Python · 238 Dart.
