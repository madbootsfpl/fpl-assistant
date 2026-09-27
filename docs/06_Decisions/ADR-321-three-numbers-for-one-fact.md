# ADR-321 — Three numbers for one fact

**Date:** 2026-09-27
**Status:** ✅ **Built.**
**From:** the owner — *"We have calculated that we have 2 transfers for next week left, per the Timing
section in 'This Week', on our landing page we have 1 Transfer (is that 1/3 used??) and we input that we
have 1 in settings."*

---

## The decision

**The server works the number out and says where it came from. The manager can override it, and the
override now survives the app closing.**

## What was actually wrong — three things, and the report named the smallest one

The three numbers were **arithmetically consistent**: Settings held 1, the pitch echoed that 1, and Timing
said *"next week you would have two"* because banking this week's transfer accrues another. Nothing was
miscalculated. ⭐⭐ *But a reader cannot check consistency he cannot see the basis for* — and the
parenthesis is the real report.

### 1 — The pitch stat had no direction on it

It rendered a bare `1` under the word **Transfers**. *"One available"* and *"one of three used"* are
equally good readings of that, and the owner said so. 🔴 **The comment directly above the line claimed it
showed `n free`** — it never had:

```dart
// ⭐ Shown as "n free" because the number is one the manager set …
_Stat(value: '${team.freeTransfers}', label: 'Transfers'),
```

⚠️⚠️ *A comment describing an intent the code does not carry out is worse than no comment, because it
stops the next person re-reading the line.* It stopped me, twice, in the two sessions before this one.

### 2 — The app already knew the answer and asked anyway

ADR-318 made the number **derivable** from the manager's own transfer history and surfaced it in Settings —
**as a caption beside a control that ignored it.** The committed API sample records the whole defect in two
adjacent lines:

```json
"free_transfers": 1,
"free_transfers_implied": 5,
```

⭐⭐⭐ The cause is one default. `free_transfers: int = 1` meant the server **could not tell *"I hold one"*
from *"nobody has said"***, so it answered both with 1. ⚠️ *A default that is also a valid answer is a
guess the code can no longer identify as one* — which is precisely the reasoning `ManagerStore` already
carried, about the field **one row up on the same screen**:

> *"Null, not a default … the app cannot tell a guess from an answer once it has written one down."*

### 3 — The setting did not survive the app closing

🔴 `_freeTransfers` was a plain field initialised to `1`, with **no store behind it**. Set it to 2, quit,
reopen, and every screen was planning on 1 again — silently. ⭐ *A setting that does not persist is a
setting that was never really offered* — the sentence ADR-279 wrote about the manager id, one row above
this one, which got a `ManagerStore` while this did not.

## What shipped

- **`free_transfers` is optional end to end.** `None` means *"you work it out"*. Precedence: **what the
  manager said → what his history implies → 1**. ⭐ Each step is a fact the step below it does not have.
- ⚠️ **The precedence itself did not change**, and that is deliberate. ADR-318's reasoning still holds:
  transfers made during the current window are invisible until the deadline passes, so *he may know
  something the derivation cannot*. What changed is only the case ADR-318 could not express — nobody
  having said anything.
- **`free_transfers_source`** — `you` · `history` · `default` — so a surface can **explain itself rather
  than assert**. ⚠️ *A number whose provenance is invisible is one the reader has to take on trust, and
  this is the number he already distrusted.*
- **`FreeTransferStore`**, with a `clear()`. ⭐ Without a way back, correcting the number once would be a
  one-way door: the app would never trust the history again, **including after the deadline that made the
  history right**.
- **Settings gains an "Auto" chip**, selected on the **override** and never on the effective number —
  ⭐ *highlighting `2` because history says 2 would make "Auto" and "2" look like the same choice, and the
  difference is the whole point: one keeps updating, the other does not.*
- **The pitch says `5 free`**, and the glossary stops claiming FPL does not publish it.

## The one that would have shipped broken

🔴 **The HTTP body kept its own default.** The dataclass had learned that `None` means *"you work it out"*;
`src/service/http/app.py` still said `Field(1, ge=0, le=5)`. In-process callers — the tests, Streamlit —
got the derived number. **Every request from the phone got the hard-coded 1**, which is every request that
matters here.

⭐⭐ *A default declared twice is a decision made once and obeyed in one place.* Caught by
`test_my_team_returns_over_http_what_it_returns_in_process`, which exists for exactly this and had nothing
to do with transfers.

## Two layout bugs, both mine, both from widening a label

⚠️ *"Transfers this week"* overflowed the pitch header by **89px**. I shortened it to `Transfers` with the
meaning moved into the value — and `5 free` **still** overflowed by **9.8px**, but only on the *framed*
live page inside the season walk, which is narrower than the plain one.

⭐⭐ So the fix is structural rather than a third round of shortening: the four stats **share** the width
and `scaleDown` to fit it. *Choosing copy that happens to fit the widest container is a guess that has to
be re-made every time either the copy or the container changes* — and it was re-made wrong twice in twenty
minutes. The same story one screen along: **"Auto" was a seventh chip in a row built for six** and
overflowed Settings by 30px, so the chips took their own wrapped line. ⭐ *A seventh option is not a copy
problem; it is one option more than the row was built for.*

## Definition of done

- **Tests** — six in `tests/test_service_endpoints.py`, thirteen in `mobile/test/free_transfers_test.dart`.
  Nine mutants killed: `or` instead of `is not None` (**zero read as unset** — ⭐ *the one value where
  being overruled costs points*, since the plan would recommend a move that is really a −4) · history
  ignored · **the HTTP default restored** · the dataclass default restored · the source lying when history
  could not be read · zero not saved · the bare number returning · Auto never highlighting · the chip
  selected on the effective number.
- **Smoke test** — the rendered Settings caption read back from a pumped widget, not from the source.
- **Docs** — this ADR, the index, PROJECT_STATUS, and `src/glossary.py` → `mobile/lib/glossary.dart`.

**2973 Python · 479 Dart.**
