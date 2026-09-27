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

# ── 2. build ──────────────────────────────────────────────────────────────────────────────────────
# ⚠️⚠️ **The API address is baked in at BUILD time** — `flutter install` has no `--dart-define`, and a
# build without this points at `localhost`, which on a phone **is the phone**. ⭐ Every screen would fail
# and nothing would say why.
#
# ⚠️ And deliberately **no `MADBOOTS_DEV`**: that flag adds the Settings ▸ Server field for aiming at a
# laptop (ADR-270). This build is the real one, so it gets the real address and no way to change it.
#
# ⭐ `--release`, not debug: a debug build is materially slower on a phone, and judging the app's feel from
# one would be judging the wrong thing.
(cd mobile && flutter build ios --release --dart-define=MADBOOTS_API="$API" >/tmp/release_ios.log 2>&1) \
  || { echo "  ✗ build failed:"; tail -20 /tmp/release_ios.log; exit 1; }
echo "  built $(grep -o 'Runner.app ([0-9.]*MB)' /tmp/release_ios.log | tail -1)"

# ── 3. install ────────────────────────────────────────────────────────────────────────────────────
# ⭐ `install`, not `run`: `run` stays attached and quitting it **terminates the app on the phone**. This
# leaves the app installed and the terminal free.
(cd mobile && flutter install -d "$device" >>/tmp/release_ios.log 2>&1) \
  || { echo "  ✗ install failed:"; tail -20 /tmp/release_ios.log; exit 1; }

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

echo
echo "  ⚠️  Free provisioning expires after SEVEN DAYS and the app stops launching."
echo "     Re-run this script to fix it. That weekly minute is what the £79/yr buys away (ADR-239)."
