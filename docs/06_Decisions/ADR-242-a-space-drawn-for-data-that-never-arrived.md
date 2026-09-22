# ADR-242 — A space drawn for data that never arrived

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback on the phone build — items 1, 2 and 5
**Builds on:** ADR-235 (one card, three readings), ADR-237 (the expanding row)

---

## Context

Six things off one list. Three were copy and layout; three were the same bug in different clothes —
**the client drew a space and the server never sent anything to put in it.**

## Decision

### 1. ⭐⭐⭐ The run card had three columns and one number

ADR-235's premise is *one fetch, three readings*. The third reading shipped without its data: `by_gameweek`
follows the request's `horizon`, and the horizon is **1**, because the headline beside it is a *this-week*
projection. So the run drew **three fixture columns and had one week of expected points**. Two of them read
`—` on every card, on every squad, from the day it shipped.

⚠️ *A field that is absent renders as a dash, and a dash reads as "no data for this player" rather than as
"this endpoint was never asked for it".* Nobody reported it as a bug for a month because it looked like
missing data about the football.

**Fixed with a second analysis pass, not by raising the horizon.** Raising it changes the headline: the
owner's `projected_xp` goes **44.9 → 133.9** — a three-week total wearing a one-week label. ⭐ *A fix that
corrupts the number beside it is not a fix.* The pass is skipped when the caller already asked for a wide
enough window; `my-team` grows 9.3 KB → 10.1 KB.

⭐ The card is now handed the **map**, not the player, so it cannot silently read the wrong window again.

### 2. The last five did not say who they were against

⭐ The data was already in the row — `player_history` has stored `opponent_team` and `was_home` since
ADR-201. ⚠️ **Two blanks against City and Arsenal say something completely different from two blanks
against the bottom two**, and the column that made them different was being dropped on the way out.

⚠️ `opponent` is **null, never a guess**: an away trip to `???` is worse than one to nothing. Home and away
travel as a separate boolean rather than folded into the name — *a prettified `"vs ARS (H)"` would be a
layout decision taken in the API.*

### 3. Confidence, Edge and Risk are three cards

The owner: *"captain is good, rest are not aligned with style card."* `_Card` puts its label **top-left**
inside an all-round border; the confidence block put `CONFIDENCE` **top-right** with a left bar, and held
Edge and Risk as sub-sections. So the first card on the screen was the one card that read differently from
every other — ⚠️ *a layout that is unique for no reason reads as a mistake, whatever it looks like on its
own.* They are three different questions (*how sure? · what is going for you? · what could go wrong?*)
sharing one box.

The coloured left bar stays: it encodes the band, which is a reason.

### 4. Smaller banner, and "Transfer" rather than "Replace him"

The draft banner keeps its colour — that is what makes it unmissable — and loses a line and some height.
⚠️ *The colour was doing the work; the height was only making it loud.* **"Replace him…"** described the
mechanic; **"Transfer…"** is the word FPL uses, and an app that renames a manager's moves makes him
translate.

### 5. A "My squad" filter

481 players, fifteen of which a manager keeps coming back to. ⚠️ Disabled rather than hidden when there is
no squad — *a chip that vanishes looks like a bug; one that is visibly unavailable looks like a state.*

## What building it found

⚠️⚠️ **`dart format` and the brand generator were fighting over one file, with no stable state.**
`lib/brand.dart` is generated from `brand.py` and compared byte-for-byte by `tests/test_brand_dart.py`.
Formatting rewrapped its long strings and failed the test; regenerating unwrapped them and the formatter
rewrapped them again. ⭐ **The visible symptom was a test failing for a file nobody had edited** — the kind
of failure people learn to re-run past.

Fixed with a `// dart format off` marker emitted by the generator. ⚠️ Two false starts worth recording:
`formatter: exclude:` in `analysis_options.yaml` **does not cover `dart format lib/`** with an explicit
path, and the marker is recognised **only verbatim** — a trailing comment on the same line disables it
silently. There is now a test for the marker's exact form.

⚠️ **A mutation survived that mattered**: making `my_team` reuse the narrow answer — *precisely the shipped
behaviour before this change* — left every test green, because they all exercised `analysis` rather than the
composition that drew the card. ⭐ *A test one layer away from the defect passes through it.*

## Verification

* **9 Python tests** on the run window and the opponents, including one asserting `my_team`'s composition
  directly, and one pinning the headline to a single week so the second pass cannot be "simplified" away.
* **7 mutations killed**: the opponent dropped; an unknown club guessed at; home/away collapsed; the run
  reusing the narrow answer; a wasteful second pass; the bench left without a run; and both forms of
  breaking the `dart format off` marker.
