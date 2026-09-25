# ADR-290 — The step that kept getting skipped

**Date:** 2026-09-25
**Status:** Accepted
**From:** the owner — *"lets set up wrangler and automate the deploy"*
**Completes:** ADR-282 (distribution), ADR-289 (the site joins the repo)

---

## The evidence was this project

`scripts/release_android.sh` bumped, built, signed and staged — and then printed *"drag this folder to
Cloudflare Pages."* Cutting a release and shipping it were two actions with a person in between.

⭐⭐ **While that script was being improved, the live build fell three releases behind.** Nine testers
spent an evening on build 6 while 7, 8 and 9 sat finished on a laptop. Nobody forgot; there was simply
always one more thing to do first.

⚠️ *A publish step a person has to remember is a publish step that measures how busy they are.*

## The decision

`npx wrangler pages deploy "$SITE"` at the end of the release, so **cutting a release is shipping it.**

Three things that matter more than the command:

**⚠️ Absent credentials are not an error.** With no token the script still bumps, builds, stages, prints
what it made, and explains how to turn publishing on. ⭐ *A release tool that refuses to run without a
secret is a release tool you stop running* — and the fallback is the drag that was happening anyway.

**⚠️ A failed publish is not a failed release.** The APKs are staged before the upload is attempted, so a
network failure costs the deploy and not the three minutes of building.

**⚠️⚠️ The token is read from the environment and never written.** Not to a file, not to the command
line — where it would sit in shell history and in `ps` for every process on the machine — and never
echoed. The scoped permission is **Cloudflare Pages: Edit** and nothing else: ⭐ *a deploy token that can
also read your DNS is a deploy token whose loss is a different-sized problem.*

## ⭐ The test that nearly forbade its own documentation

The guard began as *"no line may mention `CLOUDFLARE_API_TOKEN` outside the presence check"* — and failed
immediately, on the two lines that **tell the reader what to export**.

⚠️⚠️ *A test that cannot tell `$TOKEN` from the word "TOKEN" forbids the documentation along with the
leak*, and a guard that fires on the prose explaining the guard teaches people to delete the prose
(ADR-261's trap, third appearance). It now matches **expansions**, so the instructions are allowed and
`--api-token="$CLOUDFLARE_API_TOKEN"` is not — a mutation confirmed it catches exactly that.

5/5 mutations killed: publishing removed, the wrong folder deployed, a missing token breaking the
release, the script falling silent about publishing, and the token reaching the command line.

## ⭐ Proven on the first run, and it found two things

Release `1.0.0+10` published itself:

```
  publishing to Cloudflare Pages (project: madboots)…
✨ Success! Uploaded 3 files (6 already uploaded) (7.13 sec)
  ✅ live at https://madboots.com/
```

The project was called `madboots` — the default — so the third variable was never needed. ⭐ *Trying the
default before chasing the name cost one command and would have cost a dashboard visit.*

**The release was correct and its last word was wrong.** It deployed, and then printed *"NEXT: drag
$SITE to Cloudflare Pages"* — ⚠️ *a closing instruction that tells you to do the thing the script just
did is how a reader learns to stop reading them.* It now says what is actually left, and still gives the
manual fallback to anyone without a token.

**And the security guard failed on safe code.** Adding that second branch meant a second
`${CLOUDFLARE_API_TOKEN:-}`, and the test asserted there was exactly **one**. ⭐⭐ *A security test that
counts occurrences instead of judging them fails on growth and gets loosened by whoever is in a hurry* —
exactly the wrong moment to be editing a guard about secrets. It checks that **every** expansion is the
presence-check form now, which is the rule it always meant, and re-killing the command-line-leak mutation
confirmed it still bites.

## What this does not do

- **No CI deploy.** This runs on the machine that builds the APK, because that is where the APK is.
  Moving it to Actions would mean putting the **signing keystore** in a secret, which is a much larger
  decision than a deploy token (ADR-278).
- **No rollback.** Cloudflare keeps previous deployments and can promote one; that is a dashboard action
  and does not need scripting until it has been needed once.
- **It does not deploy the API.** Render does that from the push, and ⚠️ *ten of twelve of those pushes
  had no reason to* — the build filter in ADR-288 is still open.
