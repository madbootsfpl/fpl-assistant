# ADR-362 — Three notes from the phone

**Date:** 2026-10-18
**Status:** Accepted
**From:** the owner, on build 46 — *"that said looks really well"*
**Extends:** ADR-360, ADR-361

---

## 1. 🔴 The purple dot was missing on the week being played

The dot marking one of your own was derived from `yours` — and `yours` is built from `player_history`,
which the backfill does not reach until a gameweek is complete (ADR-361). ⭐⭐ *So the dot marked the
**data source**, not the squad*, and vanished for exactly the week it was most wanted.

**The squad travels in its own right now**: the answer carries `squad`, the ids that were actually in the
team that week.

⚠️⚠️ **Not the caller's list echoed back.** For a settled week it is FPL's own answer (ADR-350), and with
no manager id it is **empty** rather than today's squad — *a dot on the wrong player is a wrong
attribution wearing a confident colour*, which is the bug ADR-350 exists to record.

## 2. Cards sat in one run, and the scoreline above them does not

Every booking in a single wrap, so the reader matched each name to a club from memory. ⭐ Now split home
and away, in the two columns the scoreline and the scorers already use — *the work the card exists to
save.*

## 3. The bonus race had a number with no name

> *"dont know what the Bonus Race scores on the right hand mean, eg Neto 64?"*

It is **BPS** — the score that decides the 3/2/1. ⭐ *A number with no unit is a number the reader has to
guess at*, and BPS is not something anyone should be expected to infer. The column is labelled.

## 🔴 And two more tests that proved nothing

**The cards test checked a shape, not a result.** It looked for a `Wrap` inside a `Row` — which is just as
true when **every card appears in both columns**. ⭐⭐ *A layout assertion that cannot tell right from
doubled.* Each booking belongs to one side, so the chips are counted against the cards now.

📌 That is the fourth test in two days that passed for the wrong reason: the allow-list test that held
with the allow-list deleted, the horizon test whose button was disabled for the wrong reason, the live
fallback masked by an ordinary fetch, and this. ⭐ *Every one was found by a mutant and none by review.*

## Consequences

✅ Three mutants, each caught — after the cards one survived and sent the test back.

📌 `yours` still waits for the backfill, deliberately: the live payload carries BPS and bonus but no
`total_points`, and a total this app computed would eventually disagree with FPL's (ADR-346). The dot no
longer waits with it, which was the whole of this fix.
