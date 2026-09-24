#!/usr/bin/env bash
# Cut an Android release: bump the build number, build the APKs, and stage the download page.
#
# ⚠️⚠️ **The build number is the whole point of this script.** Android decides *"is this an update?"* on
# `versionCode` alone — `versionName` is a label it ignores. Ship a new APK without bumping and every
# tester's phone refuses it **silently**: no error, no prompt, the old build simply stays.
#
# ⭐ *A step that must happen every time and is invisible when skipped is a step that belongs in a script,
# not in a person's memory.*
#
# Usage:   scripts/release_android.sh            # bump the build number, e.g. 1.0.0+3 -> 1.0.0+4
#          scripts/release_android.sh 1.1.0      # …and set a new version name too
set -euo pipefail

cd "$(dirname "$0")/.."
SITE="${MADBOOTS_SITE:-$HOME/madboots-site}"
API="${MADBOOTS_API:-https://madboots-api.onrender.com}"

# ── 1. bump ───────────────────────────────────────────────────────────────────────────────────────
current=$(grep '^version:' mobile/pubspec.yaml | awk '{print $2}')
name="${current%%+*}"; build="${current##*+}"
[ $# -ge 1 ] && name="$1"
next=$((build + 1))
python3 - "$name" "$next" <<'PY'
import pathlib, sys
name, build = sys.argv[1], sys.argv[2]
p = pathlib.Path('mobile/pubspec.yaml'); t = p.read_text()
import re
new = re.sub(r'^version: .*$', f'version: {name}+{build}', t, count=1, flags=re.M)
assert new != t, 'pubspec version line not found'
p.write_text(new)

# ⚠️ kAppVersion is what the app REPORTS to the usage panel — if it drifts from pubspec, the panel
# attributes new builds to the old version and a stale install becomes invisible.
c = pathlib.Path('mobile/lib/api/client.dart'); s = c.read_text()
# ⚠️ Asserts the constant was **found**, not that it changed. A rebuild under the same version name
# rewrites it to the identical text — ⭐ *"nothing changed" and "nothing matched" look the same to a
# diff, and only one of them is a bug.* The build number below always changes; the name often does not.
updated, hits = re.subn(r"const String kAppVersion = '[^']*';", f"const String kAppVersion = '{name}';", s, count=1)
assert hits == 1, 'kAppVersion not found'
# ⚠️ And the build number, which is what the update check actually compares on — ⭐ *bumping the name
# and not the number leaves a new build unable to tell it is newer than itself.*
updated2, hits = re.subn(r'const int kAppBuild = \d+;', f'const int kAppBuild = {build};', updated, count=1)
assert hits == 1, 'kAppBuild not found'
c.write_text(updated2)
PY
echo "  version: $current  ->  $name+$next"

# ── 2. build ──────────────────────────────────────────────────────────────────────────────────────
echo "  building…"
(cd mobile && flutter build apk --release --split-per-abi --dart-define=MADBOOTS_API="$API" >/tmp/release.log 2>&1) \
  || { echo "  BUILD FAILED — see /tmp/release.log"; exit 1; }

APK=mobile/build/app/outputs/flutter-apk/app-arm64-v8a-release.apk
# ⭐ Found, not hardcoded — *a path pinned to build-tools 36.0.0 breaks on the day they become 37.0.0,
# and breaks in a release script, which is the worst place to discover a broken path.*
# ⚠️ `|| true`: one of those globs will not exist on any given machine, `ls` reports that as failure,
# and under `set -e` a failing command substitution kills the script — ⭐ *after the build, which is the
# most expensive possible place to fall over.*
AAPT2=$(ls -d /opt/homebrew/share/android-commandlinetools/build-tools/*/aapt2 \
                "$HOME/Library/Android/sdk/build-tools"/*/aapt2 2>/dev/null | sort -V | tail -1 || true)
[ -x "$AAPT2" ] || { echo "  no aapt2 found — install Android build-tools"; exit 1; }
code=$("$AAPT2" dump badging "$APK" | grep -oE "versionCode='[0-9]+'" | head -1 | grep -oE '[0-9]+')
echo "  built: $(du -h "$APK" | cut -f1)  versionCode=$code"

# ── 3. stage the site ─────────────────────────────────────────────────────────────────────────────
# ⭐ `version.json` sits NEXT TO the APK it describes, so the two cannot disagree — *a manifest kept
# somewhere else is a manifest that will eventually describe a different build.*
mkdir -p "$SITE/app"
cp "$APK" "$SITE/app/madboots.apk"
cat > "$SITE/app/version.json" <<JSON
{
  "version": "$name",
  "build": $next,
  "versionCode": $code,
  "url": "https://madboots.com/app/madboots.apk",
  "notes": ""
}
JSON

# ⚠️⚠️ **A landing page, not a bare APK link.** Android refuses a sideloaded install until the browser
# is allowed to do it, and the prompt it shows ("for security, your phone is not allowed to install
# unknown apps") reads like a virus warning. ⭐ *Testers who hit that with no explanation do not ask —
# they stop.* This page says what will happen before it happens.
cat > "$SITE/app/index.html" <<HTML
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>MADBOOTS for Android</title>
<style>
 :root{--o:#ff7a18;--b:#0d1117}
 *{box-sizing:border-box}
 body{margin:0;background:var(--b);color:#e6edf3;font:16px/1.65 -apple-system,system-ui,sans-serif;
      padding:32px 20px;max-width:560px;margin-inline:auto}
 h1{font-size:1.5rem;margin:0 0 4px} .v{color:#8b949e;font-size:.85rem;margin-bottom:28px}
 a.dl{display:block;background:var(--o);color:#0d1117;font-weight:700;text-decoration:none;
      text-align:center;padding:15px;border-radius:10px;margin:0 0 28px}
 ol{padding-left:20px} li{margin-bottom:10px}
 .n{border-left:3px solid var(--o);background:#ff7a1815;padding:12px 14px;border-radius:0 8px 8px 0;
    font-size:.9rem;color:#c9d1d9}
</style></head><body>
<h1>MADBOOTS for Android</h1>
<div class="v">Version $name &middot; build $next</div>
<a class="dl" href="madboots.apk">Download the app</a>
<ol>
 <li>Tap <b>Download the app</b>. Chrome will warn that this file type can harm your device &mdash;
     that warning appears for every APK. Choose <b>Download anyway</b>.</li>
 <li>Open the downloaded file. Android will say this source is not allowed to install apps.
     Tap <b>Settings</b> and turn on <b>Allow from this source</b>, then go back.</li>
 <li>Tap <b>Install</b>, then <b>Open</b>.</li>
</ol>
<p class="n">Updating? Just download and install again &mdash; it installs over the old one and your
squad, plan and settings are kept. The app tells you when a newer build is here.</p>
</body></html>
HTML

echo
echo "  staged in $SITE/app:"
ls -lh "$SITE/app" | awk 'NR>1 {printf "    %-18s %s\n", $9, $5}'
echo
echo "  NEXT: drag $SITE to Cloudflare Pages, then commit the version bump."
echo "        testers go to https://madboots.com/app/"
