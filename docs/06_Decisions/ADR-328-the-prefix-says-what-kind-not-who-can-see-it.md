# ADR-328 — The prefix says what kind of change it is, not who can see it

*Build 31 told nine testers about a docs test and a requirements file.*

**Date:** 2026-09-29
**Status:** Accepted
**Amends:** ADR-296 (release notes write themselves)
**From:** the owner, on the update banner — *"what does the messaging on the Build notice mean?"*

---

## Context

ADR-296 made the update banner's bullets generate themselves, for a good reason that has not changed:
*a release note nobody is prompted for is a release note nobody writes.* It took every `feat:` / `fix:`
commit subject since the last release, and its own comment stated the rule it was going for:

> ⭐ Only what a reader of the app would notice. `docs:`, `test:` and `chore:` changed nothing they can
> see, and *a note about work nobody can observe teaches people to skip the notes.*

Build 31 shipped these three bullets to nine phones:

| The bullet | What it actually was | Visible to a tester? |
|---|---|---|
| *"A free transfer for a gameweek FPL does not pay one for, and four cards with one body"* | the bug they reported (ADR-327) | **yes** |
| *"Scope the staleness exemption to the clause it excuses"* | a fix to a **documentation test** | no |
| *"Pin the deploy requirements, including the file Render actually installs"* | versions in `requirements-api.txt` | no |

⚠️⚠️ **The comment was right and the regex under it could not keep the promise.** `fix:` is carried by a
fix to the pitch and by a fix to a test guard alike — ⭐⭐ *the prefix says what kind of change it is,
never who can see it.* So the rule produced precisely the thing its own comment warned against, and did
it for two bullets out of three.

⚠️ There is a second fault underneath, and the one real bullet shows it: *"four cards with one body"* is a
**commit subject**. It was written for someone reading a git log with the diff to hand. A tester reads it
as a riddle and has no way to know it describes their own screenshot.

🔴 **And a third, which I introduced yesterday.** The range anchors on the last release commit, found by
`--grep=^chore: release`. Build 31's release commit reads `release: 1.0.0+31`, so nothing matched it: the
next release would have anchored on build 30 again and re-reported a week-old list. ⭐ *An anchor that
matches one spelling of a convention is an anchor that moves the first time someone types it
differently.*

## Decision

### The note is opt-in, and written in the reader's voice

A change a tester can see carries a git trailer:

```
fix: a free transfer for a gameweek FPL does not pay one for

Release-note: The transfer count now matches FPL
```

The generator reads `Release-note:` trailers and nothing else. ⭐⭐ **This moves the judgement to the only
person who has it** — whoever made the change knows whether it is visible, and can say so in the words a
tester will read. The old rule tried to infer both from a prefix and could infer neither.

⚠️ **Absence is meaningful.** A release with nothing observable gets no bullets, and the script says so
on stderr rather than inventing three:

```
⚠️  no Release-note: trailers since the last release — the update banner will have no
    bullets. If this release changes something a tester can SEE, either add a trailer
    to the commit or re-run with MADBOOTS_NOTES="..." (one note per line).
```

⭐ *A script that insists on filling this field will produce "various fixes" forever, which is worse than
silence because it looks like information.* That sentence was already in ADR-296's tests; it now describes
the common case rather than an edge one.

`MADBOOTS_NOTES` still overrides everything, unchanged.

### The anchor accepts both spellings

`--grep=^chore: release --grep=^release: -E`, so the convention slipping does not silently re-report a
week-old list.

### Build 31's live manifest was rewritten

The APK, its build number and its URL are untouched; only `notes` changed, because that is the only part
a tester had reason to complain about:

* The transfer count now matches FPL
* Each suggested transfer explains its own move

⭐ *The banner is the only thing a tester reads before deciding whether to update* — leaving it saying
"scope the staleness exemption" until the next release would have cost two weeks of that banner being
worth ignoring.

## Verified

`tests/test_release_notes.py` runs the **real generator over a throwaway repo** rather than reading the
script — ⭐ *a test that reads the code instead of running it will believe whatever the code says about
itself*, which is how the old subject filter passed while shipping three unusable notes. Nine tests,
covering: a trailer becomes a note · a `fix:` with no trailer reaches nobody (the exact three subjects
from build 31) · an ADR number cannot leak into a bullet · the anchor restarts at either spelling · an
empty release stays empty · the override still wins and is still capped.

## Consequences

**Good:** bullets are written by the person who knows, for the person who reads them. Two of build 31's
three were noise, and that class of noise is now impossible rather than discouraged.

**Costs:** ⚠️ a note is now something someone must remember to write, which is exactly the failure mode
ADR-296 existed to remove. The stderr warning is the whole mitigation, and it is weaker than a rule that
needs nobody. ⭐ *This trade is deliberate: a bullet nobody can act on is worse than a missing one*, but
the next release that ships a visible change with no trailer will prove whether the warning is loud
enough.

**Open:** nothing stops a release with no notes from still prompting an update. That is probably right —
a build number moves for reasons a tester cannot see — but it has never been decided on purpose.
