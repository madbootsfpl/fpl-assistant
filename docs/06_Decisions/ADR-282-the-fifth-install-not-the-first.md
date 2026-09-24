# ADR-282 — The fifth install, not the first

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner — *"lets sort the distribution next"*
**Builds on:** ADR-278 (the Android build), ADR-280/281 (usage by platform)

---

## The problem is not getting the app onto a phone

That part is already solved: an APK exists, it is signed, and it installs. Nine testers can each be sent
a file once.

⭐⭐ **The problem is the fifth install.** Every fix after today has to reach nine devices that have no
idea a fix exists. Asking people to go and re-download an APK after every change is a request that is
honoured twice and then quietly stops being honoured — and the way you find out is a bug report about
something fixed last week, from someone whose phone never said anything was wrong.

⚠️ **A stale install does not look like a stale install. It looks like a bug that will not die.**

## The decision

**Self-host the APK on `madboots.com/app/`, and let the app check for itself.**

Three pieces:

1. **`scripts/release_android.sh`** — bumps the build number, builds the split APKs, and stages the
   arm64 APK, a `version.json` manifest and an install page into the website folder.
2. **`mobile/lib/update_check.dart`** — reads that manifest on start-up and answers one question:
   *is the published build newer than this one?*
3. **A slim banner** at the top of the team screen when the answer is yes.

### Why not Firebase App Distribution

It is the obvious answer and it was the wrong one here. It wants a Google account per tester, a service
account secret in the build, and a console to administer — ⭐ *three new things to maintain, to solve a
problem that a JSON file next to the APK solves.* The website already exists and already deploys.

⚠️ It also composes with what ADR-280 just built: the usage panel already records `version`, so **a
tester stuck on an old build is now visible in data** rather than being something you find out from a
confusing bug report.

## Three things this got right by being careful

### The comparison is on the build number, never the version name

`1.0.0` will ship twenty times during a beta. ⭐ *A comparison on a label that does not change cannot
tell two builds apart* — which is exactly why Android itself ignores `versionName` and decides on
`versionCode`. The name is for humans; the number is the fact.

So **three numbers must move together** — `pubspec.yaml`, `kAppVersion`, `kAppBuild` — and a release that
moves two of them ships an app that cannot tell it is newer than itself. The script moves all three, and
`mobile/test/telemetry_test.dart` fails if they ever drift apart.

### The check cannot block, cannot throw, and cannot nag

No `await` before the first frame, no modal, no forced update. Every failure — offline, a typo'd URL, a
half-deployed site serving its own index page — returns `null` and the app behaves exactly as it did
before the check existed. ⚠️⚠️ *An update prompt that can stop you using the app is worse than the stale
build it is warning about.*

The banner has no ✕. It disappears when the new build is installed, and ⭐ *a warning you can silence
without fixing anything is a warning that gets silenced.*

### The install page, because the first-run experience is three scary warnings

Chrome says the file may harm your device. Android says this source is not allowed to install apps. Both
are routine for any sideloaded APK and both read like a virus alert. ⭐ *Testers who hit that with no
warning do not ask what it means — they stop.* The page says what each prompt will say before it says it.

## ⚠️ What the tests caught that review did not

**Two mutations survived the first pass**, and both for the same reason: the test body failed a *later*
guard too, so the test passed whether or not the guard it was written for still existed. A 404 test whose
body was also unparseable proved nothing about the status check. Fixed by giving the 404 a **valid**
manifest body.

**One guard turned out to be unobservable.** A shape check rejecting non-object JSON changed *which line*
produced `null`, not whether `null` was produced — the surrounding `catch` already did it. No test could
tell it was there, so it was deleted. ⭐ *A guard no test can tell is missing is a guard that will one day
be deleted by someone who cannot tell either* — better to remove it deliberately and say why.

**And the release script failed twice in ways only running it could find:** an assert that checked
*changed* rather than *found* (a rebuild under the same version name rewrites the constant to identical
text), and a `set -e` death on an `ls` glob that does not exist on every machine — ⚠️ *after the build,
which is the most expensive possible place to fall over.*

`tests/test_update_manifest.py` now holds the shell script and the Dart file to the same manifest shape.
They share no code, no types and no language; ⭐ *the only thing holding them together was that someone
remembered.*

