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

# ⚠️ **Explicit environment wins over the file.** The first version sourced .env.staging unconditionally, so
# `SUPA_URL=<production> ./scripts/supabase_probe.sh` would have silently probed STAGING and reported it as
# production — the worst possible failure for a script whose whole job is telling you which is which.
if [ -z "${SUPA_URL:-}" ] && [ -f .env.staging ]; then
  set -a; . ./.env.staging; set +a
  echo "(credentials from .env.staging)"
fi

: "${SUPA_URL:?set SUPA_URL (https://<ref>.supabase.co) in .env.staging or the environment}"
: "${SUPA_KEY:?set SUPA_KEY (the anon / publishable key — NEVER the service_role key)}"

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

echo "⭐ Write these down. The fix is only visible as a difference."
