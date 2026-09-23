# ADR-266 — Trending returns as a tab, not as the screen that was removed

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"Signals: Add in the Trending Tab here, alongside My squad [and] The Market tabs"*
**Revisits:** ADR-245 (which removed the Trending page), ADR-150 (the evidence tiers)

---

## ⚠️ This looks like undoing ADR-245, and it is not

ADR-245 deleted the standalone Trending page and folded it into the Signals market scope, on the grounds
that *"what is notable?"* was being asked twice. **That was right and it stands.**

⭐⭐ **What comes back is the other question.** The market scope answers *"what is notable?"* and orders by
**how strong the evidence is** (ADR-150: FPL's own news first, crowd behaviour **last**). A trending board
answers *"who is top of the charts?"* and orders by **how many managers moved**.

⚠️ *Same data, genuinely different ordering — which is why one cannot serve the other.* Forcing both
through one list would mean picking an ordering and misrepresenting whichever question did not get it.

## Decisions

**`POST /api/v1/trending`** — four boards: **most bought · most sold · most owned · in form**.

**⚠️⚠️ The caveat travels with the numbers.** This is the weakest evidence the app carries, and ADR-150
puts it last on purpose: ⭐ *"lots of people did this" is a fact about other managers, not about the
player* — the reason a template forms, and not on its own a reason to join one. The warning is **in the
response**, not written into each client, because *a caveat that lives apart from its numbers drifts from
them*.

**⭐ Ownership rides on every board**, whichever one you are looking at — *"661k bought him" means
something different at 4% than at 40%*, so the number that makes the others readable is always present.

**⚠️ `player_ids` flags rows; it never narrows the board.** ADR-245's arrangement: the ids are sent so a
row can come back marked *yours*, and the client never matches ids itself. One of yours is **outlined**
rather than badged — the charts read differently when you are already in the trade.

**⚠️ One `value` field, four quantities** — so each board names its own `column` (`Net in`, `Own%`,
`Form`). ⭐ *A number with no unit is not information.* Net transfers are **people**, so `660754` renders
as `661k`: a raw six-digit count is a number you have to parse before you can compare two of them, and a
sale keeps its minus sign, which is its whole meaning.

**⚠️ Picking the tab must not refetch signals** — `scope` accepts only `squad`/`global`, so asking would
fetch a **422** nothing reads.

## ⚠️ Two guards fired, and a mutation harness lied

The **shape sweep** demanded registration — correctly, and *in the sweep proper rather than `NO_PLAYERS`*:
a board carries a player summary per row, which is exactly the shape a raw 45-column database row leaks
through. The **contract test** demanded a committed sample.

⚠️⚠️ **And a mutation reported SURVIVED without having been applied.** The patched line —
`photo: json['photo'] ...` — appears **four times** in the models file, and the harness replaced the first
occurrence, in an unrelated model. ⭐ *A mutation harness that patches the wrong place reports fiction*,
which is the **second** harness fault of this species today (ADR-263's was `git checkout` on an untracked
file). Re-run against the right model, the test killed it.

## Verification

* **13 Python tests** — every board ranked by its own number (⚠️ including that *most-sold* runs from the
  biggest sell downward, since the sort is by magnitude while the display keeps its sign), the caveat
  present, flagging that does not narrow, ownership and a photo on every row.
* **11 Dart tests** against the committed sample; **5/5 mutations killed**, one only after the harness was
  corrected.
* 2,520 Python · 168 Dart.
