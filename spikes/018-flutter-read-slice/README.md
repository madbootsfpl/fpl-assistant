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
