# ADR-339 — The web app could not tell you it was stale

*A bank that went negative and did not go red. Both halves were working.*

**Date:** 2026-10-01
**Status:** Accepted
**Extends:** ADR-282 (the self-hosted update check) · ADR-304 (the retired service worker)
**From:** the owner, on build 39 — *"worked except that the bank did not go red when negative"*

---

## What actually happened

Nothing was broken. Checked, in this order:

| | |
|---|---|
| Deployed `index.html` | references `?v=39`, `cf-cache-status: DYNAMIC` |
| Deployed `main.dart.js` | **contains** `Over budget` and `bank_is_estimated` |
| The live API, for an over-budget draft | `bank: -5.9`, `bank_is_estimated: true` |
| The native app, 22 minutes earlier | showed it red, labelled *Over budget (est.)* |

🔴 **The screenshot was the web app, running an older bundle.** The server half of ADR-337 deploys on
push, so the bank went negative; the client half ships in a build, so it did not go red. ⭐ *A
half-updated app produces symptoms that look exactly like a half-built feature.*

## The real gap

`selfHostedUpdates` is `!kIsWeb && Platform.isAndroid`, and ADR-282's reasoning for excluding iOS is
right: *"a notice is a promise that tapping it will help"*, and the manifest describes an **APK**, which
an iPhone cannot use.

⚠️⚠️ **Web was silenced by the same line, and the reasoning does not fit it.** A browser *can* update
itself — it reloads. So the web is the one platform where the promise is trivially keepable, and it was
the only one with no way to say *"you are eleven builds behind"*.

⭐⭐ *An app that cannot tell you it is stale makes every stale symptom look like a defect* — and costs
its owner an afternoon reporting one.

## Decision

`webUpdates` is its own gate. The banner is **platform-honest**: on the web it says *"Refresh the page
to get it"*, carries no chevron, and is not tappable — because there is nothing to tap through to.

## 🔴 And the branch could not be tested, which is how ADR-282's bug shipped

`kIsWeb` is a compile-time constant, so a Mac test run can never enter the web path. My first test
asserted `checksForUpdates == selfHostedUpdates || webUpdates` — **true by construction**, and it passed
cheerfully when I mutated `webUpdates` to `false`.

⭐⭐⭐ *A guard no test can reach is a guard that is not there.* That sentence is already in
`update_check.dart`, written after the iOS banner shipped offering an iPhone an APK — **for exactly this
reason**, and `published()` already took a `selfHosted` override to answer it. I had read the file and
still repeated the mistake one function along.

So `published()` takes `onWeb` as well, and `_UpdateBanner` became **public** `UpdateBanner` with an
`onWeb` override. Both branches now have tests that fail when the branch is removed.

## Verified

537 Dart tests. Two mutations caught: silencing the web again, and offering a browser the download.

## Consequences

**Good:** a web reader is told when their tab is behind, in the one place a reader looks, with an action
they can actually take.

**Costs:** ⚠️ `UpdateBanner` is public purely so a test can reach it. That is a real widening of the API
surface for testability, taken deliberately — the alternative is the untestable branch this ADR exists
to stop repeating.

⚠️ **Open, and the owner has already raised it:** none of this would have mattered with a way to try a
build before the nine testers get it. ⭐ `release_android.sh` builds the APK **and** publishes the
`version.json` that prompts them, in one command — so the smallest possible gate is splitting those two
steps. That discussion is his to have; this ADR only removes the trap that made a working release look
broken.
