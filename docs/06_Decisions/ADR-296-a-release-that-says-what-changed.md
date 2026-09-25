# ADR-296 — A release that says what changed

**Date:** 2026-09-25
**Status:** Accepted
**From:** the owner — *"add the notes field to the update banner"*, after declining a docs-only release
**Completes:** ADR-282, which shipped `"notes": ""` and nothing that filled it

---

## The field existed and was always empty

ADR-282 put `notes` in the manifest and never produced one. ⚠️ *A release note nobody is prompted for is
a release note nobody writes* — the same argument that moved the publish step into the script (ADR-290).

So the notes come from **the commits since the last release**: `feat:` and `fix:` subjects, with the
`(ADR-nnn)` stripped, capped at three. `MADBOOTS_NOTES` overrides them when a release deserves words
chosen on purpose.

The banner goes from *"there is an update"* to:

> **Build 99 is out — yours is 12.** Tap to update; what you are about to report may already be fixed.
> · In landscape the bench sits beside the pitch
> · A plan that contradicted itself, and could not be cleared
> · The player card shows every fixture's xP

⭐ *"There is a new build" is a chore; "the landscape pitch is fixed" is a reason.*

## The decisions inside it

**Only what a reader could notice.** `docs:`, `test:`, `chore:` and `refactor:` are filtered out — ⚠️ *a
note about work nobody can observe teaches people to skip the notes.* Tested by exercising the filter on
real subjects, not by grepping the script: the first version of that test asserted `"^chore"` was absent
and failed on `--grep=^chore: release`, which **finds the range** rather than letting chore commits
through. ⭐ *A test that reads the code instead of running it will believe whatever the code says about
itself.*

**The ADR number never reaches the reader.** `feat(ADR-293):` is how this project talks to itself; ⭐ *a
tester reading "ADR-293" learns the note was not written for them*, and stops reading the next one.

**Empty is the normal case and must read as one.** Today's HEAD is docs and tests since the last
release, and the honest note for that is none — ⚠️ *a script that insists on filling this field will
produce "various fixes" forever, which is worse than silence because it looks like information.*

**A bare string is still accepted.** Manifests already published carry `"notes": ""`, and ⭐ *a reader
that only understands the new format makes every older release unreadable* — which is the opposite of
what a version check is for.

## ⭐⭐ The cap was in three places, and two mutations proved it

The limit of three lived in the model, in the generator's two branches, and in the banner's `take(3)`.
Removing any one left the other tests passing:

```
SURVIVED   the banner grows without limit
SURVIVED   the derived notes are uncapped
```

⚠️⚠️ *A cap enforced in several places is a cap that moves* — which is a sentence I had already written
into one of these tests while leaving the condition it describes in place. It is now **one** cap per
side of the wire: `kMaxNotes` decides what is rendered, `MAX_NOTES` decides what is published, and each
is covered by a test that fails when it moves.

6/6 mutations killed after the consolidation.

## What this does not do

- **No changelog screen.** Three lines in a banner, then the install page. ⭐ *A notice that grows with
  the work is a notice that stops being read on the busiest week.*
- **It does not make a docs-only release worth cutting.** The generator returns `[]` for the current
  HEAD, which is the same answer as declining it by hand — now computed rather than argued.
