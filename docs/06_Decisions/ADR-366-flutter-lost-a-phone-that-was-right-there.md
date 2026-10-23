# ADR-366 — Flutter lost a phone that was right there

**Date:** 2026-10-23
**Status:** Accepted
**Found:** reinstalling build 50 on the owner's iPhone

---

## Context

`scripts/release_ios.sh` failed twice:

```
To use 'iPhone 17 (wireless)' for development, enable Developer Mode in
Settings → Privacy & Security on the device.
No target device found
```

Both times the build succeeded and only the copy-to-device failed. ⚠️ And the phone was fine:

* `flutter devices` **listed it**, wirelessly, in the same run;
* `xcrun devicectl list devices` reported `available (paired)`;
* Developer Mode was **already on** — and had been the first time too.

⭐⭐ *That message is flutter's guess when its own device lookup fails, not something the phone said.* I
read it as a diagnosis and sent the owner to check a setting that was not the problem — twice, before
asking the device layer what it thought.

## Decision

**Fall back to Apple's own installer.** `xcrun devicectl device install app` put the build on the same
UDID without complaint, and ⭐ *this script already trusts `devicectl`*: step 4 has always asked it
whether the app is really on the phone. Now it does the installing too, when flutter cannot.

⚠️ **Announced, never silent** — the script says it fell back. *A fallback nobody is told about turns a
broken tool into a mystery that gets rediscovered.*

## 🔴 It is intermittent, which is worse than broken

Run again immediately afterwards, **`flutter install` worked** and the fallback never fired. So this is
not a tool that has stopped working; it is one that loses the device sometimes. ⚠️⚠️ *A failure that
clears up on its own is the kind that gets blamed on the phone every time*, which is exactly what
happened here.

📌 Verified by forcing the branch rather than waiting for it: with `flutter install` replaced by `false`,
the script printed *"using Apple's installer instead"* and the phone reported `MADBOOTS 1.0.0 (50)`.
⭐ *A fallback that has never run is a fallback nobody can say works.*

## Consequences

✅ A wireless install no longer depends on flutter's device matching. The staging path (ADR-340) inherits
this, since `release_stage.sh` calls this script.

📌 Unchanged: the **build** still goes through flutter, and `--dart-define=MADBOOTS_API` with it. Only the
final copy is replaced, so nothing about what is installed changes.
