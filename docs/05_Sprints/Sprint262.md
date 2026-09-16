# Sprint 262: The observer, in place before the thing it observes

**Dates:** 2026-09-17
**Status:** ✅ Complete — **ADR-203. 1823 → 1832 tests, ruff clean. 7 mutants, 7 red.**

---

## The job

ADR-202 published the minutes baseline the day before with an asterisk it could not remove: the model is
scored with **today's** injury news applied retrospectively to round 1, and that cannot be made walk-forward
because FPL serves availability as a *now* field. **195 of 659 players carry a flag today**, and against a
five-week-old round essentially all of them are wrong in both directions.

⭐ **This is ADR-201 again** — not a rollover, but the same shape: *a field that only ever holds the present,
quietly destroying the past on a schedule.* Left alone, the GW8 review would re-run the baseline and reproduce
the identical asterisk, because nothing in between was recording.

⭐ **The observer has to be in place before the thing it observes.** That is why this came before the Phase 1
gate, which can be run at any time.

---

## Built

A `player_availability` log written on every `refresh`. **A change log, not a poll log** — a row per player
per refresh is ~480k a season and carries nothing extra. Verified against real FPL data: 659 observations on
the first refresh, **0 rows added** on a second eight hours later.

⭐ **But a change log alone cannot tell "unchanged" from "not observed"**, and three silent weeks would look
exactly like three stable ones. So each row is an **interval** — `observed_at` when first seen,
`last_seen_at` when last confirmed — and `availability_as_of(when)` returns both *with* the value, because a
caller that cannot see the staleness will treat a three-week-old status like this morning's.

**`observed_at`, not `changed_at`.** ADR-201 stamps a match with its own kickoff, on the principle that a
record about a point in time takes its timestamp from the event. Availability has no such timestamp — the
flag may have gone up hours before the refresh that saw it. ⭐ **The same principle produces the opposite
column name here**, because it is about what is actually known, not about preferring one clock to another.

---

## ⚠️ What the build got wrong

**The recorder would have crashed the refresh.** A codeless player let a `NOT NULL` violation propagate out of
`save_availability`, out of `refresh`, taking teams, players, fixtures and Elo with it. ⭐ *The failure path of
a side-record must not take down the thing it observes.*

**Found by the test fixture, which is the interesting part.** The shared `bootstrap_static_sample.json` carries
eight keys and no `code` — so it **is** the pathological payload, and four existing ingest tests went red the
moment the writer was wired in.

⚠️ **And that same thinness then made the wiring test vacuous**: *"every player in the payload has an
observation"*, against a payload where no player can be keyed, asserts `0 == 0` and passes whatever the code
does. ⭐ *A fixture that cannot express the field under test turns the guard into decoration.*

⭐ **Testing a component is not testing that anything uses it** — all six writer tests passed with the call
absent from `refresh`.

---

## ⚠️ The mutation sweep that reported nothing and looked like a pass

Seven mutants, seven red — on the second attempt. The first printed every label and **no verdict**, because
the harness ran under **zsh**, which does not word-split unquoted parameter expansions: the two test paths
reached pytest as one impossible argument and no run produced a summary line.

⭐ **A mutation sweep that cannot fail is worth less than no sweep, because it reports confidence.** The only
thing that gave it away was a blank column.

---

## 💡 The lesson

⭐ **A recorder with no reader is worth building when the data is perishable, and only then.** Nothing reads
`availability_as_of` yet; it exists for a review five weeks away. That is normally a smell — but the
alternative is not "build it later", it is "build it later and have nothing to read".

---

## Definition of Done

- ✅ **Tests** — 9 new (6 writer, 3 wiring/robustness); **1832 passed**, ruff clean; 7 mutants, all red
- ✅ **Manual smoke** — real `refresh` against a **copy** of the live DB: 659 observations, 195 flagged
  (matching ADR-202's count exactly), second refresh adds 0 rows and advances `last_seen_at`
- ✅ **Docs** — ADR-203 + index row, Roadmap, PROJECT_STATUS, this sprint doc

**Next:** the Phase 1 gate — a minutes forecaster that is better *board-wide*, which is the test ADR-202's
false negative was meant to be.
