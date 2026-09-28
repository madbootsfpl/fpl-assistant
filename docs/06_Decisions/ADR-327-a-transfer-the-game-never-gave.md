# ADR-327 — A transfer the game never gave

*Two tester reports, one screen: four transfers where FPL allows three, and four cards with one body between them.*

**Date:** 2026-09-28
**Status:** Accepted
**From:** a tester — *"Transfers — calculated 4 transfers for manager ID 1467290, there are only 3 available,
how are you calculating same?"* and *"4 transfers show attached image, data is the same after the headline on
each, which is an error."*
**Touches:** ADR-318 (the derivation), ADR-321 (the free-transfer number), ADR-089 (the explanations)

---

## Context

Both reports came from one screenshot, and they are **two unrelated defects** that happened to land on the
same screen. Worth separating before anything else, because the second one explains why the first looked
worse than it was: four wrong cards, each repeating the same wrong sentence.

## 1. The count — a free transfer for a gameweek FPL does not pay one for

`free_transfers_from_history` (ADR-318) derives the number from a manager's own history, because the
authenticated endpoint that returns it outright needs their login. It opened with:

```python
held = 1                                        # ⭐ GW1 opens with one
```

⚠️⚠️ **It does not.** FPL issues your first free transfer *after* the GW1 deadline, for GW2. Before that the
squad is unlimited to edit, which is not a transfer anyone can bank. The loop then adds one for every played
gameweek after the first, and the function ends with `+ 1` for the week ahead — so that opening `1` was
counted a second time.

**Reproduced against the tester's own manager**, fetched live from `/entry/1467290/history/`:

| GW | transfers | chip |
|---|---|---|
| 1 | 0 | |
| 2 | 1 | Bench Boost |
| 3 | 1 | |
| 4 | 0 | |
| 5 | 0 | |

FPL's arithmetic: GW2 earns one and spends it · GW3 earns one and spends it · GW4 earns one · GW5 earns one ·
the week ahead earns one → **3**. The function returned **4**.

**Fixed by opening at `0`.** Every scenario re-checked: an untouched season still reaches the cap of 5, a hit
still costs points rather than a negative bank, and a wildcard week still leaves the bank untouched.

⭐ *An off-by-one in a bankable resource does not look like a bug. It looks like the app being generous*,
which is why it took a tester with the real number in front of him to see it.

### 🔴 Three tests agreed with the bug

`test_a_chip_week_leaves_the_bank_alone` asserted `banked == 3` where FPL gives 2. Two endpoint tests asserted
a derived 4 and an implied 3. All three were written against the implementation rather than against the game,
and all three passed for two weeks.

⚠️⚠️ *A test written by reading the code cannot disagree with it.* The new tests state FPL's rule first —
including one that reproduces this manager's exact history and names him — so the next change has something
to be wrong about.

⭐ Bench Boost is in that regression fixture deliberately. It is **not** in `FT_FREE_CHIPS`, because it does
not make transfers free, and a "fix" that quietly widened that set would make the test pass for the wrong
reason.

## 2. The cards — one explanation, painted four times

The screenshot's four cards carried different headlines (`+3.3`, `+3.5`, `+1.7`, `+1.8`) and **identical
bodies**: every one claimed *"+3.3 to your starting XI"*, *"Higher projected points (6.5 vs 2.4)"* and
*"Selling M.Sangaré (2.4 xP)"* — including the card that sells Konsa.

Two halves, and each is a one-line fault:

* `explain_gameweek` explained **`plan["transfer"]`**, the primary move, and nothing else. A coordinated plan
  holds its moves in `plan["transfers"]`, and those were never explained at all.
* `this_week_view.dart` looped over `moves` for the headline and read `explanation['transfer']` — hoisted,
  outside the loop — for the body.

```dart
for (final m in moves)
  _Card(
    headline: '${m['out']['web_name']} → ${m['in']['web_name']}',   // the loop variable
    explanation: explanation?['transfer'] as Map<String, dynamic>?,  // …and not the loop variable
  ),
```

⭐⭐ **`explain_transfer` was never wrong.** It was right about the move it was handed, every time. *Nothing
was wrong except how many times the answer was used* — which is why no test of the explainer could have caught
it, and why it is worth writing down as a shape rather than as a typo.

⚠️ **Invisible until a plan holds more than one move**, which is the condition this tester reached and the
committed sample does not: `gameweek-plan.json` has exactly one transfer in it.

**Fixed on the server**, not the client: `explain_gameweek` now returns `transfers`, one `Explanation` per
move, **keyed by the incoming player's id**. ⭐ *Not by position* — matching a card to its reasons by index
holds only while both lists stay in the same order, and neither side promises that. The client looks its own
move up by id; `explanation["transfer"]` stays, because the web app and the ask layer read it and this adds a
shape rather than replacing one.

⚠️ `_explained` had to become **recursive**: it flattened dataclasses one level deep, and the new key is a
dict *of* them. ⭐ *The shape grew a level and the converter did not, which fails at the wire rather than in
the test.*

## Verified

* **Live**: manager 1467290 now derives **3**, against FPL's 3.
* **Server**: five tests in `test_every_move_explains_itself.py`, three of which fail if the primary
  explanation is reused — proved by reverting to exactly that.
* **Client**: three widget tests in `transfer_cards_do_not_share_reasons_test.dart`, **all three** failing
  against the shipped line, proved the same way. ⚠️ They need a tall viewport: the cards sit in a lazy
  `ListView` and the fourth — the one the bug shows on best — is off-screen at the default 800px test
  surface. ⭐ *A widget test that only ever renders the first item cannot see a bug about the rest of them.*
* **Contract**: `gameweek-plan.json` regenerated; the diff is the new key and nothing else. The `my-team.json`
  churn the same run produced was reverted — `age_minutes`, a countdown and a signal id are time drift, and
  ⭐ *a sample regenerated for an unrelated reason is a diff nobody reads next time.*

## Consequences

**Good:** the number matches the game, and every card explains its own move. 3,018 Python and 484 Dart tests
green.

⚠️ **Unchanged, and worth stating:** the derivation's blind spot from ADR-318 is still there — transfers made
*during* the current window are invisible until the deadline passes, because `event_transfers` only appears
once a gameweek ticks over. The manager's own override still wins (ADR-321). ⭐ *This is the honest reason the
paid tools ask you to log in.*

**Open:** `GameweekRequest.free` still defaults to `1` where `MyTeamRequest.free_transfers` is `None` with a
derived fallback (ADR-321). Both surfaces now receive the right number from the client, so nothing is wrong
today — but it is the same *"a default that is also a valid answer"* shape ADR-321 removed from its
neighbour, left rather than changed in a bug fix.
