# ADR-247 — A club is half of what a player is worth

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback — *"DNA could be a section in More"*
**Builds on:** ADR-118 (DNA, the eight axes), ADR-127 (percentile ranking), ADR-238 (More as a directory)

---

## Context

The owner asked for DNA in More. The engine has two of them, and they answer different questions.

⭐⭐ **Player DNA answers *what kind of player is he?* — which the app already answers twice**, on the
expanding card (ADR-237) and in Boot Battle (ADR-236). **Team DNA answers *is this attack actually any
good?***, which is what decides between two players from different sides, and the app could not answer it
at all.

So: Team DNA. Player DNA stays on the web for now, and 📌 the card is the obvious home for it later.

## Decision

**`POST /api/v1/team-dna`** — all twenty clubs, eight axes each, best first, with a grade and the
insights the web already renders.

⭐ **Every axis is a percentile**, so `74` means the same thing on Attacking Threat as on Squad Depth.
That is what lets eight different units share one scale.

### ⭐⭐ Bars, where the web draws a radar

A radar needs width a phone does not have; eight labels around a circle on a 390pt screen are unreadable.
The numbers are identical and the shape is the one that survives the screen. ⚠️ *Porting a layout is not
the same as porting a view.*

### The squad marks, and filters nothing

`player_ids` tags the clubs you hold players from. ⚠️⚠️ **It narrows nothing**, and a "Mine" toggle on the
screen is off by default. ⭐ *A league table you can see yourself in is a different object from a league
table of the clubs you already own* — and a request that quietly narrowed would make the grades
meaningless, because they are ranks across all twenty.

### The grade is a letter

A+ → D, not a number a manager would have to learn a scale for. The 0–100 it came from travels too, for
the sort.

## What building it found

⚠️⚠️ **Two mutations survived by being no-ops**, and measuring said why: today's board has **zero null
percentiles and zero tied scores**. Turning an unranked axis into a `0`, and dropping the tie-break, both
changed nothing observable. ⭐ *A mutation that survives because the data has no instance of the thing under
test says nothing about the test.* Both branches are now constructed.

⭐ **The tie-break one is subtle**: the first test compared two runs of the same query, and Python's sort is
stable, so it agreed with itself no matter what. ⚠️ *Stability is not determinism when the input can be
reordered* — a schema change, a different index, another data source. The test shuffles the arrival order
now.

⭐⭐ **`test_player_shape.py` caught the new endpoint before I did.** It fails when a public service
function is not exercised by the shape sweep, and it named `team_dna` on the first full run. It is
registered in `NO_PLAYERS` with a reason — ⚠️ *"nothing to check here" has to be written down, or the next
reader cannot tell it from "nobody checked".*

## Consequences

⚠️ **This is the app's first pure exploration surface.** The audit put those on the web, and ADR-238's More
copy said so in as many words — that paragraph has been corrected, because ⭐ *positioning copy that
outlives the positioning is worse than none: it teaches a reader something the app then contradicts.*
📌 Worth watching whether it pulls the phone the wrong way.

## Verification

* **9 tests**: the full league ranked, best-first and stable, percentiles in range, the squad marking
  without filtering, grades from the fixed set, insights using the web's own four kinds, the payload
  measured, and the two constructed branches above.
* **5/5 mutations killed** once those branches were reachable: the squad filtering instead of marking;
  nothing marked; an unstable tie-break; the table sorted backwards; and an unranked axis rendered as
  worst-in-league.
