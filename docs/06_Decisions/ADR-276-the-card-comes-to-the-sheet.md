# ADR-276 — The card comes to the sheet

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"on the desktop version you get a mini card, do you think there is enough real
estate to merge these 2 at the bottom of the screen on the app, so you can select the option as well as
having some real stats?"*
**Builds on:** ADR-236 (the player card), ADR-265 (the difficulty scale)

---

## Context

Tapping a player on the pitch gave a name, a one-line subtitle and four buttons — in a panel half of
which was blank. The desktop's mini-card carries his **run** and his **season**.

⭐ **There is room, and the question the sheet answers is incomplete without them.** *"Make captain"* and
*"Transfer…"* are decisions, and the sheet offered no basis for either beyond a single xP figure.

## Decisions

**The run is drawn immediately; the season fills in.**

⚠️ The fixtures are **already on the device** — `MyTeam` carries three per club — while the season stats
are a round trip. ⭐ *Blocking the whole card on the slower half would make the fast half feel slow.*

**Four stats, not nine.** The endpoint returns everything the Players tab shows. ⚠️ *A stat block long
enough to push the actions off-screen has replaced them rather than joined them* — so it is the first
four, which are the desktop card's own: FPL Points, Points/game, Goals, xG Involvement.

**⭐⭐ A failed fetch loses the stats, never the actions.** The reason the sheet exists is the four buttons
below it; a network error must not take them with it. It says *"Season stats did not load"* and the sheet
still works.

**⚠️ Only alongside the actions.** Once the sheet has become a replacement list or a swap picker it is
answering a different question — ⭐ *a stat block under a list of candidates describes the wrong player.*

**The fixture chips reuse the ticker's 1-5 colours** (ADR-265). ⚠️ *A colour that means "hard" on one
screen must not mean anything else on another* (ADR-184).

## Verification

* **5 widget tests** pumping the real sheet against the committed samples — the actions survive, the
  stats arrive, the run shows with its per-gameweek number, and a **500 loses only the stats**.
* **4/4 mutations killed**: all nine stats shown, an error thrown rather than caught, the run suppressed,
  and the card not rendered at all.
* ⚠️ Two mutation patches failed to apply first time because `dart format` had reflowed the lines —
  ⭐ *the fourth harness fault of the week, and the reason every patch asserts its own application.*
* 2,570 Python · 249 Dart.
