# Building and shipping the Android app

**Status:** ✅ running — a release APK built, installed and verified against the hosted API on 2026-09-24.

⭐ **The Flutter code is untouched.** All 36 files in `mobile/lib/` are platform-neutral — no
`Platform.is` branches, no `defaultTargetPlatform`, no Cupertino widgets — so Android needed **no change
to a single screen, model or test.** Everything below is toolchain and distribution.

---

## 1. The toolchain (one-off)

```bash
brew install openjdk@17                      # ⚠️ NOT the Oracle 11 already on the machine — see below
brew install --cask android-commandlinetools

export ANDROID_HOME=/opt/homebrew/share/android-commandlinetools
export JAVA_HOME=/opt/homebrew/opt/openjdk@17
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

yes | sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-36" "build-tools;36.0.0"

flutter config --android-sdk "$ANDROID_HOME"
flutter config --jdk-dir "$JAVA_HOME"
flutter doctor                                # expect: Android toolchain ✓
```

⚠️ **JDK 17, and it matters twice.** The Mac already had Oracle **11** — too old for the Android Gradle
Plugin — **and an Intel build**, so it would have run under Rosetta. ⭐ *A toolchain that works is not the
same as a toolchain that is the right one*, and the failure would have come from Gradle, not from Java.

📌 **API 36 / NDK 28.2 are not chosen, they are read.** `flutter_tools/lib/src/android/gradle_utils.dart`
declares `compileSdkVersion = 36` and `ndkVersion = '28.2.13676358'`. ⭐ *Installing what the tool asks
for beats installing what a tutorial suggested*, and Gradle fetches the NDK itself on first build.

⚠️ There may be a second, older `adb` (a `/usr/local` Intel cask). `flutter doctor` warns about it; it has
not caused trouble, but a device-detection oddity would start there.

---

## 2. ⚠️⚠️ Two defects Flutter's template ships with

**`INTERNET` is missing from the release manifest.** The template puts it in `src/debug` and
`src/profile` only — the builds that need it for hot reload. ⭐ **A release APK generated from the
template declares no permissions at all**: it installs, opens, and every API call fails. It is now in
`src/main/AndroidManifest.xml`.

⚠️ *A permission present in every build you test and absent from the one you ship is the hardest kind of
missing thing to notice.*

**The release build is signed with the debug key.** The template says so in a comment, so that
`flutter run --release` works out of the box. See §3 — this repo now **fails the build** instead.

📌 **And the package id trap** (ADR-221, hit again): `--org com.madboots` + project name `madboots` gives
`com.madboots.madboots`. It is `com.madboots.fpl`, matching iOS, and `namespace`, `applicationId` and the
`MainActivity` package directory all had to move together.

---

## 3. Signing

🔴 **The keystore is the app's identity.** An APK signed with one key can **never** be updated by a build
signed with another — Android refuses. ⚠️ *And uninstall-to-fix wipes `shared_preferences`, which is where
a tester's saved drafts live (ADR-225/272).* So this is settled **before** anyone installs, not after.

```bash
# In a real terminal — not through an agent session, where keytool cannot hide the password.
/opt/homebrew/opt/openjdk@17/bin/keytool -genkey -v \
  -keystore ~/madboots-release.jks -keyalg RSA -keysize 2048 -validity 10000 \
  -alias madboots -dname "CN=MADBOOTS, O=MADBOOTS, L=Dublin, C=IE"
```

Then `cp android/key.properties.example android/key.properties` and fill in the password.

⭐ **The release build fails loudly without it** rather than falling back to the debug key: *a fallback
that silently produces an installable artefact is how a debug-signed APK reaches a tester.*

**v2 and v3 signing are both on.** ⭐ v3 is the scheme that supports **key rotation**, the only hedge
against the one unrecoverable mistake here — ⚠️ *and it has to be in the APKs people already installed*,
because rotation proves a chain from the key they already trust. A build signed v2-only can never start
that chain.

### ⚠️ What "the signature must match" looks like

Installing a properly-signed build over the earlier debug-signed one is **refused**:

```
INSTALL_FAILED_UPDATE_INCOMPATIBLE: Existing package com.madboots.fpl
signatures do not match newer version; ignoring!
```

⭐ *That refusal is the guarantee, not a bug* — it is what stops anyone else publishing an update to your
users. The only way past it is uninstall, which is why signing is settled **before** distribution.

### 🔴 What is private, and what ships

| | Where it lives | Who sees it |
|---|---|---|
| **Private key** (`~/madboots-release.jks`) | your machine + an **off-machine** backup | only you |
| **Password** (`android/key.properties`) | gitignored, never committed | only you |
| **Public certificate + signature** | inside every APK | everyone |

⚠️⚠️ **A backup inside the repository is not a backup** — it is the same disk, plus a way to publish it.
A keystore copied to `backup/` in the repo root on day one sat outside Flutter's
`mobile/android/.gitignore` and would have been committed: *an ignore rule is only as wide as the
directory it lives in.* The root `.gitignore` now covers `*.jks`, `*.keystore` and `key.properties`
anywhere in the tree, and `tests/test_no_signing_material_tracked.py` fails if any is ever staged.

---

## 4. Building

```bash
(cd mobile && flutter build apk --release --split-per-abi \
   --dart-define=MADBOOTS_API=https://madboots-api.onrender.com)
```

⭐ **`--split-per-abi`, always.** One universal APK is **51 MB** because it carries three ABIs; split, the
one that matters is **18 MB**. ⚠️ Send `app-arm64-v8a-release.apk` — every phone made in the last decade —
and keep `armeabi-v7a` for anything genuinely old.

**Verify the artefact, not the source:**

```bash
$ANDROID_HOME/build-tools/36.0.0/aapt2 dump badging <apk> | grep -E "^package|uses-permission|label"
$ANDROID_HOME/build-tools/36.0.0/apksigner verify --print-certs <apk>
```

⭐ *The manifest is what you wrote; the APK is what you ship*, and the missing-INTERNET defect above was
found by reading one and confirmed by dumping the other.

---

## 5. The emulator (no Android device needed)

```bash
sdkmanager "emulator" "system-images;android-36;google_apis;arm64-v8a"
echo no | avdmanager create avd -n madboots -k "system-images;android-36;google_apis;arm64-v8a" -d pixel_7
emulator -avd madboots &
adb install -r build/app/outputs/flutter-apk/app-arm64-v8a-release.apk
adb shell am start -n com.madboots.fpl/.MainActivity
```

⚠️ **Install the `arm64-v8a` APK, not `x86_64`.** On Apple Silicon the emulator is arm64, and the x86_64
split fails with `INSTALL_FAILED_NO_MATCHING_ABIS` — ⭐ *which is the split working, not breaking.*

Screenshot: `adb exec-out screencap -p > shot.png`.

---

## 6. What this buys over iOS

| | iOS | Android |
|---|---|---|
| Developer fee | £79/yr for TestFlight | **none** |
| Certificate expiry | **7 days** on free provisioning | **none** |
| Getting a build to a tester | re-sign weekly, or pay | **send the APK** |

⭐ This is why Android went first once the testers were counted: **9 of 10 are on it**, and it is also the
platform where a build reaching them costs nothing and does not expire.
