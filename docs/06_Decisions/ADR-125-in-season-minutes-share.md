# Architectural Decision Record: In-season minutes in the xMins share — Defer to ~GW4-6

**Decision ID:** ADR-125
**Date:** 2026-08-24
**Status:** ✅ **Accepted — Defer** (owner-approved). Do not build now; revisit at ~GW4-6 alongside the
`FORM_WEIGHT` calibration. Investigated on the live GW1 data; the numbers below are measured, not estimated.
**Superseded By / Replaces:** Revisits the "explicitly not in scope" clause of ADR-124. Extends ADR-038 (xMins v0).
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`availability_weight` (ADR-038) is `chance_factor × minutes_share`, and `minutes_share` returns `None` for a
player with no stored history — which the caller reads as **1.0, "nailed-on"**. ADR-124 flagged this as the
sibling of the cold-start rate bug it fixed, and left it deliberately out of scope: a player with no history
takes both the raw rate *and* a full minutes weight, so neither damper holds.

Now that the GW1 backfill (Sprint 175) has populated `player_history`, in-season minutes exist and could inform
that share. The question is whether to use them yet.

---

### ✅ Proposed Decision: **defer, and build it at ~GW4-6**

Three findings, in order of how much they moved the decision.

#### 1. ADR-124 already absorbed most of the harm — measured

The 93 players with no stored history are **all 93** on the cold-start rate tier. ADR-124 forces the *outer*
minutes weight to 1.0 for that tier and applies `w` to the `points_per_game` term only, scaled by evidence
`c`. After one gameweek `c ≈ 0.08`, so the weight now has roughly 8% leverage on their rate where it used to
have all of it.

Measured by halving the no-history default (1.0 → 0.5) on the live board:

```
xP changed for 25 of the 93 players, all by ≤1.8 over a 3-gameweek horizon:
   M.Sangaré     9.3 → 7.5      Emersonn   6.5 → 5.6
   Tzolakis      8.1 → 6.6      Slater     4.5 → 3.6
```

None of them is near the top of the board any more — Sangaré, the worst case, ranks 49th. Before ADR-124 this
same defect was helping put him 1st. **The urgency was real yesterday and is largely spent today.**

#### 2. The in-season data would lie right now — and by exactly the amount that matters

**FPL writes a player's per-GW row when the fixture is created, not when it is played,** with `minutes = 0`. On
the live data, every one of Chelsea's 38 and Fulham's 23 players has a round-1 row reading 0 minutes, because
their opener kicks off tonight:

```
team   rows   earliest kickoff        total minutes
CHE      38   2026-08-24T19:00:00Z    0
FUL      23   2026-08-24T19:00:00Z    0
```

A naive in-season share — `minutes ÷ (90 × gameweeks)` — therefore reads:

```
Palmer    0/(90×1) = 0.00      "never plays"
Caicedo   0/(90×1) = 0.00      "never plays"
Sánchez   0/(90×1) = 0.00      "never plays"
```

It would zero the xP of two entire clubs for the two days their gameweek is in flight. And a 0-minute row for a
team that *has* played (an unused substitute — 266 of them this gameweek) is indistinguishable from these by
minutes alone. Any in-season minutes signal must first answer *"has this fixture actually been played?"* —
which is ADR-123's question again, one level down. The row carries `kickoff_time`, so it is answerable; it is
just not free, and getting it wrong is catastrophic rather than merely inaccurate.

#### 3. One gameweek is not evidence — and we just wrote that ADR

The natural design is the shrinkage this codebase now uses three times over (ADR-040, ADR-124):

```
in_season_share = played_minutes / (90 × gameweeks_actually_played)
c               = min(1, gameweeks_played / K)
share           = in_season_share × c + (historical share, else 1.0) × (1 − c)
```

That is almost certainly the right shape. But at one gameweek `c ≈ 0.1`, so it would barely move anything —
while introducing the trap in (2). Building a minutes signal off a single game is the same mistake ADR-124 just
corrected one function over: a single observation wearing the word "average". **The design is ready; the data
is not.**

#### What "revisit" means concretely

Build it when the `FORM_WEIGHT` calibration runs — the ADR-101 harness needs ≥4 gameweeks (`calibrate` currently
reports *"have 1, need ≥4"*), which is the same threshold, the same data, and the same sitting. One gate, not
two. By then `c` is meaningful, several gameweeks of started/benched history exist per player, and the
played-vs-scheduled distinction can be tested against real cases instead of one night's fixtures.

---

### 🔀 Alternatives Considered

- **Build it now with the kickoff-time guard.** Rejected: it is the full cost and risk of the change for
  almost none of its benefit (25 players, ≤1.8 xP, none near the top), and the guard would be validated against
  a single evening's fixtures.
- **Drop the "no history → 1.0" default to a flat penalty (say 0.75) as a stopgap.** Rejected: a magic constant
  that penalises *the unknown* rather than the *known-to-rotate*, which is exactly the instinct ADR-038 rejected
  ("never penalise the unknown"). It would hit a genuine new signing and a fringe squad player identically.
- **Do nothing and leave it unrecorded.** Rejected: it was raised twice and measured once; without a written
  decision it gets re-litigated, and the pre-kickoff-row trap gets rediscovered the hard way.

---

### 🧭 Consequences

**Positive** — no change to a live decision engine on one gameweek of data; the trap in (2) is documented at the
source before anyone builds on `player_history`; the work lands in the same sitting as the calibration that
needs the same evidence.

**Negative / risks (mitigations)** — the 93 no-history players keep a slightly generous minutes weight for a few
more gameweeks (*mitigation:* measured at ≤1.8 xP over 3 GWs for 25 of them, none near the top of the board, and
falling further as ADR-124's `c` grows); the deferral could be forgotten (*mitigation:* the trigger is tied to
`calibrate` clearing its ≥4-gameweek guard, which is already on the roadmap and already prints the countdown).

---

### 🧾 Status & follow-ups

- **Accepted — Defer.** No engine change. The one thing landed: a docstring note on
  `Storage.get_gw_history_by_code` recording that per-GW rows exist **before** their fixture is played, so the
  next reader of that table does not have to rediscover it.
- **Trigger to revisit:** when `calibrate` clears its ≥4-gameweek guard (~GW4-6), gated together with
  `FORM_WEIGHT`.
- **Design to build then:** the shrinkage above, with `gameweeks_actually_played` counted from rows whose
  `kickoff_time` has passed — never from row *presence*.