## ⭐ The smoke test found the one thing review could not

`https://madboots.com/app/version.json` **does not 404 today.** Cloudflare Pages answers `200` with the
site's own homepage for any unknown path:

```
content-type: text/html; charset=utf-8
<!DOCTYPE html><html lang="en">…
```

⚠️⚠️ **That is the exact case the HTML guard was written for, and it turned out not to be hypothetical —
it is the default behaviour of the host this depends on.** A check that parsed optimistically would have
thrown on every launch, in every tester's app, before the feature was ever switched on.

To see the banner actually fire before a real second build exists, `kManifestUrl` became a
`String.fromEnvironment('MADBOOTS_MANIFEST')` with the live URL as its default — the same
`--dart-define` pattern the API URL already uses. ⭐ *A notice that only appears when a real release
exists is a notice first tested in front of testers.* Built against a local manifest claiming build 99,
the emulator showed:

> **Build 99 is out — yours is 2. Tap to update; what you are about to report may already be fixed.**

⚠️ The release build is **HTTPS-only** — cleartext is enabled in the debug manifest alone — so this could
only be proven on a debug build, which is the correct trade and worth writing down rather than
rediscovering.

## ⚠️ And then the first real download rendered as text

The site went live and the first tester tap produced **18MB of zip printed into the browser**.

`curl -sI` on the APK:

```
HTTP/2 200
content-length: 18707560
x-content-type-options: nosniff
```

⭐⭐ **No `Content-Type` line at all.** Cloudflare Pages does not recognise `.apk`, so it declares
nothing, and Chrome falls back to rendering the bytes. ⚠️ *The download did not fail — it succeeded, into
a wall of mojibake*, which reads as a broken site rather than a missing header.

Fixed with a `_headers` rule at the **site root**, written by the release script and merged rather than
overwritten, because ⭐ *a one-line fix on a path nobody revisits is exactly the kind that vanishes in the
next site rebuild.*

### ⚠️⚠️ The redeploy changed nothing

The rule was correct and the site was redeployed, and the tester saw **exactly the same wall of text.**

```
cf-cache-status: REVALIDATED     ← the plain url: still no content-type
cf-cache-status: MISS            ← the same url with ?x=…: correct, both headers
```

Cloudflare had cached `madboots.apk` for four hours *before* the rule existed and kept serving that copy.
⭐⭐ **A fix that is live but invisible is indistinguishable from a fix that did not work** — and the
person looking at it is a tester, not the person who can read the cache status.

The answer was not "purge the cache". Each release now publishes **`madboots-<build>.apk`**, and ⭐ *a URL
that has never been requested cannot be stale.* No purge step, no waiting: cache invalidation **avoided**
rather than managed, because *the release that needs a manual cache purge is the release someone ships
without one.*

⚠️ **And the `_headers` merge had the same bug in miniature.** It skipped when `/app/*.apk` was already
present — protecting other people's rules, and in doing so preserving its own outdated one. ⭐ *"Leave
other people's config alone" had quietly become "never fix my own."* It now replaces the block it owns and
keeps the rest, with four tests covering from-nothing, own-stale-rule, foreign-rule-alongside, and
run-twice.

**What the smoke test could not have caught.** Every check to this point ran against the manifest, the
signature and the app — all of which were right. ⚠️⚠️ *The APK was the one artefact nothing verified by
asking for it the way a tester would*, and `curl -sI` on the published file is now part of the runbook.

## What this does not do

- **iOS.** TestFlight is the answer there and it needs the paid developer account. The owner is the only
  iPhone tester, so this is not yet costing anything.
- **Automatic install.** The banner opens the download page; Android does the rest.
- **Release notes.** `version.json` has a `notes` field and it is empty. When there is something worth
  saying, there is somewhere to say it.

## Status

Build `1.0.0+2` (`versionCode` 2002) is staged and signed with the release key — v2 and v3 schemes, the
same key as the build already on the tablet, so it installs over the top and keeps squad, plan and
settings.

**It goes live when the site folder is deployed to Cloudflare Pages.** Until then the app asks for a
manifest that 404s, gets `null`, and says nothing — which is the designed behaviour, and the reason this
could be shipped before the site was.
