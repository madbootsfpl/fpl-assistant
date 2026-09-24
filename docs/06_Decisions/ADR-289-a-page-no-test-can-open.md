# ADR-289 — A page no test can open

**Date:** 2026-09-25
**Status:** Accepted
**From:** the owner — *"madboots.com page images look very big, could they be scaled to page fit
depending on device size?"* and then *"yes, bring it into the repo"*

---

## The image, first

The artwork is **377 × 378**. The CSS said `width:100%`, so it was **upscaled to 460px** on desktop —
blurry as well as large — and on a phone it rendered 341px tall against an 852px screen: ⭐ **40% of the
viewport, for a decorative picture of two boots.** On the owner's iPhone it spanned two screens.

⚠️ *An image told to fill its column will fill it whether or not it has the pixels to.*

It is now bounded by the **viewport** rather than the column, so it shrinks on a short window instead of
pushing the page down:

| | before | now |
|---|---|---|
| desktop 1900×1062 | 460px (upscaled) | **377px** — its own pixels |
| laptop 1440×900 | 460px | **342px** |
| iPhone 15 | 341px · 40% of screen | **222px · 26%** |

⭐ Verified by serving the page to a real browser and scrolling it, not by arithmetic. The boots and the
wordmark now sit on one screen.

**And 273KB of base64 came out of the HTML** — `376KB → 12KB`. That blob was downloaded before anything
rendered and could be cached by nobody. ⚠️ *An asset inside the document is an asset the browser cannot
skip.* `width`/`height` attributes now reserve its space, so the page no longer jumps as it arrives.

## ⭐⭐ The real finding: nothing could look at this page

It lived only in `~/madboots-site` — one folder, on one machine, not backed up, not reviewable, not
testable. **A broken explainer-video link sat on the live homepage** until the owner happened to click
it, and the only reason it was ever fixed is that he mentioned it in passing.

⚠️⚠️ *A page no test can open is a page whose only reviewer is a visitor.*

So `site/` is now the source, and **`$MADBOOTS_SITE` is a build output** that `release_android.sh`
assembles: the repo's page and images copied in, the generated `app/`, `_headers` and `_redirects` added
beside them.

⚠️ **Copied, not synced.** A `--delete` would remove the APKs the script just spent three minutes
building — ⭐ *the tidiest form of a publish step is the one that deletes your release.*

📌 **Editing `~/madboots-site` by hand now works until the next release overwrites it** — the same trap
the install page already had, one directory up, and the README in `site/` says so.

## The tests that could not exist before

Eight, asserting the things that have actually gone wrong rather than everything that could:

- **the explainer video is the current id** — the one that broke, and it appears **twice**, so the test
  fails if the two spellings disagree (ADR-184's rule)
- **every referenced local file exists** — ⚠️ Cloudflare serves the index for a missing asset rather than
  a 404, so *the failure arrives looking like the homepage*, which is how it hides (ADR-282)
- **the artwork is not upscaled**, and is bounded relative to the viewport on a phone
- **the declared `width`/`height` match the actual PNG header** — ⭐ *numbers that disagree with the file
  reserve the wrong space, which is worse than reserving none*
- **no inlined images**, with a size ceiling on the page
- **iOS is not a link** — *a tap that does nothing reads as broken* (ADR-283)
- **the release script publishes this directory**, or the repo copy is a decoration

7/7 mutations killed. ⭐ A deliberate **no-op control** was included and correctly survived — *a mutation
harness that fails everything proves nothing, and the only way to know is to feed it a change that should
pass.*

## What this does not do

- **The APKs stay out of the repo.** 18MB each, and `site/` would collect them forever.
- **`_headers` and `_redirects` stay generated.** They are derived from the release, not authored.
- **No CI deploy.** The Cloudflare drag is still manual — *and it is still the step that gets skipped*
  (the live build was three releases behind while this was written). That is the next thing worth fixing,
  and it needs an API token rather than a decision.
