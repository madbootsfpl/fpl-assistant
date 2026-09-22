# ADR-241 — The armband did not survive the other feature

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback on the phone build, item 1 — *"My team, C doesn't hold"*
**Builds on:** ADR-225 (drafts), ADR-230 (a tap sets the armband)

---

## Context

The armband code was fine. It serialised `captain_id`, restored it on reload, survived a restart, and
applied cleanly at render. I read the whole path twice and found nothing, because nothing was there.

⭐⭐⭐ **What the C did not survive was the other feature.** `_planSwap` — the one-click transfer the owner
had just called the best thing in the app — built a **brand-new `Draft`** and never carried the armbands
across. So the sequence he uses most, *pick a captain, then apply a suggested transfer*, took the armband
off without saying so.

⚠️ **This is why reading found nothing.** Every line about armbands was correct. The fault was in a
function that is not about armbands at all, and which therefore nobody thought to check.

## Decision

**Three fixes, and the third is the one that matters.**

### 1. A transfer carries the armbands, and drops one whose player has left

⭐ Carrying an armband forward is only right while the player is still yours. `armbandsWithin(squad)`
returns each letter only if its wearer is still in the XV — *a C on a player you have sold is worse than no
C*, because it survives into the pitch, the plan and the next reload, describing a squad that no longer
exists.

### 2. `copyWith` can clear an armband, not only set one

⚠️⚠️ `captainId ?? this.captainId` means **passing `null` asks for "leave it alone"**, so the caller trying
to empty the vice slot silently kept it — and promoting your vice left one player wearing **C and V at
once**, which FPL would reject. ⭐ *An optional argument cannot say "unset" and "no opinion" with the same
value.* Explicit `clearCaptain` / `clearViceCaptain` flags now do it.

### 3. ⭐⭐ The swap logic moved out of the widget

`Draft.swap(...)` is a named static function that `main.dart` and the tests both call.

⚠️ **Logic inside a `State`'s private method cannot be called by a test, so its test has to *re-describe*
it** — and a re-description drifts from the thing it describes without either side going red. The armband
was dropped here for exactly as long as nothing could reach this code but the app itself.

## What building it found

⚠️⚠️ **My first reproduction included the fix and passed, proving nothing.** The test helper standing in for
`_planSwap` carried the armbands over, because that is what the code obviously *ought* to do — so the
"failing" test was green on the first run. ⭐ **A reproduction that quietly includes the fix reproduces the
fix, not the bug.** It only became a real reproduction once the helper was made to match the shipping code
line for line — and that duplication is itself what §3 removes.

⚠️ **Two mutations in the first sweep reported SURVIVED and had never applied** — `dart format` had
reflowed the lines the patches matched on. The third time this session. The guard is now an `if python3 …;
then run …; else discard`, rather than a bare command whose failure the shell ignores.

⭐ **One mutation found a real gap**: removing the line that swaps the outgoing player off the bench left
every test green. A plan could hold a man you no longer own *and* omit the one you bought. There is a test
for it now.

## Consequences

* Armbands survive transfers, and only while their wearer does.
* ⚠️ **Setting an armband still stores `analysis.bench` — the engine's recommended bench, not yours.** So
  tapping "make captain" can still submit a lineup you did not choose. Tested and *asserted as current
  behaviour* rather than fixed, because changing it is a decision about what a draft means, not a bug fix.
  📌 Open.

## Verification

* **8 Dart tests** walking the real sequence: save, reload, staleness, overlay, a second armband change,
  promotion of the vice, a transfer, and a transfer *of* the captain.
* **5/5 mutations killed** after the gap above was closed: the swap dropping both armbands; a C surviving
  its player being sold; `clearViceCaptain` no longer clearing; the transfer not happening at all; and the
  bench not being updated.
