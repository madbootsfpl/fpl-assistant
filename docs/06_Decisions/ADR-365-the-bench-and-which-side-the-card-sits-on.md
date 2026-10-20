# ADR-365 — The bench, and which side the card sits on

**Date:** 2026-10-20
**Status:** Accepted
**From:** the owner, on build 49 — and the confirmation that ADR-363's lifecycle ran end to end:
*"it did, now this morning provisional is gone as expected."*

---

## 1. 🔴 Benched players' points were printed as though they counted

**YOUR PLAYERS** listed all fifteen alike. A benched man's points do not count, and the card said nothing.

⭐ **Picks are public once the deadline passes**, not only once the week is over — so a week in play has
them too, and with them the one thing a flat list of ids cannot carry.

### ⚠️⚠️ `multiplier`, never `position` — and my first reason for that was wrong

I wrote that `multiplier` is authoritative *"after automatic substitutions"*. 🔴 **A mutation reading
`position > 11` survived every test in the file**, because on an autosub FPL **swaps the positions**: the
man brought on reads `position 5, multiplier 1` and the one he replaced `13, 0`. The two fields agree and
neither can be told from the other.

⭐⭐ They diverge under **Bench Boost**, where all fifteen play: the bench keeps positions 12–15 and gains
`multiplier 1`. Reading the position there benches four men whose points counted. *That* is the reason,
and there is a test for it now.

📌 `None` where there are no picks to read — ⚠️ *unknown and "nobody was benched" are different facts*, and
an empty set quietly asserts the second.

## 2. The home side's cards read inside-out

Every chip drew its card **before** the name, while the scorers and assists above mirror outward from the
centre. ⭐ The owner: *"this would align with scorers and assists and make reading a little easier."*
Home now reads *name then card*, away *card then name*.

## Consequences

✅ Four mutants, each caught — after the first survived and sent the **rationale**, not just the test,
back for correction.

⭐ The match total excludes benched points. ⚠️ *A sum that includes them disagrees with the one FPL
shows* — ADR-346's rule, pointing the other way.

🔴 **Two tests asserted things the sample could not show.** One totalled a squad that happened to be
entirely on the bench, so *"1 pt"* was never going to appear; the other looked for a mirrored pair of
cards in a match whose bookings were **both on the home side**, and whose away club had nobody in the
`people` sidecar at all. ⭐ *A test that cannot fail for the reason it names is not testing that reason* —
both construct their scenario now.
