#!/usr/bin/env bash
# Run ONE pipeline tick against a Postgres, prompting for the connection string (docs ADR-211).
#
# ⭐ Prompts rather than taking the DSN on the command line, because that string contains the **database
# password** — the most powerful credential in the project — and a command line lands in shell history.
#
#   ./scripts/pipeline_once.sh            # refresh if due
#   ./scripts/pipeline_once.sh --force    # refresh regardless (use this to populate a fresh database)
set -uo pipefail

if [ -z "${FPL_DATABASE_URL:-}" ]; then
  printf 'Paste the Supabase connection string (with the password filled in)\n(it will not be shown) > '
  stty -echo 2>/dev/null; IFS= read -r FPL_DATABASE_URL; stty echo 2>/dev/null; printf '\n\n'
fi
: "${FPL_DATABASE_URL:?no connection string given}"

case "$FPL_DATABASE_URL" in
  *"[YOUR-PASSWORD]"*)
    echo "🔴 The placeholder is still in the string — replace [YOUR-PASSWORD] with the real password."
    echo "   Supabase never shows it again: Project Settings → Database → Reset database password."
    exit 1 ;;
  postgresql://*|postgres://*) ;;
  *) echo "🔴 That does not look like a connection string (it should start postgresql://)."; exit 1 ;;
esac

case "$FPL_DATABASE_URL" in
  *pooler.supabase.com*) echo "✅ Pooler connection — reachable from GitHub Actions." ;;
  *supabase.co*)         echo "⚠️  This looks like the DIRECT connection, which is IPv6-only on most"
                         echo "    projects — GitHub Actions cannot reach it. Use a pooler string instead." ;;
esac

PY=venv/bin/python; [ -x "$PY" ] || PY=python3
echo
exec env FPL_DATABASE_URL="$FPL_DATABASE_URL" "$PY" app.py pipeline "$@"
