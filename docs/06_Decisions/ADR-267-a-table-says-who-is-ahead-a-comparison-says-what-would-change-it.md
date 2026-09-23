# ADR-267 — A table says who is ahead; a comparison says what would change it

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"Start with General & Captain Stats from FFH and the other feature that we have in
the desktop version, which is super is the Head to Head comparison — thats a must have!"*
**Builds on:** ADR-141 (leagues), ADR-161 (the H2H decomposition), ADR-227 (one player shape)

---

## Context

The competitor's mini-league screen has three tabs and five sub-tabs. The owner picked **General**,
**Captains** and — the one that is not on the competitor's screen at all — the **head-to-head** from our
own desktop app.

⭐⭐ **That third one is the reason the screen exists.** A league table tells you who is ahead, which you
already knew from the app that generated it. ⚠️ *It cannot tell you whether that is about to change.*

## Decisions

**Three endpoints, because they cost three different amounts.**

| | Upstream cost |
|---|---|
| `leagues` — which leagues you are in | **1** request |
| `league` — the table | **1** request |
| `league` with `with_captains` | **1 + one per manager**, capped at 20 |
| `h2h` | **2** requests |

**⭐ Looked up from the manager id.** *Nobody knows their league id* (ADR-141) — it lives in a URL you have
to go and find. ⚠️ **Private leagues lead**: FPL mixes the league you joined with friends in among
automatic ones, and *sorting by size would bury the only leagues anyone means.*

**⚠️⚠️ The captain split is opt-in and fetched once.** It is the only panel here that spends a request per
manager, so it happens when that tab is opened and not again. ⭐ *A screen that quietly spends fifty
requests to draw a panel nobody looked at will be blamed for being slow.*

**⚠️ A failed squad read is absent, not fatal** — *an exception would throw away nineteen good fetches
because of one bad id* — so the answer reports `captains_from`, and the screen says *"From 12 squads"*.
⭐ *A partial read must never present itself as the whole league* (ADR-215's rule).

**⭐ The share, not just the count.** *"9 of 12" is a different fact from "9"*, and the reader is deciding
whether to differ from a crowd.

**⚠️ The head-to-head reads the last FINISHED gameweek** — a rival's picks are public only after a
deadline — and uses `last_completed_gameweek`, the same rule the rest of the app uses. ⭐ *Two places
deciding separately where "now" is would eventually disagree.*

**⭐⭐ And it sets the shared players aside.** They are usually most of both squads and the part you can do
nothing about; ⚠️ *printing the shared total is what makes a 2 xP gap believable rather than looking like
a rounding error on two big numbers.* What is left is priced, captain differentials marked.

## ⚠️⚠️ The shape sweep found a real defect in the engine's output

`h2h`'s differential rows carried `{id, web_name, team, position, multiplier, xp}` — **a sixth player
shape, with no `status`**. So ⭐ *a differential who was doubtful could not be flagged as one*, which is
exactly ADR-226's bug — **a doubt hidden is a doubt priced at certainty** — landing on **the players the
whole screen is about**.

Fixed in the **service layer**, not the engine: the Streamlit page reads the same function, and ⭐ *a shape
the API owes its clients is not a reason to change what the engine computes.*

## Verification

* **14 Python tests**, every one stubbing the FPL boundary — ⭐ *a test that needs the internet is a test
  that fails for reasons about the internet*, and gets ignored.
* **6/6 mutations killed.** ⚠️ **One survived first**: removing the 20-manager cap changed nothing, because
  every fixture held three or four managers — ⭐ *the tell is always "does the population contain the
  case?"*, and it did not. A fifty-row fixture kills it.
* **14 Dart tests** against stubbed-but-real samples; **4/4 mutations killed** — ⚠️ one after
  `greaterThan(0)` let a fabricated `99` through: *a bound that any wrong answer also satisfies is not an
  assertion.* Replaced with the real invariant: nobody can be captained by more managers than were read.
* 2,540 Python · 182 Dart.

📌 **Not built:** Transfers, Rank and Chips sub-tabs, and the Awards tab. Named rather than forgotten.
