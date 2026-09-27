# ADR-316 — A release that reached two platforms

**Date:** 2026-09-27
**Status:** ✅ **Built.** `scripts/release_ios.sh`.
**From:** the owner, after being told build 26 could not reach his phone — *"you have been pushing to my
iPhone, that does not need testflight."*

---

## What happened

Build 26 went out to **Android and web**. I reported it as shipped, and when asked directly about the
iPhone I said *"no iOS pipeline exists"* — having grepped `scripts/` and CI, found nothing, and stopped.

⚠️⚠️⚠️ **The procedure existed.** `docs/03_Architecture/iPhone_Free_Provisioning.md` (ADR-239) documents
it in seven steps, and I had used it earlier the same week. ⭐ *It is a document, not a script, and I looked
for it in the shape I expected it to have.*

⚠️⚠️ **And I collapsed two different questions.** *"Can this go on your phone?"* — yes, free provisioning,
a personal Apple ID, £0. *"Can testers get it?"* — no, that needs the £79/yr programme. The provisioning
doc's **opening line** draws exactly that line, and answering the second question when asked the first made
a solved problem sound blocked.

🔴 **It was the second time.** The same thing happened at build 14, for the same reason.

## The decision

**The iPhone gets a script, because the other two have one.** Android and web are one command each; the
phone in the owner's pocket was prose. ⭐⭐⭐ *A step that must happen every release and lives only in a
document is a step that gets skipped — and it will be skipped by whoever is in a hurry, which is everyone
cutting a release.*

## What the script does, and the four things it gets right

| | |
|---|---|
| **Discovers the phone** | ⚠️ The doc names a device id in prose — ⭐ *and a device id in prose goes stale the day the phone is replaced.* |
| **Bakes the API in at build time** | ⚠️⚠️ `flutter install` has no `--dart-define`, so a build without it points at `localhost` — **which on a phone is the phone** — and every screen fails with nothing to say why. |
| **Installs rather than runs** | ⭐ `flutter run` stays attached, and quitting it **terminates the app on the device**. ⚠️ *A release script whose last act can uninstall its own release is not a release script.* |
| **Asks the phone** | ⭐⭐ A build that succeeded and an app that is on the device are **different claims**, and this script exists because the second was assumed twice. It prints what `devicectl` reports: `MADBOOTS 1.0.0 (26)`. |

⭐ It deliberately does **not** pass `MADBOOTS_DEV`: that flag adds the Settings ▸ Server field for aiming
at a laptop (ADR-270), and this is the real build.

⭐ It also does **not bump the version**. `release_android.sh` owns that, because `versionCode` is the
release's identity; this installs whatever the current build is.

## Where the omission actually happened

⭐ **The fix is not only the new script — it is the last line of the old one.** Whoever cuts a build reads
`release_android.sh`'s closing hint, so that hint now names the other two:

```
NEXT: commit the version bump. Testers already have it: https://madboots.com/app/
      …and the other two:  scripts/release_web.sh  ·  scripts/release_ios.sh
```

## 🔴 The seven days, stated where it will be read

Free provisioning expires after a week and the app **stops launching** — so the script prints that every
time it runs. ⭐ *The cost people forget is the one nobody prints*, and this is the real argument for the
£79/yr: not distribution to testers, but a weekly minute that never ends.

## Consequences

- ⭐ **"Cut a build" now means three platforms**, and a test asserts the Android script says so.
- 📌 The script cannot be run in CI — it needs a physical phone — so its guards read it rather than run it.
  ⚠️ *Reading a script is a weak test and a real one:* it catches the `--release` flag going missing, the
  API define being dropped, `run` creeping back in place of `install`, and a hard-coded device id
  returning.
- 📌 **TestFlight is still open and still £79/yr** — genuinely, for *other people's* phones. This ADR
  narrows what that decision is about; it does not make it.
