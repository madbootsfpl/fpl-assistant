#!/usr/bin/env bash
# What the anon key can actually see (ADR-211 / docs/SUPABASE_RLS.md).
#
# ⭐ **Run this BEFORE and AFTER the hardening.** The point is the difference: Stage A must turn the waitlist
# dump into a refusal while leaving the app's own reads working. Without a "before" there is nothing to
# compare a "after" against, and a fix that did nothing looks identical to one that worked.
#
# ⚠️ **The Supabase SQL Editor cannot do this job.** It runs as the table owner, and owners bypass RLS — so a
# permission test run there passes whatever the policies say. Only the anon key sees what the app sees.
#
#   cp .env.staging.example .env.staging   # then fill it in (.env.* is gitignored)
#   ./scripts/supabase_probe.sh
#
# Reads SUPA_URL and SUPA_KEY from the environment, or from .env.staging if present.
set -uo pipefail
BAD_KEY=0

# ⚠️ **Explicit environment wins over the file.** The first version sourced .env.staging unconditionally, so
# `SUPA_URL=<production> ./scripts/supabase_probe.sh` would have silently probed STAGING and reported it as
# production — the worst possible failure for a script whose whole job is telling you which is which.
if [ -z "${SUPA_URL:-}" ] && [ -f .env.staging ]; then
  set -a; . ./.env.staging; set +a
  echo "(credentials from .env.staging)"
fi

: "${SUPA_URL:?set SUPA_URL (https://<ref>.supabase.co) in .env.staging or the environment}"

# ⚠️ **Prompt for the key rather than making the caller build a shell one-liner.** The first version of that
# instruction used `read -s -p`, which is **bash**; the owner's shell is **zsh**, where `-p` means coprocess —
# so the command errored and the check silently did not run. ⭐ *An instruction that only works in one shell
# is a step that will sometimes be skipped without anyone noticing.* Doing it here works in both.
if [ -z "${SUPA_KEY:-}" ]; then
  printf 'Paste the anon / publishable key for %s
(it will not be shown) > ' "$SUPA_URL"
  stty -echo 2>/dev/null; IFS= read -r SUPA_KEY; stty echo 2>/dev/null; printf '

'
fi
: "${SUPA_KEY:?no key given (the anon / publishable key — NEVER the service_role key)}"

echo "Target: ${SUPA_URL}"
echo "⚠️  Confirm that host is STAGING before reading anything below."
echo

probe() {                       # probe <label> <path> <what a hardened system should do>
  printf '── %s\n' "$1"
  local body code
  body=$(curl -s -w '\n%{http_code}' "${SUPA_URL}/rest/v1/$2" \
              -H "apikey: ${SUPA_KEY}" -H "Authorization: Bearer ${SUPA_KEY}")
  code=$(printf '%s' "$body" | tail -n1)
  body=$(printf '%s' "$body" | sed '$d')
  # ⚠️⚠️ **"The lock works" and "the key is wrong" both return 401**, and four of the latter reads as total
  # success at a glance. It happened: a mistyped key produced 401 on every probe, including `maddie_videos`
  # which is supposed to stay readable. ⭐ *A check that cannot distinguish two outcomes is not a check* —
  # so an invalid key is called out as a broken RUN, not reported as a result.
  case "$body" in
    *"Invalid API key"*|*"invalid JWT"*|*"JWSError"*)
      printf '   🔴 HTTP %s — THE KEY WAS REJECTED. This is not a permission result.\n' "$code"
      printf '      Nothing below can be trusted; fix the key and run again.\n\n'
      BAD_KEY=1
      return ;;
  esac
  printf '   HTTP %s\n   %s\n   after Stage A, expect: %s\n\n' "$code" "${body:0:300}" "$3"
}

probe "beta_users — the allow-list (real tester emails in production)" \
      "beta_users?select=email" \
      "unchanged for now; Stage B replaces the whole-table read with a boolean RPC"

probe "beta_waitlist — people who were REFUSED" \
      "beta_waitlist?select=email,reason" \
      "🔴 an empty list or a permission error — this is Stage A's main win"

probe "squads — enumerate every saved squad without knowing a handle" \
      "squads?select=handle" \
      "unchanged for now; Stage B's RPCs are what stop enumeration"

probe "maddie_videos — public marketing content" \
      "maddie_videos?select=topic" \
      "unchanged — public read is correct here"

if [ "${BAD_KEY:-0}" = "1" ]; then
  echo "🔴 THE RUN IS INVALID — the API key was rejected, so every 401 above means 'bad key', not 'locked'."
  echo "   Common causes: the surrounding quotes were copied from secrets.toml, the paste was truncated,"
  echo "   or it is a key from the other project. Copy it from Project Settings → API, value only."
  exit 1
fi
echo "⭐ Write these down. The fix is only visible as a difference."
