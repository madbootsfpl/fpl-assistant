#!/usr/bin/env bash
# Run MadBoots locally against the Supabase STAGING project (docs/SUPABASE_STAGING.md, Step 5).
#
# Every one of the seven user-data tables derives its endpoint from FPL_STORE_URL's base plus FPL_STORE_KEY,
# so these two variables move the whole user-data layer. ⭐ No code changes, and closing the app puts you
# straight back — nothing is written to a file.
#
#   ./scripts/run_app_staging.sh            the app, open gate
#   ./scripts/run_app_staging.sh --gate      + the registration gate, already AT CAP
#
# ⭐ `--gate` is how you test the waitlist write through the real UI without setting up Google OIDC. Three
# paths call `waitlist.add()` and they hit the same table: `bad_code` (wrong invite code), `full` (at the
# cap) and `not_listed` (Google sign-in, not allow-listed). The first two need no auth at all, so they
# exercise the locked-down write end to end — and that write is **fail-silent**, which is exactly why it has
# to be watched by hand rather than trusted.
set -uo pipefail

[ -f .env.staging ] || { echo "No .env.staging — copy .env.staging.example and fill it in."; exit 1; }
set -a; . ./.env.staging; set +a
: "${SUPA_URL:?SUPA_URL is empty in .env.staging}"
: "${SUPA_KEY:?SUPA_KEY is empty in .env.staging}"

# ⚠️⚠️ **The one failure that is invisible from inside the app.** `access.secret()` reads `st.secrets` BEFORE
# the environment, so a secrets file naming FPL_STORE_URL silently wins — and you would be writing to
# PRODUCTION while every screen told you it was working. Refuse rather than warn: the cost of being wrong
# here is real tester data, and the cost of stopping is ten seconds.
if [ -f .streamlit/secrets.toml ] && grep -q "FPL_STORE_URL" .streamlit/secrets.toml 2>/dev/null; then
  echo "🔴 .streamlit/secrets.toml sets FPL_STORE_URL, and st.secrets beats the environment."
  echo "   This run would use THAT value, not staging. Move the file aside and try again."
  exit 1
fi

echo "Target: ${SUPA_URL}"

# Positive identification, not a guess: staging is the project seeded with .invalid addresses at Step 3.
seed=$(curl -s "${SUPA_URL}/rest/v1/beta_users?select=email&limit=3" \
         -H "apikey: ${SUPA_KEY}" -H "Authorization: Bearer ${SUPA_KEY}" 2>/dev/null)
case "$seed" in
  *".invalid"*) echo "✅ Confirmed staging (the .invalid seed rows are present)." ;;
  *)            echo "⚠️  Could NOT find the .invalid seed rows. If this is production, stop now (Ctrl-C)."
                echo "    Continuing in 5s…"; sleep 5 ;;
esac

ADMIN_VARS=()
if [ -n "${SUPA_SERVICE_KEY:-}" ]; then
  # ⚠️ The Admin roster needs this after Stage B revokes anon's access to beta_users. Server-side only.
  ADMIN_VARS=(FPL_ADMIN_STORE_KEY="${SUPA_SERVICE_KEY}")
  echo "🔑 Admin service-role key present — the roster will render."
else
  echo "ℹ️  No SUPA_SERVICE_KEY — the Admin roster will be EMPTY (expected after Stage B)."
fi

GATE_VARS=()
if [ "${1:-}" = "--gate" ]; then
  # The staging project was seeded with exactly 3 allow-listed users, so a cap of 3 is already full.
  GATE_VARS=(FPL_ACCESS_CODE=stagingcode FPL_USER_CAP=3)
  echo "🔒 Registration gate ON — invite code 'stagingcode', cap 3 (staging has 3 users, so it is AT CAP)."
fi

# ⚠️ **Streamlit silently moves to the next free port**, so a forgotten instance on 8501 means this run lands
# on 8502 while the browser tab you open out of habit shows the OLD one — which may have different settings
# (no gate, a different database) and will look like "nothing happened". ⭐ *A process you forgot is still a
# process that answers.*
if lsof -iTCP:8501 -sTCP:LISTEN -P >/dev/null 2>&1; then
  echo
  echo "⚠️  Port 8501 is already in use, so this run will start on 8502 or higher."
  echo "    Watch the 'Local URL' line below — and consider stopping the old one first:"
  lsof -iTCP:8501 -sTCP:LISTEN -P 2>/dev/null | awk 'NR>1 {print "      kill " $2 "   # " $1}'
  echo
fi

PY=venv/bin/python; [ -x "$PY" ] || PY=python3
echo
echo "Starting the app against staging. Ctrl-C to stop; nothing persists after that."
echo
exec env \
  FPL_STORE_URL="${SUPA_URL}/rest/v1/squads" \
  FPL_STORE_KEY="${SUPA_KEY}" \
  FPL_LOCAL=1 \
  "${GATE_VARS[@]}" \
  "${ADMIN_VARS[@]}" \
  "$PY" -m src.web_streamlit
