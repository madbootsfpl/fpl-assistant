#!/usr/bin/env bash
# The API, reachable from a phone on the same Wi-Fi (ADR-239).
#
# ⭐⭐ The only substantive difference from the one-liner in the Flutter checklist is `--host 0.0.0.0`.
# uvicorn binds to 127.0.0.1 by default, which accepts nothing that is not this machine — so a phone gets
# a refusal that is indistinguishable from "the server is not running". ⚠️ *A default that is correct for
# a laptop is the bug when the client is a handset.*
#
# ⚠️ macOS will ask, once, whether to allow incoming connections. Answer **Allow** — a Deny is remembered
# and the symptom afterwards is the same refusal, with nothing on screen to explain it.
#
# Usage: scripts/serve_api.sh [port]
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${1:-8078}"

# ⭐ Printed rather than left to be looked up, because this is the value that has to be typed into the
# phone's Settings screen and `ipconfig getifaddr` is not a command anyone remembers.
ADDRESS="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
if [ -n "$ADDRESS" ]; then
  echo "  This machine on the Wi-Fi:  http://${ADDRESS}:${PORT}"
  echo "  Put that in the app under More ▸ Settings ▸ Server, then press Check and use."
else
  echo "  ⚠️  No Wi-Fi address found — a phone will not be able to reach this."
fi
echo "  Interactive docs:           http://localhost:${PORT}/api/v1/docs"
echo

# ⚠️ --reload, because a server that is silently serving yesterday's code produces 404s on endpoints that
# exist, and three of those were chased as client bugs before the flag went in.
exec venv/bin/python -m uvicorn src.service.http:app \
  --host 0.0.0.0 --port "$PORT" --reload --reload-dir src
