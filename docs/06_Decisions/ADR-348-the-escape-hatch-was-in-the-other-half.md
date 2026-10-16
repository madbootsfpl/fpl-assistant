# ADR-348 — The escape hatch was in the other half

**Date:** 2026-10-16
**Status:** Accepted
**Found by:** shipping build 44 with release notes that described iterations nobody had seen
**Revises:** ADR-296 (the notes), ADR-328 (the trailers), ADR-340 (the staging gate)

---

## What happened

Build 44 went to nine testers with three bullets:

> · Scores now links to the club's own highlights when they have posted them
> · *Scores is tidier — one line per club, your players named once, and the points each match was worth*
> · *Scores now shows each match with the clubs, the score and your own players on their own side*

The first is true. ⚠️ **The other two describe builds that never left this machine.** Testers went from
40 straight to 44, so *"tidier"* implies they had an untidy version and *"on their own side"* describes a
layout replaced before anyone received it.

⭐ The notes were right as **commit trailers** — each described a real change at the moment it was made.
They are wrong as **release notes**, because a release is a diff between two things a reader has held, and
four staged builds collapse into one of those.

## 🔴 And the documented remedy did not work

ADR-328 records that `MADBOOTS_NOTES` *"still overrides everything, unchanged"*. It was set on the ship
command and **nothing happened**, because the notes are written into `version.json` at **stage** time by
`release_android.sh`. `release_ship.sh` only publishes the folder staging left behind.

⭐⭐ **ADR-340 split one command into two and the escape hatch stayed with the half that builds** — not the
half you reach for the moment you read the bullets and find them wrong, which is the only moment anybody
wants it. ⚠️ *A split that moves a step also moves every lever attached to it, and the documentation
describing the lever does not notice.*

## Decision

**`release_ship.sh` honours `MADBOOTS_NOTES` too.** It rewrites the staged manifest's `notes` and nothing
else — ⚠️ *a manifest whose `url` no longer matches its `build` prompts nine people to download a file
that is not there.*

Three tests, each mutation-checked: the override reaches the publishing command, an ordinary ship leaves
the staged notes untouched, and an override never disturbs the build it is shipping.

## ⭐ The judgement this does not automate, and should not

A release note is written for *"what changed since the last build you had"*, and only a person knows which
build that was. ⚠️ **The generator cannot know**, because it reads commits and commits do not record who
received what. 📌 So the rule is a habit rather than a check: **before shipping, read the bullets as a
tester who last saw the previous release** — and when several staged builds collapse into one, expect to
replace them.

⭐ The cost of getting it wrong is small and real: nine people were told the app got tidier, which only
makes sense if they had seen it untidy.

## Consequences

✅ Build 44's notes were corrected and republished in place — same build, same APK, two true lines instead
of three half-true ones. ⚠️ Anyone already prompted saw the first version; a manifest cannot reach back.
