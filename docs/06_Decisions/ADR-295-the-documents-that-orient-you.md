# ADR-295 — The documents that orient you

**Date:** 2026-09-25
**Status:** Accepted
**From:** the owner — *"a quick review of our documentation to make sure that it is up to date"*, and
*"we also have the ML decisions to make post GW8"*

---

## What was stale, and why it mattered more than usual

Four documents still said the mobile app was **next**. It is on Android and iOS, nine testers have it,
and the release publishes itself.

| | said |
|---|---|
| `CLAUDE.md` | *"Next: a Flutter mobile app"* |
| `README.md` ×2 | *"Next: a mobile app"* · under **Planned (not yet built)** |
| `PROJECT_STATUS` → Next Milestone | *"Then Phase 4, the Flutter foundation"* |
| `Roadmap` item 3 | *"The next phase is mobile"* |

And `PROJECT_STATUS`'s **Current Story** — a field whose name promises it is current — was from
**2026-08-24**: 118 ADRs against an actual 295, and GW1 listed as a *future* marker five weeks after it
was played.

⭐⭐ **`CLAUDE.md` is loaded into every session.** For three weeks it told each new one that the project's
next job was the thing the project had already finished. ⚠️ *A document that orients you is the one worst
placed to be out of date* — every other stale file is read by somebody already holding enough context to
notice.

⭐ *A field named "current" is the one nobody re-reads, because its name promises it was.*

## The guard, not just the fix

Five tests over those four files, checking claims **against the repo** rather than against prose:

- **nothing calls the mobile app unbuilt** — and the refutation is derived: if `mobile/lib/main.dart`
  exists, the claim is false. ⭐ *The claim and its contradiction live in the same test, so nobody has to
  remember to come back and delete it.*
- **the live fields are not a season behind** — an ADR count in `Current Story` must be within ten of the
  directory
- **an expired "on or after" date is not still pending** — ⭐ *a date is the only part of a plan that
  expires on its own* (ADR-212)
- **the held ML gate keeps its date, its rule, and its decline branch** — *a gate with one exit is a plan*
- **the four files are tracked**, because `site/index.html` was not and a broken link lived on it for
  weeks (ADR-289)

4/4 mutations killed. ⚠️ The first version banned any line mentioning the old claim, which would have
forbidden the sentences that *explain the drift* — the same trap as ADR-290's token guard, so lines
marked done or quoting the old wording are exempt.

## 📅 The ML decision: nothing to decide yet, and that is the answer

The Phase 1 gate (ADR-204) is **held**, and re-decided once **GW8 is played — on or after 2026-10-26**,
which is a month away. The rule was written before the data existed:

> Ship the blend if, on ≥8 gameweeks: **ρ gain ≥ +1 SE**, *or* **hit@20 gain ≥ +2 SE and ρ does not
> fall**, both holding across ≥2 adjacent values of `k`. ⚠️ `k` re-fitted on the eight gameweeks, not
> carried over. **If neither clause is met, Phase 1 is declined for the season.**

⭐⭐ **Do not re-argue the threshold in October — that is the entire point of having set it in September.**

**What was worth checking now is whether the review can be run at all**, because the failure mode is
arriving on 26 October and discovering the harness has rotted against four weeks of `src/` changes. It
has not: `spikes/204-board-wide-minutes/{blend,blend_on_points,hit_rate_error}.py` all still import and
execute against today's code, checked 2026-09-25. ⭐ *A held decision is only held if the thing that
decides it still runs.*

## What this does not do

- **No sweep of the deep docs.** `Architecture.md` and the sprint records are history and are allowed to
  be; ⭐ *a log that updates itself is not a log.* This is about the four files that claim to be current.
- **It does not stop staleness**, only the four shapes of it that have actually happened here.
