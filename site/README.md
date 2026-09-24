# The public site

⭐⭐ **The source of truth for `madboots.com`.** It lived only in `~/madboots-site` until ADR-289 — one
folder, on one machine, not backed up and not reviewable. ⚠️ *A broken explainer-video link sat on the
live homepage unnoticed because nothing could look at it*, which is the argument for this directory in
one sentence.

| file | |
|---|---|
| `index.html` | the landing page — **hand-written, edit it here** |
| `boots.png` | the hero artwork, 377×378 |
| `favicon.png`, `og-image.png` | the browser tab and the link preview |

`scripts/release_android.sh` copies these into `$MADBOOTS_SITE` (default `~/madboots-site`) and adds the
**generated** files beside them: `app/index.html`, `app/version.json`, the APKs, `_headers`, `_redirects`.

⚠️ **So `~/madboots-site` is now a build output.** Editing it by hand works until the next release
overwrites it — ⭐ *the same trap the install page had, one directory up.*
