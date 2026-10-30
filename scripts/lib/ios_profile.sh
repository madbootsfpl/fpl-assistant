#!/usr/bin/env bash
# Provisioning-profile arithmetic for release_ios.sh (ADR-379).
#
# ⭐⭐ **Its own file because the release script cannot be run by a test** — it needs a phone. The decision
# that went wrong was pure arithmetic on two timestamps, so it lives where `tests/test_ios_release.py` can
# drive it with synthetic dates. ⚠️ *A rule tested by grepping for its own source text is not tested.*
#
# 🔴 The bug these exist for: on 2026-10-30 the app was reinstalled at 14:35 and stopped launching at
# 14:52. `flutter build ios` had **reused a cached profile created seven days earlier**, so re-signing
# bought seventeen minutes. The script's own docstring promised *"re-running this fixes it in about a
# minute"* — which is only true if the build mints a NEW profile, and it does not.
#
# Pure: no side effects, no `set -e` of its own. Source it and call.

# Where Xcode keeps them. The first is Xcode 15+; the second is the historical location and is still read
# by older toolchains, so both are swept rather than assumed.
IOS_PROFILE_DIRS=(
  "$HOME/Library/Developer/Xcode/UserData/Provisioning Profiles"
  "$HOME/Library/MobileDevice/Provisioning Profiles"
)

# How little life makes a cached profile not worth keeping. ⭐ **48 hours, and the direction of the risk
# decides it.** Purging a profile only helps if Apple then issues a new one — so purging one that is still
# *useful* trades a working build for a network round trip that can fail. At under two days the cached
# profile is about to be worthless anyway, so there is nothing left to lose. ⚠️ Deliberately NOT "always
# reissue": that would turn an offline laptop from an inconvenience into a failed release.
IOS_PROFILE_MIN_HOURS="${IOS_PROFILE_MIN_HOURS:-48}"

iso_epoch() {   # $1 = 2026-11-06T19:48:46Z  ->  epoch seconds
  # ⚠️ BSD `date` needs the format spelled out; GNU `date -d` is not available on a stock Mac.
  date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$1" "+%s" 2>/dev/null
}

hours_left() {  # $1 = ISO expiry, $2 = optional "now" epoch (for tests)  -> whole hours, may be negative
  local exp now
  exp=$(iso_epoch "$1") || return 1
  [ -n "$exp" ] || return 1
  now="${2:-$(date -u "+%s")}"
  echo $(( (exp - now) / 3600 ))
}

profile_expiry() {   # $1 = a .mobileprovision (or an app bundle's embedded one) -> ISO expiry
  security cms -D -i "$1" 2>/dev/null | plutil -extract ExpirationDate raw - 2>/dev/null
}

profile_name() {     # $1 = a .mobileprovision -> its Name, used to tell ours from other projects'
  security cms -D -i "$1" 2>/dev/null | plutil -extract Name raw - 2>/dev/null
}

should_purge() {     # $1 = ISO expiry, $2 = threshold hours, $3 = optional now epoch. 0 = purge it.
  local left
  left=$(hours_left "$1" "${3:-}") || return 1    # unreadable date → do not touch it
  [ "$left" -lt "$2" ]
}

# ⭐⭐ **The verdict is separated from the wording so the verdict can be tested.** This whole file exists
# because a *message* was wrong — "expires after SEVEN DAYS" on a build with seventeen minutes left — so
# the branch that decides which message to print is the last place to leave untested. Prints one of:
#
#   critical <hours> <iso>   — under a day: the cached-profile bug has recurred, say so loudly
#   ok       <hours> <iso>   — a real week
#   unknown                  — no readable expiry; claim nothing
IOS_PROFILE_ALARM_HOURS="${IOS_PROFILE_ALARM_HOURS:-24}"

expiry_verdict() {   # $1 = ISO expiry (may be empty), $2 = optional now epoch
  local left
  [ -n "${1:-}" ] || { echo "unknown"; return 0; }
  left=$(hours_left "$1" "${2:-}") || { echo "unknown"; return 0; }
  [ -n "$left" ] || { echo "unknown"; return 0; }
  if [ "$left" -lt "$IOS_PROFILE_ALARM_HOURS" ]; then
    echo "critical $left $1"
  else
    echo "ok $left $1"
  fi
}
