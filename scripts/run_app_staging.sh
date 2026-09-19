#!/usr/bin/env bash
# Run MadBoots locally against the Supabase STAGING project (docs/SUPABASE_STAGING.md, Step 5).
#
# Every one of the seven user-data tables derives its endpoint from FPL_STORE_URL's base plus FPL_STORE_KEY,
# so these two variables move the whole user-data layer. ⭐ No code changes, and closing the app puts you
# straight back — nothing is written to a file.
#
#   ./scripts/run_app_staging.sh
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

PY=venv/bin/python; [ -x "$PY" ] || PY=python3
echo
echo "Starting the app against staging. Ctrl-C to stop; nothing persists after that."
echo
FPL_STORE_URL="${SUPA_URL}/rest/v1/squads" \
FPL_STORE_KEY="${SUPA_KEY}" \
FPL_LOCAL=1 \
exec "$PY" -m src.web_streamlit
