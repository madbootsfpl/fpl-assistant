# ADR-283 — Alternatives belong beside the recommendation

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner — *"I want to merge the Transfer Tab into the This Week tab… I would then like to move
the signals tab to the main screen replacing transfers."*
**Touches:** ADR-256 (signals), ADR-279 (whose team this is), ADR-282 (distribution)

---

## The tab was not unused. It was in the wrong place.

This Week says **"Kinsky → Tzolakis, +4.1 xP"**. The obvious next question is *"and what else?"* — and the
answer to it lived one tab away, reached by leaving the card that raised it.

⭐⭐ **A list of alternatives is only meaningful beside the thing it is an alternative to.** So the board
moves under a `See transfer alternatives` button between the TRANSFER and TIMING cards, opened as a pushed
screen with a back button: ⚠️ *a tab is somewhere you go; this is something you open.*

The placement pays off immediately — the move This Week recommended is the highlighted card at the top of
the board you land on, so the screen opens already answering the question that sent you there.

⚠️ **The button shows even when the recommendation is "Hold."** *The reader most likely to want the
alternatives is the one who was just told to do nothing.*

## Signals takes the slot

The other half of the same argument. Signals answers *"has anything changed?"* — asked far more often than
*"who else could I buy?"* — and was buried in More.

⭐ **The purple nudge on My Team stays.** The tab is a second door, not a replacement: the banner is still
the thing that makes you look, and the owner chose to keep it.

⚠️⚠️ **That created a real bug, which is why it is worth writing down.** Signals marks its keys seen *as it
renders*. As a pushed screen the caller re-read the count when the screen popped — but **a tab is never
come back from**, so the badge would have sat there while you read the very thing it pointed at. Signals
now reports upward via `onSeen`.

## The two sentences that read as one complaint

The owner sent two screenshots three minutes apart:

> *That plan belonged to a different manager id. Cleared.*
> *A plan — not your FPL team · 3 changes*

**The first was correct and badly explained.** Until ADR-279 the manager id was a constant in the source —
`const int kDefaultManagerId = 2885974` — so every install opened on a demo squad, and the first plan a
tester saved was saved against *that* id. Setting their own id then produced a message that is true about
the machine and silent about the cause. ⭐ *A message accurate about the machine and silent about the cause
reads as a fault.* It now says it will not happen again, which is the part the reader needs.

**The second was not an error at all.** It is the ordinary draft banner. But landing minutes after a real
identity message, ⚠️ *two unrelated sentences that both begin by denying this is your team are read as the
same complaint twice.* It now says `Your plan — not saved to FPL yet` — what you are looking at, and what
has not happened.

## ⚠️ These screens had no widget tests, and the suite stayed green through the whole rewiring

A nav change and a **new required constructor argument** passed 287 tests without a single assertion.
⭐⭐ *A suite that stays green through a rewiring is not confirming the rewiring; it is silent about it.*

Eight tests now cover it, and writing them found three things reasoning would not have:

- **`pumpAndSettle` never settles** against the loading spinner's endless animation. Two `pump`s instead.
- **The default 800×600 test window is too short.** This Week scrolls, so the list stopped building at the
  Lineup card — the Transfer card, the button and Timing were *never constructed*. ⭐ *A widget test on a
  short window asserts about the top of the page and reports it as the whole page.*
- **The card renders its label uppercased.** `indexOf('Transfer')` found nothing while `TRANSFER` was on
  screen — ⚠️ *asserting against what the code says rather than what the screen shows is how a passing test
  describes a page nobody sees.*

8/8 mutations killed, including the button being deleted, drifting out from between the cards, the nav
label and icon disagreeing, `onSeen` being dropped, and either message reverting.

## The landing page

- **The explainer video was broken.** `99CATSFHBAA` → `Igt5mqheQpE`, in both the iframe and the comment.
- **One "Launch the app" became a platform picker**: Desktop and Android as buttons, and `iOS — coming
  soon` as **plain text**. ⭐ *A greyed-out button still invites a tap, and a tap that does nothing reads as
  broken.* A line of muted text says the same thing and asks for nothing.

## ⚠️⚠️ And the answer to the question underneath it: the cap does not apply to the app

The owner asked whether publishing an Android button opens the product past his 50-user cap.

**The cap has never applied to the app.** `FPL_USER_CAP` and the `beta_users` table live entirely in
`src/web_streamlit/`. The FastAPI service the mobile app talks to has **no cap, no allowlist and no auth** —
so anyone holding the APK has been uncapped since the first build. Publishing the button does not change
the cap; it changes **discovery**.

What stands between the service and load is per-caller rate limiting: `/squad/build` 20/min (the LP solver,
the only endpoint whose CPU a stranger controls), `/players` 60/min, `/league` 20/min, `/feedback` 5/hour.

⭐ The number to watch is not users. It is the **slowest 5% on `/squad/build`** in the platform panel
(ADR-280) — *which is the first argument that panel has settled rather than merely reported.*

📌 **Named as open, not solved:** the mobile API is unauthenticated and uncapped. That was acceptable while
distribution was "I send you a file"; a public download button makes it a decision rather than a default.
It belongs with accounts/identity (ADR-259), still parked.

## What this does not do

- **Trending's pill order did change, on the third answer.** The owner asked for Worth noticing to lead,
  called the direction a mistake, then confirmed the swap after seeing the build. ⭐ *Recorded as three
  answers rather than tidied into one, because the cost of the churn was a minute and the cost of
  pretending it did not happen is a reader who cannot tell a settled decision from a fresh one.*

  **Order and default moved together.** A first pill that is not the selected one is a row that opens
  mid-way along itself — ⚠️ *"first tab" names a position and a starting point, and splitting them makes
  the screen look like it forgot where it was.*

  ⚠️⚠️ **And nothing pinned that order, through two reversals.** Both times the full suite stayed green.
  ⭐ *An order no test names is an order the next edit reverses by accident, and the only reader who
  notices is the owner.* Three tests now hold the row, the two leading boards and the default; 3/3
  mutations killed.
- **Mini-league sub-tabs, the Lab's other modes, the tablet's portrait pitch** — all still open.
