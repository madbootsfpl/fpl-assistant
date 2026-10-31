#!/usr/bin/env bash
# Put the current build on a connected iPhone (ADR-239's procedure, ADR-316).
#
# ⚠️⚠️⚠️ **This exists because the iPhone got left behind twice.** Android and web are one command each;
# the iPhone was a *document* — `docs/03_Architecture/iPhone_Free_Provisioning.md` — and twice a release
# went out to two platforms while the owner's own phone stayed on an older build. ⭐ *A step that must
# happen every release and lives only in prose is a step that gets skipped.*
#
# ⭐⭐ **This is NOT TestFlight and does not replace it.** Free provisioning puts the app on *your own*
# phone with a personal Apple ID, for £0. Other people's phones still need the £79/yr programme — that is
# the decision ADR-239 defers, and conflating the two is what made "no iOS pipeline exists" sound true.
#
# 🔴 **The seven days is the trade.** A free-provisioned certificate expires and the app stops launching.
# Re-running this fixes it in about a minute, and you will do that weekly for as long as you stay free.
#
# Usage:   scripts/release_ios.sh                 # the connected iPhone, pointed at the live API
#          scripts/release_ios.sh <device-id>     # …a specific one, if several are attached
set -euo pipefail
cd "$(dirname "$0")/.."

API="${MADBOOTS_API:-https://madboots-api.onrender.com}"

