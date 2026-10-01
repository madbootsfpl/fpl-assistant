#!/usr/bin/env bash
# Cut a build and put it on the owner's iPhone ONLY. Nothing reaches the testers (ADR-340).
#
# ⭐⭐ **The iPhone is the staging environment**, because it already is one: `release_ios.sh` installs
# to one phone with free provisioning, and no other platform can receive a build without the nine
# testers receiving it too. ⚠️ *A staging environment you already own beats a better one you have to
# build* — this costs one env var and two scripts rather than a second API, a second database and a
# second set of credentials to keep honest.
#
# ⚠️⚠️ **This deliberately re-introduces the step ADR-290 removed.** That ADR automated publishing
# because *"a publish step a person has to remember is a publish step that measures how busy they are"*
# — the live build once sat **three releases behind**. The difference now is that the step buys
# something: a build nobody has opened does not reach nine people. ⭐ The risk is identical, so the
# mitigation is noise: this script ends by saying it is not live, and `ship.sh` says what it is about
# to publish before it does.
#
# Usage:  scripts/release_stage.sh          # bump, build, install on the phone
#         scripts/release_ship.sh           # …then publish to web + Android
# ⚠️ **"Staging" already means something else in this repo**: `run_app_staging.sh` points the app at a
# staging **Supabase** project (`docs/SUPABASE_STAGING.md`) — that is the *data* layer. This is the
# *build* layer, and the two are unrelated. ⭐ Named `release_*` so it groups with its siblings rather
# than with the word it shares.
set -euo pipefail
cd "$(dirname "$0")/.."

export MADBOOTS_STAGE_ONLY=1

echo "═══ STAGING — nothing will be published ═══"
echo
scripts/release_android.sh
echo
scripts/release_web.sh
echo
# ⚠️ Last, and not gated: this is the whole point of staging, and it touches one phone.
scripts/release_ios.sh

version=$(grep '^version:' mobile/pubspec.yaml | awk '{print $2}')
echo
echo "═══════════════════════════════════════════════════════════════════"
echo "  $version is on the phone. It is NOT live."
echo
echo "  The nine testers are still on whatever madboots.com/app/ says."
echo "  When you are happy:   scripts/release_ship.sh"
echo "═══════════════════════════════════════════════════════════════════"
