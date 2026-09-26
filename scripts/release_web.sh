#!/usr/bin/env bash
# Publish the Flutter web build to madboots.com/app/web/ (ADR-301's measurement, ADR-304's cache fix).
#
# ⚠️⚠️⚠️ **The whole reason this is a script and not two commands is the cache.** Cloudflare's zone for
# `madboots.com` rewrites `Cache-Control` to `max-age=14400` for `.js` — measured 2026-09-26: the Pages
# origin serves the `no-cache` that `_headers` asks for, and the custom domain serves four hours. So a
# deploy went live and every browser that had already opened the app kept serving the old one **through a
# reload**, for four hours.
#
# ⭐⭐ *This is the APK bug's twin, and it gets the APK bug's fix*: a URL that has never been requested
# cannot be stale. Flutter already version-stamps its service worker; it does **not** stamp
# `flutter_bootstrap.js` or `main.dart.js`, which are the two the browser holds.
#
# 📌 The cleaner fix is one dashboard setting — Caching → Browser Cache TTL → **Respect Existing Headers**
# — which is the owner's to make, and would let `_headers` do this on its own.
set -euo pipefail

SITE="${MADBOOTS_SITE:-$HOME/madboots-site}"
API="${MADBOOTS_API:-https://madboots-api.onrender.com}"
PROJECT="${MADBOOTS_PAGES_PROJECT:-madboots}"

# ⭐ The same build number the APK carries, so a tester's *"which version am I on?"* has one answer.
version=$(grep '^version:' mobile/pubspec.yaml | awk '{print $2}')
build="${version##*+}"
echo "  building web for $version"

# ⚠️⚠️⚠️ **`--pwa-strategy=none`: no service worker, deliberately.** Flutter's own bootstrap calls it
# *"deprecated and will be removed in a future Flutter release"*, and this app cannot do a single useful
# thing offline — every screen is an API call. ⭐ *A cache layer for an app that cannot work offline is
# all of the staleness and none of the benefit*, and it is the layer that made a shipped feature look
# missing: the owner opened More and Ask was not there, because his browser was serving an app from
# before it existed.
(cd mobile && flutter build web --release --base-href /app/web/ --pwa-strategy=none \
    --dart-define=MADBOOTS_API="$API" >/tmp/release_web.log 2>&1) \
  || { echo "  ✗ build failed:"; tail -20 /tmp/release_web.log; exit 1; }

# ⚠️ Stamped **after** the build, on the output. Flutter regenerates both files every time, so editing
# them in the repo would be editing something that does not survive.
python3 - "mobile/build/web" "$build" <<'PY'
import pathlib, sys
out, build = pathlib.Path(sys.argv[1]), sys.argv[2]

index = out / "index.html"
html = index.read_text()
# ⭐ `index.html` is the one file the zone does NOT override — it still carries `max-age=0,
# must-revalidate` — so it is the hook: it always revalidates, and it points at a versioned URL.
before = html
html = html.replace('src="flutter_bootstrap.js"', f'src="flutter_bootstrap.js?v={build}"')
assert html != before, "index.html no longer loads flutter_bootstrap.js — the stamp missed"
index.write_text(html)

boot = out / "flutter_bootstrap.js"
js = boot.read_text()
# ⚠️ `main.dart.js` is referenced as a bare string literal and Flutter does not hash it into the
# filename — *the name is stable and the contents are not*, which is exactly what a four-hour cache gets
# wrong. The service worker is already `?v=<serviceWorkerVersion>` and needs nothing.
hits = js.count('"main.dart.js"')
assert hits, "flutter_bootstrap.js no longer names main.dart.js — the stamp missed"
boot.write_text(js.replace('"main.dart.js"', f'"main.dart.js?v={build}"'))
print(f"  stamped v{build} onto flutter_bootstrap.js and {hits} main.dart.js reference(s)")
PY

# ⭐⭐ **A kill switch, because turning the worker off does not remove the ones already installed.** A
# registered service worker survives until it unregisters itself or its script stops being servable — and
# Cloudflare Pages does not 404 a missing file, it serves the index page, which a browser cannot parse as
# a worker and therefore treats as "no update". ⚠️ *The old worker would have outlived the decision to
# stop using workers*, on exactly the machines that already had the problem.
cat > mobile/build/web/flutter_service_worker.js <<'SW'
// Retired (ADR-304). This file exists only to unregister the worker a previous build installed:
// Pages serves index.html for anything missing, so deleting it would keep the old worker alive.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) { await caches.delete(key); }
    await self.registration.unregister();
    for (const client of await self.clients.matchAll({ type: 'window' })) {
      client.navigate(client.url);
    }
  })());
});
SW

rm -rf "$SITE/app/web"
mkdir -p "$SITE/app/web"
cp -R mobile/build/web/. "$SITE/app/web/"
echo "  staged $(du -sh "$SITE/app/web" | cut -f1) in $SITE/app/web"

if [ -n "${CLOUDFLARE_API_TOKEN:-}" ]; then
  # ⚠️ Deploys the whole site, like the Android script — `$SITE` is one folder and Pages takes all of it.
  npx --yes wrangler@4 pages deploy "$SITE" \
      --project-name="$PROJECT" --branch=main --commit-dirty=true 2>&1 | tail -4
  echo "  ✅ https://madboots.com/app/web/"
else
  echo "  ⓘ  not published: CLOUDFLARE_API_TOKEN is not set."
fi
