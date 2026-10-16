#!/usr/bin/env bash
# Publish what `release_stage.sh` built — to the web and to the nine testers (ADR-340).
#
# ⭐ One deploy, not two. Both release scripts have always pushed the **whole** `$SITE` folder, so the
# APK, the web build and `version.json` go live together — ⚠️ *and they must, because the manifest is
# what prompts an update and it names an APK that has to be there when it does.*
set -euo pipefail
cd "$(dirname "$0")/.."

SITE="${MADBOOTS_SITE:-$HOME/madboots-site}"
PROJECT="${MADBOOTS_PAGES_PROJECT:-madboots}"

[ -d "$SITE/app" ] || { echo "  ✗ nothing staged at $SITE/app — run scripts/release_stage.sh first"; exit 1; }

# ⭐⭐ **Says what is about to happen before it happens.** `release_stage.sh` can run several times before anyone
# ships, so the build on disk is not necessarily the one you remember testing — ⚠️ *a publish step that
# does not name what it publishes is a publish step you cannot check.*
# ⚠️⚠️ **`MADBOOTS_NOTES` works HERE too, and it did not used to** (ADR-348). The notes are written into
# `version.json` at **stage** time by `release_android.sh`, so the override documented as "overriding
# everything" was unreachable from the command that actually publishes. ⭐⭐ *ADR-340 split one command in
# two and the escape hatch stayed with the half that builds, not the half you reach for when you read the
# bullets and find them wrong* — which is the only moment anybody wants it.
python3 - "$SITE/app/version.json" <<'PY'
import json, os, pathlib, sys
m = pathlib.Path(sys.argv[1])
if not m.exists():
    sys.exit("  ✗ no version.json staged — run scripts/release_stage.sh first")
d = json.loads(m.read_text())

override = [ln.strip() for ln in (os.environ.get("MADBOOTS_NOTES") or "").splitlines() if ln.strip()]
if override:
    d["notes"] = override
    m.write_text(json.dumps(d, indent=2) + "\n")

print(f"  about to publish build {d['build']}  ({d.get('url','')})")
for n in d.get("notes") or []:
    print(f"    · {n}")
if override:
    print("    ⓘ  notes replaced by MADBOOTS_NOTES")
if not d.get("notes"):
    print("    (no release notes — the banner will have no bullets)")
PY

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo
  echo "  ⓘ  not published: CLOUDFLARE_API_TOKEN is not set."
  echo "     Drag $SITE to Cloudflare Pages by hand."
  exit 0
fi

echo
echo "  publishing to Cloudflare Pages (project: $PROJECT)…"
if npx --yes wrangler@4 pages deploy "$SITE" \
      --project-name="$PROJECT" --branch=main --commit-dirty=true 2>&1 | tail -6; then
  echo "  ✅ live at https://madboots.com/        (testers prompted)"
  echo "  ✅ live at https://madboots.com/app/web/"
  echo
  echo "  NEXT: commit the version bump."
else
  echo "  ⚠️  publish failed — the files are still staged; drag $SITE to Cloudflare Pages instead"
  exit 1
fi
