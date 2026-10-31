# ADR-379 — Seventeen minutes

**Decision ID:** ADR-379
**Date:** 2026-10-30
**Status:** ✅ **Accepted and built.** `release_ios.sh` now sets aside a stale provisioning profile **before**
building, and reports the installed build's **actual** expiry instead of quoting the policy.
**Superseded By / Replaces:** Makes [ADR-316](./ADR-316-a-release-that-reached-two-platforms.md)'s script
keep the promise its own docstring made. Second failure of the same install path after
[ADR-366](./ADR-366-flutter-lost-a-phone-that-was-right-there.md), and the same shape: *a tool reported
success for something it had not done.*
**Deciders / Participants:** Tony Sheridan (Owner, reported it), Claude Code (Implementation)

---

### 📌 What happened, from the owner's side

> *"why is madboots no longer available on my iphone?"*

Asked at **19:46**. I had reinstalled the app at **14:35** the same afternoon and told him: *"Fresh
certificate, so you're good until ~2026-11-06."*

The profile embedded in that build:

| | |
|---|---|
| created | 2026-10-23 **14:52** |
| expires | 2026-10-30 **14:52** |
| installed | 2026-10-30 **14:35** |

⭐⭐ **THE APP HAD SEVENTEEN MINUTES.** `flutter build ios` re-signed with a **cached profile created seven
days earlier**, so re-running the installer renewed nothing. The signing *certificate* was valid the whole
time — `security find-identity` showed it — which is why nothing looked wrong.

---

### 🔴 The real defect: an instruction that had quietly stopped being true

`release_ios.sh` has said, since ADR-239:

> *"The seven days is the trade. A free-provisioned certificate expires and the app stops launching.
> **Re-running this fixes it in about a minute**, and you will do that weekly for as long as you stay free."*

⭐⭐ **THAT IS ONLY TRUE IF THE BUILD MINTS A NEW PROFILE, AND IT DOES NOT.** Xcode reuses whatever is
cached in `~/Library/Developer/Xcode/UserData/Provisioning Profiles/` until the file is gone. So re-running
on day 6 re-signs with a profile that dies on day 7 — and the script prints its cheerful weekly reminder
either way.

