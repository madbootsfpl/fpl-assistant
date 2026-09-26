# ADR-304 — A cache that hid a feature

**Date:** 2026-09-26
**Status:** ✅ **Built.**
**From:** the owner — *"the web version is not showing 'Ask' in the More Tab"*, before a release he had
asked for.

---

## Ask was deployed the whole time

⭐ **Checked before changing anything**: `curl` on the served bundle found `"Ask about your squad"` in
`main.dart.js`. The server had it. The browser was running an app from before it existed.

## Two caches, stacked

⚠️⚠️⚠️ **A Cloudflare zone setting rewrites `Cache-Control` on the custom domain.** Proven by asking both
hosts the same question:

| file | Pages origin | `madboots.com` |
|---|---|---|
| `flutter_bootstrap.js` | `no-cache` | **`max-age=14400`** |
| `main.dart.js` | `no-cache` | **`max-age=14400`** |
| `madboots-20.apk` | `max-age=0, must-revalidate` | **`max-age=14400`** |
| `index.html` | `max-age=0, must-revalidate` | `max-age=0, must-revalidate` |

The origin honours `_headers`; the zone overrides it to four hours for `.js` and `.apk`, and leaves HTML
alone. ⭐⭐ **This is also what caused the APK staleness in ADR-282** — the versioned filenames adopted then
were the right instinct against a cause nobody had named.

⚠️⚠️ **And a service worker on top of it**, caching the whole app shell and surviving reloads.

## Fixed without touching the dashboard

⭐ **`index.html` is the hook**, because it is the one file the zone does not override: it always
revalidates, so whatever it points at is fetched. `scripts/release_web.sh` stamps the build number onto
`flutter_bootstrap.js?v=N` and `main.dart.js?v=N` — ⭐ *a URL that has never been requested cannot be
stale*, which is ADR-282's fix applied to the web. Flutter version-stamps its service worker and **not**
these two; `main.dart.js` in particular has a stable name and changing contents, which is exactly what a
long `max-age` gets wrong.

⭐⭐ **No service worker at all** (`--pwa-strategy=none`). Flutter's own bootstrap calls it *"deprecated and
will be removed in a future Flutter release"*, and this app cannot do a single useful thing offline —
every screen is an API call. ⚠️ *A cache layer for an app that cannot work offline is all of the staleness
and none of the benefit.*

⚠️ **A kill switch is left at `flutter_service_worker.js`**, because turning the worker off does not
remove the ones already installed. A registration survives until it unregisters itself or its script
stops being servable — and **Pages does not 404 a missing file, it serves the index page**, which a
browser cannot parse as a worker and therefore treats as *"no update"*. ⭐ *The old worker would have
outlived the decision to stop using workers*, on exactly the machines that already had the problem.

**Verified:** `service worker registrations: 0`, and Ask renders in More on a headless desktop Chrome.

## The deploy is a script now

📌 It was me typing four commands. ⭐ *A deploy that lives in someone's shell history is a deploy that is
slightly different every time* — and this one has a cache-busting step that must not be forgotten.

## What is left, and it is the owner's

🔴 **One Cloudflare setting is the clean root fix**: Caching → Configuration → **Browser Cache TTL →
"Respect Existing Headers"**. That would let `_headers` do this on its own and retire the stamping. It is
an account-wide setting, so it is not mine to change — and the stamping is correct either way, because
⚠️ *a fix that depends on a dashboard nobody can see from the repo is a fix the next person cannot
verify.*
