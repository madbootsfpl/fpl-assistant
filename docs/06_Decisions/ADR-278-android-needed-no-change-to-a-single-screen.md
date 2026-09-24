# ADR-278 — Android needed no change to a single screen

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner — *"next up is Android support setup. Reason: 90% of active testers are android, I am
the only iPhone at the moment"*

---

## The shared-code answer, checked rather than assumed

**Zero** `Platform.is` branches. **Zero** `defaultTargetPlatform` checks. **No** Cupertino widgets. All
36 files and ~26,700 lines of `mobile/lib/` are platform-neutral, and Android required **no change to a
single screen, model or test**.

⭐ So a feature asked for by an Android tester **is iOS code the moment it is written** — and anything
server-side reaches both with no rebuild at all. ⚠️ *The code is shared instantly; the build on a
handset is not.* Fix once, ship twice.

## ⚠️⚠️ Two defects Flutter's own template ships with

### The release APK could not reach the network

`INTERNET` is declared in `src/debug` and `src/profile` — the builds that need it for hot reload — and
**not** in `src/main`. A release APK from the template therefore declares **no permissions at all**: it
installs, it opens, and every request fails.

⭐ **A permission present in every build you test and absent from the one you ship is the hardest kind of
missing thing to notice.** Found by reading the manifest rather than trusting the build, and confirmed by
dumping the **built APK** — ⚠️ *the manifest is what you wrote; the APK is what you ship.*

### The release build was signed with the debug key

The template does this so `flutter run --release` works out of the box, and says so in a comment.

🔴 **An APK signed with one key can never be updated by a build signed with another.** A tester who
installs a debug-signed build can only move to a properly signed one by uninstalling — which wipes
`shared_preferences`, **where their saved drafts live** (ADR-225/272).

⭐ So the release build now **throws** when `key.properties` is absent: *a fallback that silently
produces an installable artefact is how a debug-signed APK reaches a tester.* A build that stops is a
build you fix; one that quietly signs with the wrong key is discovered months later, by the one person
who cannot update.

📌 And the **package-id trap from ADR-221, hit again**: `--org com.madboots` plus project name `madboots`
gives `com.madboots.madboots`. Corrected to `com.madboots.fpl` across `namespace`, `applicationId` and
the `MainActivity` package directory.

## 🔴 The private signing key was one `git add -A` from being published

A keystore backed up to `backup/` in the **repository root** sat outside Flutter's
`mobile/android/.gitignore`, which only covers its own subtree.

⭐⭐ **An ignore rule is only as wide as the directory it lives in** — the same shape as ADR-261's
hand-maintained `_CORE` list, and ADR-269's near-white chip: *a guard that is correct and does not reach.*

⚠️ **And a backup inside the repository is not a backup** — it is the same disk, plus a way to publish it.

Never committed. The root `.gitignore` now covers `*.jks`, `*.keystore` and `key.properties` **anywhere**
in the tree, and a test fails if any is ever staged — ⭐ matching by **extension, not by name**, because
*nobody will remember to add the second keystore's filename to a list.*

## Decisions

**JDK 17 via Homebrew, alongside the existing Java 11.** ⚠️ The Oracle 11 already installed was both too
old for the Android Gradle Plugin **and an Intel build** — ⭐ *a toolchain that works is not the same as
the right one*, and the failure would have surfaced from Gradle rather than from Java.

**Command-line tools, not Android Studio** — 8.7 GB including an emulator image, against ~10 GB for the
IDE alone on a machine with 16 GB free.

**API 36 and NDK 28.2 read from `gradle_utils.dart`**, not chosen. ⭐ *Installing what the tool asks for
beats installing what a tutorial suggested.*

**`--split-per-abi` always**: 51 MB universal versus **18 MB** for arm64.

**Cleartext HTTP is debug-only**, mirroring ADR-239's refusal of `NSAllowsArbitraryLoads` — a release
build has no network-security config at all and is HTTPS-only.

## Verification

* **A release APK built, installed on an emulator and verified running against the hosted API** — the
  owner's real squad, kits, xP and bench, from an unmodified `lib/`.
* **The artefact was inspected, not the source**: `aapt2 dump badging` confirms `com.madboots.fpl`, the
  `INTERNET` permission and the `Madboots` label.
* **3 Python tests** on signing material, one **proved** to fail by staging a decoy keystore.
* ⚠️ `flutter create` also deleted iOS, macOS and web from `.metadata` and added a template counter test
  referencing a `MyApp` this app does not have. Both reverted — ⭐ *a scaffolding tool assumes it is
  scaffolding.*
* 2,578 Python · 254 Dart.