⚠️ **It is worse than a no-op: it is a no-op that reports success.** Step 4 asks the device whether the app
is installed (ADR-316's hard-won check) and it truthfully answers yes. ⭐ *A verification that is narrower
than the claim it is read as supporting will certify the broken case.* We verified the **install** and
assumed the **signing**.

---

### 🩺 What I did wrong, separately from the script

I asserted the renewal from having run the installer. The refutation was **inside the artefact I had just
built** — one `security cms -D -i Runner.app/embedded.mobileprovision` away, which is the command that
diagnosed it five hours later. ⭐ *I had the evidence, generated it myself, and did not look at it.*

---

### ✅ The fix, in two halves

**1 — Make the seven days real.** Before building, any cached profile for `com.madboots.fpl` with less than
`IOS_PROFILE_MIN_HOURS` (**48**) left is **moved aside**, so Xcode reissues:

```
⟳ cached profile has only 167h left — set aside so Xcode issues a fresh seven days
```

⚠️ **48 hours, and the direction of the risk decides it — not "always reissue".** Purging only helps if
Apple then issues a replacement, so discarding a profile that is still *useful* trades a working build for
a network round trip that can fail. Under two days there is nothing left to lose. ⭐ *Always reissuing would
turn an offline laptop from an inconvenience into a failed release.*

⭐ **Moved, never deleted.** If Apple cannot be reached, the owner still has the file that was working this
morning.

**2 — State the measurement, not the policy.** The closing warning now reads the installed artefact:

```
⚠️  This build stops launching on Fri 06 Nov, 19:59 UTC (167h from now).
```

…and shouts when the bug recurs:

```
🔴 THIS BUILD EXPIRES IN 0h — Fri 30 Oct, 20:00 UTC
   That is not a fresh seven days: the build re-used a cached profile. Re-run this script.
```

⭐⭐ **THE OLD LINE WAS A TRUE FACT ABOUT FREE PROVISIONING AND A FALSE ONE ABOUT THE BUILD IT HAD JUST
INSTALLED.** *A warning that states the policy instead of the measurement cannot tell you the policy was
not applied* — which is exactly the failure it sat next to for seven months.

---

### 🧪 Definition of Done

**1 — Automated tests.** 11 new in `tests/test_ios_release.py`. ⭐ The arithmetic moved to
`scripts/lib/ios_profile.sh` **so that it could be tested**: the release script needs a phone, the decision
needs two timestamps. ⚠️ *A rule tested by grepping for its own source text is not tested* — which is what
the old file could only do.

### 🔴 And then CI went red, which is the third mistake in this ADR

The first version parsed dates with **BSD `date -j -u -f`**. It passed the pre-push net and **failed CI** —
the net runs on this **Mac**, CI runs on **Linux**, and `-j` does not exist there. Every date test returned
`''`. ⭐⭐ *A NET THAT RUNS ON ONE PLATFORM CANNOT CATCH A DIFFERENCE BETWEEN TWO*, and
[ADR-359](./ADR-359-a-net-not-a-gate.md) carefully lists what it cannot catch **without listing this** —
its blind spots were enumerated from the categories that had bitten us, not from first principles.

⚠️ The obvious patch was *"try BSD, fall back to GNU"*. **I could not verify the GNU branch on this
machine:** there is no `gdate`, and a stub that merely hides `-j` still falls through to BSD, so the
fallback **tested as broken** and would have shipped on faith. ⭐⭐ *A fallback you cannot exercise is a
second guess, not a safety net* — and guessing at a platform is what broke it the first time.

**So the dates are parsed in `python3` instead**, which this project already requires everywhere. One
implementation, no dialects, **no untested branch**, and verifiable here. ⭐ *The fix for "it behaves
differently on two platforms" is not a second path; it is one path that does not depend on the platform.*

**9 deliberate defects, 8 caught** (re-run after the Python rewrite): purge decision inverted · default
threshold set to 0 · alarm never fires on a dying build · `hours_left` sign flipped · epoch parser format
wrong · stale profile deleted instead of set aside · closing line stops reading the artefact · purge moved
after the build.

⭐ The ninth — deleting `hours_left`'s `[ -n "$exp" ]` guard — **survives, and is an equivalent mutant
rather than a hole**: `iso_epoch` already exits non-zero on an unparseable date, so the preceding
`|| return 1` catches it first. The line is redundant insurance and is kept as such. ⚠️ *Counting an
equivalent mutant as an uncaught one inflates the hole; counting it as caught inflates the coverage.*

⚠️ **Two of my own tests were wrong first and both are worth recording:**
- The threshold mutant **survived**, because my tests passed `should_purge` a literal `48` and never
  exercised the default. ⭐⭐ *A constant exercised only through a value the test supplies is a constant the
  test does not cover.*
- My new **comment broke two tests**, including a pre-existing one, by containing the words
  `flutter build ios` — `test_the_api_address_is_baked_in_at_build_time` took the first line matching that
  string and got my explanation. Fixed by stripping comments in a `_code()` helper rather than rewording:
  ⭐ *a test that greps a script cannot tell code from the paragraph describing it, and the paragraph is the
  part that keeps getting written.*

**2 — Manual smoke test.** Run end to end against the phone with `IOS_PROFILE_MIN_HOURS=200` to force the
purge path: profile set aside, Xcode reissued, app installed, and the report read **Fri 06 Nov, 19:59 UTC
(167h)** from the new artefact. Re-run after the Python rewrite and it reads **154h** — the countdown is
live, which is the point. The app is on the device with a genuine week.

**3 — Docs.** This ADR, index, PROJECT_STATUS, README counts.

---

### 📊 Consequences

**Good:** the weekly ritual now does what it has always claimed. The failure mode is self-announcing: if a
future toolchain reuses a profile anyway, the closing line says `THIS BUILD EXPIRES IN 0h` instead of
congratulating itself.

**Costs / limits:**
- ⚠️ **Reissuing needs Apple reachable.** A purge immediately before an offline build fails the build. The
  48-hour threshold keeps that to the case where the cached profile was nearly worthless anyway, and the
  file is recoverable from `$TMPDIR/madboots-stale-profiles`.
- ⚠️ **The 7-day clock itself is untouched.** This makes the renewal real; it does not make it less
  frequent. ⭐ *That weekly minute is still what the £79/yr buys away* — and this ADR slightly strengthens
  the case for paying, because the manual path has now failed twice in eight days (ADR-366, this).
- ⚠️ Only `com.madboots.fpl` profiles are swept, matched on the profile `Name`. A future bundle id rename
  would silently stop the purge — and the closing line is what would catch it.
- ⚠️ **The pre-push net's blind spot is now known and still unfixed:** it cannot see a macOS/Linux
  difference, because it runs on one of them. Shell helpers are the exposed surface; Python is not, since
  CI runs the same interpreter. ⭐ *Worth adding to ADR-359's list of what it cannot catch rather than
  rediscovering.*

---

### 🔗 Links

- [ADR-316](./ADR-316-a-release-that-reached-two-platforms.md) — the script, and the promise it now keeps
- [ADR-366](./ADR-366-flutter-lost-a-phone-that-was-right-there.md) — the previous failure of this same path
- [ADR-239](./ADR-239-a-phones-localhost-is-the-phone.md) — free provisioning, and the £79/yr it defers
- `scripts/lib/ios_profile.sh` — the arithmetic, extracted so it could be tested