# ── 1. find the phone ─────────────────────────────────────────────────────────────────────────────
# ⭐ Discovered, never hard-coded: the provisioning doc names a device id, and a device id in prose is a
# device id that goes stale the day the phone is replaced.
device="${1:-}"
if [ -z "$device" ]; then
  device=$( (cd mobile && flutter devices --machine 2>/dev/null) | python3 -c "
import json, sys
phones = [d for d in json.load(sys.stdin)
          if d.get('targetPlatform') == 'ios' and not d.get('emulator')]
print(phones[0]['id'] if len(phones) == 1 else '')
" )
fi
if [ -z "$device" ]; then
  echo "  ✗ no iPhone found."
  echo "    Plug it in (or be on the same Wi-Fi), unlock it, and make sure the Mac is trusted."
  echo "    With more than one attached, pass the id: scripts/release_ios.sh <device-id>"
  exit 1
fi

version=$(grep '^version:' mobile/pubspec.yaml | awk '{print $2}')
echo "  installing $version on $device"

# ── 1b. gate ──────────────────────────────────────────────────────────────────────────────────────
# ⭐ Same gate as the Android script, same reason (ADR-322, closing ADR-221): the Dart suite's one chance to
# stop a build is before it, because afterwards the app is on the phone.
#
# ⚠️ After the device lookup on purpose — a missing cable is the commonest failure and costs nothing to
# detect, so it is worth finding before spending 18 seconds on tests that were going to pass.
echo "  checking…"
(cd mobile && flutter analyze >/tmp/release_ios_check.log 2>&1) \
  || { echo "  ANALYZE FAILED — see /tmp/release_ios_check.log"; exit 1; }
(cd mobile && flutter test >>/tmp/release_ios_check.log 2>&1) \
  || { echo "  TESTS FAILED — see /tmp/release_ios_check.log"; exit 1; }

# ── 2. build ──────────────────────────────────────────────────────────────────────────────────────
# ⚠️⚠️ **The API address is baked in at BUILD time** — `flutter install` has no `--dart-define`, and a
# build without this points at `localhost`, which on a phone **is the phone**. ⭐ Every screen would fail
# and nothing would say why.
#
# ⚠️ And deliberately **no `MADBOOTS_DEV`**: that flag adds the Settings ▸ Server field for aiming at a
# laptop (ADR-270). This build is the real one, so it gets the real address and no way to change it.
#
# ── 1c. make the seven days real ──────────────────────────────────────────────────────────────────
# 🔴🔴 **This script's promise was false and the phone proved it.** On 2026-10-30 the app was reinstalled at
# 14:35 and stopped launching at **14:52** — `flutter build ios` had re-signed with a **cached profile
# created seven days earlier**, so re-running bought seventeen minutes. The warning at the bottom said
# *"re-running this fixes it"*, which is only true if the build mints a NEW profile. It does not; it reuses
# whatever is cached until the cache is cleared.
#
# ⭐⭐ *"Re-running fixes it" was an instruction that quietly stopped being true, and nothing checked.*
# Xcode reissues automatically once the stale file is gone, so the fix is to take it away.
#
# ⚠️ Moved, never deleted: if Apple cannot be reached the build fails, and the owner should still have the
# file that was working this morning.
. "$(dirname "$0")/lib/ios_profile.sh"
stale_dir="${TMPDIR:-/tmp}/madboots-stale-profiles"
for dir in "${IOS_PROFILE_DIRS[@]}"; do
  [ -d "$dir" ] || continue
  for prof in "$dir"/*.mobileprovision; do
    [ -e "$prof" ] || continue
    case "$(profile_name "$prof")" in *com.madboots.fpl*) ;; *) continue ;; esac
    exp=$(profile_expiry "$prof")
    [ -n "$exp" ] || continue
    left=$(hours_left "$exp") || continue
    if should_purge "$exp" "$IOS_PROFILE_MIN_HOURS"; then
      mkdir -p "$stale_dir" && mv "$prof" "$stale_dir/"
      if [ "$left" -lt 0 ]; then
        echo "  ⟳ cached profile expired ${left#-}h ago — set aside so Xcode issues a fresh seven days"
      else
        echo "  ⟳ cached profile has only ${left}h left — set aside so Xcode issues a fresh seven days"
      fi
    fi
  done
done

# ⭐ `--release`, not debug: a debug build is materially slower on a phone, and judging the app's feel from
# one would be judging the wrong thing.
(cd mobile && flutter build ios --release --dart-define=MADBOOTS_API="$API" >/tmp/release_ios.log 2>&1) \
  || { echo "  ✗ build failed:"; tail -20 /tmp/release_ios.log; exit 1; }
echo "  built $(grep -o 'Runner.app ([0-9.]*MB)' /tmp/release_ios.log | tail -1)"

# ── 3. install ────────────────────────────────────────────────────────────────────────────────────
# ⭐ `install`, not `run`: `run` stays attached and quitting it **terminates the app on the phone**. This
# leaves the app installed and the terminal free.
#
# 🔴🔴 **And a fallback, because `flutter install` loses the phone while the phone is right there**
# (ADR-366). On 2026-10-23 it failed twice with *"No target device found… enable Developer Mode"* — on a
# device `flutter devices` had just listed and `devicectl` reported `available (paired)`, with Developer
# Mode already on. ⚠️⚠️ *That message is flutter's guess when its own lookup fails, not something the
# phone said*, and it sent the owner to check a setting that was not the problem.
#
# ⭐⭐ Apple's own tool installed to the same UDID without complaint, and this script **already trusts it**
# — step 4 asks `devicectl` whether the app is really there. So it does the installing too when flutter
# cannot. ⚠️ Announced, never silent: *a fallback nobody is told about turns a broken tool into a mystery
# that gets rediscovered.*
if ! (cd mobile && flutter install -d "$device" >>/tmp/release_ios.log 2>&1); then
  echo "  ⓘ  flutter could not reach the device — using Apple's installer instead"
  if ! xcrun devicectl device install app --device "$device" \
        mobile/build/ios/iphoneos/Runner.app >>/tmp/release_ios.log 2>&1; then
    echo "  ✗ install failed, both ways:"
    tail -20 /tmp/release_ios.log
    exit 1
  fi
fi

# ── 4. prove it ───────────────────────────────────────────────────────────────────────────────────
# ⭐⭐ **Asks the phone, not the log.** A build that succeeded and an app that is on the device are
# different claims, and this script exists because the second one was assumed twice.
installed=$(xcrun devicectl device info apps --device "$device" 2>/dev/null \
            | awk '/com\.madboots\.fpl/ {print $3" ("$4")"}' | head -1)
if [ -n "$installed" ]; then
  echo "  ✅ on the phone: MADBOOTS $installed"
else
  echo "  ⓘ  installed — the device did not answer a version query, so check the home screen"
fi

# ── 5. say WHEN it dies ───────────────────────────────────────────────────────────────────────────
# ⭐⭐ **Read from the artefact, not asserted from the calendar.** The old line here said "expires after
# SEVEN DAYS", which is a fact about free provisioning and was **not** a fact about the build it had just
# installed — that one had seventeen minutes left. ⭐ *A warning that states the policy instead of the
# measurement cannot tell you the policy was not applied.*
expiry=$(profile_expiry mobile/build/ios/iphoneos/Runner.app/embedded.mobileprovision)
read -r verdict left iso <<<"$(expiry_verdict "$expiry")"
pretty=$(pretty_date "${iso:-}")
echo
case "$verdict" in
  critical)
    # 🔴 The symptom of the 2026-10-30 failure recurring. Loud, because the app dies before the owner next
    # thinks about it.
    echo "  🔴 THIS BUILD EXPIRES IN ${left}h — $pretty"
    echo "     That is not a fresh seven days: the build re-used a cached profile. Re-run this script." ;;
  ok)
    echo "  ⚠️  This build stops launching on $pretty (${left}h from now)."
    echo "     Re-run this script to renew it — that weekly minute is what the £79/yr buys away (ADR-239)." ;;
  *)
    echo "  ⚠️  Could not read the build's expiry, so the seven days is unverified here."
    echo "     Free provisioning expires after SEVEN DAYS; re-run this script to renew it (ADR-239)." ;;
esac
