# ADR-340 — The phone is the staging environment

*A release reached nine people the moment it existed.*

**Date:** 2026-10-01
**Status:** Accepted
**Re-opens:** ADR-290 (the publish step that kept getting skipped) · **Follows:** ADR-339
**From:** the owner — *"we can get away with using the iPhone as the stage and when tested I can give
you the go ahead to push to web & android"*

---

## Context

Nine releases went out in two days, and two of them were broken in ways thirty seconds of use would
have shown: landscape could not fit the perspective pitch (ADR-332), and an over-budget plan answered
every player tap with a Pydantic payload (ADR-338). A third was not broken at all and cost an
afternoon anyway (ADR-339).

⚠️ **There was no moment between "a build exists" and "nine people have it."** `release_android.sh`
builds the APK **and** publishes the `version.json` that prompts them, in one command.

⭐⭐ **And the staging environment already existed**: `release_ios.sh` installs to one phone with free
provisioning. *A staging environment you already own beats a better one you have to build* — this costs
one environment variable and two scripts, rather than a second API, a second database and a second set
of credentials to keep honest.

## Decision

```
scripts/release_stage.sh     # bump · build · install on the phone. Nothing live.
scripts/release_ship.sh      # publish to the web and the nine testers.
```

`MADBOOTS_STAGE_ONLY=1` makes both publishers do everything except deploy.

🔴 **Both publishers, and that is the whole correctness argument.** Each script deploys the **entire**
`$SITE` folder, so gating only the Android one would mean a later `release_web.sh` published the staged
`version.json` anyway — and the testers would be prompted by a release nobody had decided to make.
⭐ *A gate on one of two doors is a doorway.* A test asserts the gate precedes `wrangler` in both.

⚠️ The closing line of a staged run no longer says *"Testers already have it"*. ⭐ *A closing
instruction that is wrong about what just happened is worse than none*, because it is the sentence
someone acts on.

⚠️ Named `release_*`, not `stage.sh`: **"staging" already means a Supabase project here**
(`run_app_staging.sh`, `docs/SUPABASE_STAGING.md`). That is the *data* layer; this is the *build* layer.

## ⚠️⚠️ This re-introduces the step ADR-290 removed, deliberately

ADR-290 automated publishing because *"a publish step a person has to remember is a publish step that
measures how busy they are"* — the live build once sat **three releases behind** while the release
script was being improved.

That risk is unchanged. The difference is what the step buys: ADR-290's skipped step bought nothing, and
this one stops a broken build reaching nine people. ⭐ *A manual step is worth re-adding exactly when
skipping it is the cheaper mistake* — and here it is, because the cost of not shipping is a delay and
the cost of shipping blind is nine people hitting a wall.

The mitigation is noise, not discipline: `release_stage.sh` ends with a banner saying it is **not live**,
and `release_ship.sh` prints the build number and its release notes **before** deploying, because staging
can run several times and the build on disk is not necessarily the one anyone tested.

## The first run found one thing

⚠️ The phone was off the Wi-Fi. Everything above it had worked — APK built, web built, `version.json`
written locally — and the script exited 1 after a bare *"no iPhone found"*. ⭐ *A script that reports
its last step as its outcome invites you to redo the ones that succeeded*, and redoing this one burns a
build number for nothing. A failed install now says so and names the one command to retry.

⭐ The gate itself was verified live: testers on **39**, staged **40**, and `madboots-40.apk` not
published. ⚠️ Worth knowing for anyone checking by hand — Cloudflare Pages answers a missing file with
**HTTP 200 and the index page**, wearing whatever content-type the name implies, so a status code is not
evidence that something shipped.

## Consequences

**Good:** every one of the last three incidents would have been caught on the phone, free.

**Costs:** ⚠️ a release is two commands with a human in between, and the human is the owner. If builds
start to pile up staged, this ADR was wrong and ADR-290 was right — ⭐ *and the measurement is simply
whether `madboots.com/app/version.json` lags `pubspec.yaml` for days at a time.*

⚠️ **Open:** the gate protects the testers, not the **API**. `src/service/` deploys to Render on push, so
a server-side change is live before anything is staged — which is exactly how ADR-339's confusion
happened, with a new server and an old client. ⭐ A staged build tested against an already-updated API is
testing a combination the testers will never see for the few minutes it differs; worth knowing, not worth
a second API today.

⚠️ **And it changes if iOS goes paid.** With a developer licence the phone stops being special: TestFlight
has its own staged distribution, and this pair would be replaced rather than extended. The owner has
flagged that as a separate decision.
