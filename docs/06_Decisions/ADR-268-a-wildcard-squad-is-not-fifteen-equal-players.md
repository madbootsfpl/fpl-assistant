# ADR-268 — A wildcard squad is not fifteen equal players

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"Could we add in 'Lab' into the More tab too… will need all 3, however to get
feedback lets start with the Wildcard."*
**Builds on:** ADR-013/043 (the solver), ADR-045 (bench-aware), ADR-227 (one player shape)

---

## Context

The solver has answered *"the best fifteen within a budget"* since ADR-013. ⭐⭐ **On its own that is a
list of fifteen names you then have to diff against your own team in your head** — ⚠️ *the comparison is
the product; the squad is the input to it.*

## ⚠️⚠️ The defect building it found

`POST /squad/build` never asked for a bench, so **the solver treated all fifteen as if they play.** ADR-045
added bench-awareness in 2025 and this endpoint never used it.

⭐ **A squad optimised as fifteen equal players is not a squad anybody fields** — it spends real money on a
bench that scores nothing.

**Measured, not argued.** Against the same £100m and horizon:

| | all fifteen | the eleven |
|---|---|---|
| flat build | **423.0** | *best possible* **325.1** |
| bench-aware | 407.4 | **329.1** |

⭐⭐ The bench-aware eleven beats the flat build's **best eleven ignoring shape** — an *upper bound* on any
legal XI it could field. So the flat build could not field as good a side however it lined up, while
**scoring higher on the headline number.**

### So the headline had to change too

`projected_xp` sums all fifteen. ⚠️ A bench-aware draft therefore reads **worse** on it while fielding a
**better** side — ⭐ *a headline that falls when the answer improves is a headline that will be optimised
against.* A new `xi_xp` names what the manager actually scores; `projected_xp` keeps its old meaning,
because ⚠️ *changing what a field means is worse than adding one.*

`bench_weight` is a **request field with no default**, so existing callers are not changed underneath them.

## The Lab

**⭐ The diff is the feature.** Who goes, who arrives, and what it costs — not a fifteen to read.

**⚠️ Kept players are marked `kept`.** *A draft that cannot tell you which players you chose yourself
invites you to trust a choice you made.*

**⚠️⚠️ The budget is FPL's team value, and the screen says so.** It already includes the bank, and it is
built from **selling** prices — ⭐ *a budget built by adding up current prices would be optimistic by
exactly the amount a manager has earned*, which is the direction that invents money. Said out loud,
because *an unexplained number that disagrees with another number on the same app is a bug report.*

**⚠️ "Infeasible" is an answer, not an empty squad** — *rendering fifteen blank rows under a heading is how
"your constraints cannot be met" gets read as "there are no good players".*

**⭐ Nothing here changes anything.** FPL has no write API, so this is a scratchpad — *an experiment you
cannot accidentally execute is one you can run freely.*

📌 **Wildcard only, by the owner's call.** Free Hit and a fresh-season build are the **same solver with
different defaults** (horizon 1; £100.0m from nothing), which is why `LabMode` exists now rather than
later: ⚠️ *a second mode bolted onto a screen built for one is how a screen ends up with two of
everything.*

## Verification

* **8 Python tests**, including the measured comparison above rather than an assertion that it *should* be
  better. **3/3 mutations killed.**
* **12 Dart tests**; **5/5 mutations killed** — ⚠️ two only after the harness was corrected, because
  `dart format` had reflowed the lines the patches matched on. *Third harness fault of the day.*
* ⭐ The committed sample is now generated **with** `bench_weight`, because *the shape a client has to
  render was absent from the only example it had.*
* 2,547 Python · 196 Dart.
