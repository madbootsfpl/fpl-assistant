# ADR-273 — A conditional gain stated unconditionally

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"Leno to Tzolakis won't provide a +2.2 xP as I will be playing Pickford — this has
come up before"*
**Fixes the presentation of:** ADR-046 (XI-gain ranking)

---

## Context

He is right, **and so is the number.** They answer different questions.

| | |
|---|---|
| Pickford (starts) | 4.2 xP |
| Leno (bench) | 3.5 xP |
| Tzolakis (incoming) | **6.4 xP** |

`xi_aware` ranks by the **best legal XI** before and after (ADR-046), and the best XI after this transfer
starts **Tzolakis over Pickford**: 6.4 − 4.2 = **+2.2**. Real — *if you also change your keeper.* Keep
Pickford and the move is worth **nothing this week**.

⭐ **A conditional gain stated unconditionally is not a number, it is a promise.** The move is not wrong
and must not be dropped — it is the most valuable thing that money can do. It simply comes with a second
step, and nothing said so.

## ⚠️ And the existing note was a guess that was wrong here

The screen already warned on a benched outgoing player: *"this changes the XI only if someone ahead of him
misses."* **False in this case** — Tzolakis is better than Pickford, so he would start.

⭐ *A hedge in place of a calculation is not caution; it is a different wrong answer.* Replaced with the
computed fact.

## Decision

Each move carries **`displaces`** — who stops starting because of it — and the app says:

> *Worth +2.2 only if you also start Tzolakis ahead of Pickford. Keep Pickford and this move gains you
> nothing this week.*

⚠️ **The outgoing player is excluded from that calculation.** He leaves the squad, so of course he stops
starting; ⭐ *naming him as "displaced" would describe the transfer itself as a consequence of the
transfer.*

### ⚠️⚠️ There is no "does he start?" flag, and a mutation run settled that

One was written. Setting it to a constant `True` **broke nothing** — and it cannot be anything else: if
the incoming player were not in the after-XI, that XI would be drawn entirely from the other fourteen, a
subset of the squad the before-XI was already optimal over, so it could not beat it and the gain could not
be positive.

⭐ **A field that is provably constant is not information, it is a place for a reader to look for one.**

### ⚠️ A hidden dependency this exposed

`best_legal_xi` sorts its output on `total_points`, so a row without one raises. Real rows always carry
it; **hand-built fixtures do not**, and twelve tests went red the moment this function was added. ⭐ *A
helper that works on production rows but not on the rows its own tests use has a hidden dependency.*
Defaulted locally, since the field is only a display tie-break here.

## Also in this round

**Nine More-tab descriptions cut to two lines**, so every option fits without scrolling.

⚠️ **The obvious test for that does not work.** Laying the text out and counting lines is the right idea,
and in `flutter test` the default font is a placeholder where every glyph is a **full em wide** — 301px
fits **26** characters instead of the ~55 a real font gives, so it failed strings that sit comfortably on
two lines on the phone. ⭐ *A line count measured in a widget test is a line count for a font nobody has.*
A calibrated character budget instead, with no padding — *a budget padded "just in case" permits the thing
it was set to prevent.*

**The Trending headings were asked for again, and they were already there.** ⭐ *"I built it" is not
evidence that it draws* — so there is now a widget test that pumps the real board against the real sample
and finds all three headings, each above its own rows. They live on the **Worth noticing** pill, not the
default *Worth a look* one.

## Verification

* **4 Python tests**, **4/4 mutations killed** — ⚠️ one survived and proved the flag above was dead, so
  it was deleted rather than tested around.
* **3 widget tests** proving the Trending headings render, and one measuring the More descriptions.
* 2,566 Python · 238 Dart.
