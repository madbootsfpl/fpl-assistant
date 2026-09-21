# Spike 018 — does "direct Flutter → Supabase" actually work?

**Status:** scaffolding written; unrun until the Flutter SDK is installed.

## The claim under test

The mobile audit §4.1 commits to **direct Flutter → Supabase, no API**, for *"the majority of the app's read
surface"* — players, teams, fixtures, the xP board, the DNA boards. Everything downstream assumes it.

⭐⭐ **Nobody has ever tested it from a Flutter client.** That is the whole point of this slice: not to build a
screen, but to find out whether the architecture holds, while finding out is still cheap.

## Why this needs no auth

Board data is **public football data**. Since ADR-216 the pipeline's tables are `SELECT`-only for `anon`, so
a client can read them with the publishable key and nothing else. Owner-scoped data — your squad, your
preferences — needs Stage C, and is deliberately **not** in this slice.

⭐ *The read surface and the identity surface are separable, so separate them and learn from the cheaper one
first.*

## What it does

One screen. Fetch `xp_board` over PostgREST, join the club short name, render a list sorted by xP over the
next five gameweeks. That exercises:

1. the network path (PostgREST, the publishable key, TLS from a phone)
2. the payload — **~250 KB for 667 players**, and whether that is tolerable on mobile data
3. the data shape — is `by_gameweek` as JSON usable from Dart without a server reshaping it?
4. the sums — does a horizon-5 total computed in Dart match what the web app shows?

⚠️ **Point 4 is the one that matters most and is easiest to skip.** ADR-213 published *unrounded* per-gameweek
values precisely so any horizon sums exactly; a Dart client that rounds differently would put a different
number on the phone from the one on the web, which is ADR-123/127/181's failure arriving on a new platform.

## What it deliberately does not do

No auth, no saved squad, no writes, no navigation, no state management, no theme. Those are Phase 4. A slice
that grows a framework stops being a slice and starts being a commitment.

---

## 🐛 Found before the SDK was even installed: the client cannot round the same way

ADR-213 publishes **unrounded** per-gameweek values so any horizon sums exactly. A client therefore sums a
prefix and rounds to 1dp — and that is where the platforms part company.

| | |
|---|---|
| horizon sums on the real board | **5,272** |
| landing exactly on a half-tenth | **5** (Palmer h2 = 0.55, Cho h1 = 1.95, Cho h3 = 5.85, …) |

⚠️ **And Python's answer on those is not a rule anyone can copy:**

```
round(0.55, 1) = 0.6      round(1.95, 1) = 1.9      round(5.85, 1) = 5.8
```

Not banker's, not half-up — whatever the binary float happens to be nearest to. ⭐⭐ **So there is no Dart
rounding mode that reproduces it.** A client that re-derives a displayed number will disagree with the server
on edge cases, and choosing a better rounding mode cannot fix that.

**~0.09% of values**, so roughly one player in a list of 667 would read differently on the phone than on the
web. Small, invisible in testing, and exactly the shape of ADR-123/127/181 — one number, two implementations.

### Not designed around — measured

The obvious fix is to publish the eight rounded horizon totals so the client reads rather than computes. That
is cheap (~5 KB) and it is **speculative before a client exists**, which is the trap this session has fallen
into twice.

📋 **So the slice's job includes this test**: render the list, compare its numbers against the web app's for
the same horizon, and count the disagreements. If it is the predicted handful, publishing the totals is
justified by evidence. ⭐ *The point of a slice is to learn, and this is the thing worth learning.*

---

# ✅ Run, 2026-09-21 — §4.1 holds

```
667 players · 162 KB · 511 ms
```

**Direct Flutter → Supabase works.** No API, no auth, no server in the middle. The claim the whole mobile
plan rests on is no longer an assumption.

| the same question — *"players ranked by xP"* | payload | time |
|---|---|---|
| the web app, cold | **2,468 KB** | 10,786 ms |
| this slice | **162 KB** | 511 ms |

⚠️ **Not a like-for-like race** — the slice ran from a Mac in Chrome, the web figure from Streamlit Cloud, and
those are different network paths. What *is* comparable is the payload: **162 KB to fetch the answer against
2,468 KB to ship the inputs and recompute it.** That is the architecture doing what it was designed to.

⭐ **162 KB also beat the 250 KB estimate**, because the client asks for four columns —
`select=web_name,team,position,by_gameweek`. The rest of the board never crosses the wire. PostgREST's column
selection is doing real work, and the web app's `get_xp_board()` takes every column without needing them all.

## What this does not yet answer

- **A real device on mobile data.** Chrome on a Mac is a generous network. The device questions need Xcode.
- **The rounding divergence.** Predicted at ~0.09% of values, with no Dart rounding mode able to fix it.
  Comparing the slice's numbers against the live web app is still the outstanding test, and it is the one
  that decides whether the server should publish the rounded totals.

## The rounding question, settled

**Zero boundary players on production, at every horizon.**

⚠️ **The owner's first check — "compared a few players, numbers match" — did not settle it, and saying so
mattered.** At ~0.09%, three comparisons have about a **0.3% chance of meeting the case at all**. A sample
that cannot contain the case cannot rule it out (ADR-195 · ADR-202 · ADR-208, the same shape a fourth time).

So the client was made to find the cases instead. And the detector it was given was **wrong in a way that
made the answer stronger**: its 1e-6 tolerance flagged `7.249999999999998`, a value both platforms round to
7.2 in perfect agreement — **16 reported boundaries where only 5 exist.**

⭐ Because that rule flags everything the exact rule does *and more*, finding **zero** with it means there is
genuinely nothing to find. An over-permissive instrument returning empty is a real result.

**Now fixed** to decide on the shortest round-tripping representation — the same basis Python's `repr` uses —
so both platforms ask the identical question. ⭐ *An instrument loose in the direction of alarm still tells
you the wrong thing; it just feels safer while doing it.*

### What this means for the server publishing rounded totals

📅 **Not justified today, and not dismissed.** The divergence is real in principle — 5 genuine cases exist on
the test snapshot — and zero on production is a fact about **today's numbers**, which change every pipeline
tick. The detector stays in the client so the question can be re-asked rather than re-argued.
