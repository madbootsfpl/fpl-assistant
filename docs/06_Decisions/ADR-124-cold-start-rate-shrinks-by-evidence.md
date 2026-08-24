# Architectural Decision Record: The cold-start xP rate shrinks toward `ep_next` by evidence

**Decision ID:** ADR-124
**Date:** 2026-08-24
**Status:** ✅ **Accepted — owner-approved ("build it"), built.** Sprint 174 / US-431. Design verified on the
live GW1 data *before* the gate; the invariance claim re-verified against it after (numbers below are real).
**Superseded By / Replaces:** Subsumes ADR-104 (the `ep_next` cold-start floor) — which becomes the zero-evidence
end of this curve rather than a separate rule. Applies ADR-040's shrinkage lesson to the one branch it never
reached.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

One gameweek of real data inverted the xP ranking. On the live board, over a 3-gameweek horizon:

```
  1. M.Sangaré      xP=43.4  rate=14.00/GW  mins=75  ep_next=2.0  tier=current
  2. Tzolakis       xP=30.0  rate=10.00/GW  mins=90  ep_next=1.9  tier=current
  3. Emersonn       xP=25.2  rate= 9.00/GW  mins=65  ep_next=1.8  tier=current
  4. Muharemović    xP=18.6  rate= 6.00/GW  mins=90  ep_next=2.2  tier=current
  5. Slater         xP=18.0  rate= 6.00/GW  mins=90  ep_next=1.0  tier=current
  6. Haaland        xP=17.1  rate= 6.91/GW  mins=90  ep_next=4.0  tier=hist
```

Five players with **one game each** sit above every established player in the game. Munoz is 14th on **27
minutes**.

The mechanism is small. `player_xp` picks a scoring rate from three tiers: a trusted ≥900-minute multi-season
baseline (`hist`), a shrunk low-evidence career rate (`fallback`, ADR-040), or — for a player with no history at
all — the cold-start branch, which takes `max(ep_next, points_per_game)` (ADR-104).

After one game, **`points_per_game` *is* that game's score.** Sangaré's 14-point opener becomes a 14-points-per-
gameweek projection. Haaland's 2-point opener is ignored, because he has a real baseline. So the players with the
*least* evidence get the *most* extreme rates.

Preseason this was safe: `points_per_game` was 0 for everyone, so `ep_next` always won and the branch behaved as
a floor. The `max()` could not misbehave until there was a season to average. ADR-104's own comment — *"`max`
lets real scoring take over once the player plays"* — reads as intent that assumed `points_per_game` would be an
average. For most of the season it is. For the first few gameweeks it is a single result wearing the word
"average".

**Two safeguards no-op for exactly this population.** `availability_weight` (xMins v0, ADR-038) derives its
minutes share from past seasons; with no history it defaults the share to 1.0 — "nailed-on". So a cold-start
player takes the raw rate *and* a full minutes weight (`w=1.0` above, against 0.72–0.99 for the established
players). Neither damper is holding.

**This is not the season-rollover cold-start we already knew about.** That one made everyone *equally* cold and
was honest about it (ADR-104's floor, the 🌱 empty-state note, US-430). This makes a specific 44-player group
*confidently wrong*, at the top of the board, on the page people act from.

#### Decision Drivers
- **Live and visible** — it is the first thing on the ranking, and it is worst exactly where hype lives (new
  signings, promoted clubs) — the players a manager is most tempted by.
- **Self-inflicted by success** — nothing broke; real data simply arrived and activated a dormant branch.
- **The lesson is already in the codebase** — ADR-040 solved this exact failure for a neighbouring tier.

---

### 🧠 The insight: those aren't two tiers, they're the two ends of one curve

`fallback_rate` (ADR-040) already handles this failure mode, and its docstring names it outright: *"projecting
raw `points_per_game` lets a one-game cameo (Benitez: 90 min, 7 pts → ppg 7.0) rank like a star."* Its answer is
to shrink toward a prior by how much evidence exists:

```
rate = career_pp90 × c + prior × (1 − c),   c = min(1, best_season_minutes / 900)
```

The cold-start branch is the one tier that never got this treatment — because with no history there was no
career rate to shrink. But there is now: **this season's minutes are the evidence.**

Look at what the branch actually does at its extremes:

| | today | why |
|---|---|---|
| **0 minutes** | `rate = ep_next` | `points_per_game` is 0, so `max` always picks `ep_next` (ADR-104) |
| **≥900 minutes** | `rate = points_per_game` | a full season's average — as trustworthy as the `hist` tier's bar |

Both endpoints are already agreed behaviour. `max()` is a crude switch between them that flips on the *value*
rather than on the *evidence* — which is why one big score flips it on day one. Verified on the live data:
**0 players have 0 minutes but a non-zero `points_per_game`**, so the `ep_next` tier is *exactly* the
zero-evidence case, not merely similar to it.

---

### ✅ Proposed Decision

**Interpolate between the two endpoints instead of switching between them**, with the same shrinkage shape
`fallback_rate` already uses and the same 900-minute evidence bar the rest of the module uses:

```
c    = min(1, minutes_this_season / 900)          # evidence, not value
rate = (w × points_per_game) × c  +  ep_next × (1 − c)
```

where `w` is the xMins weight, applied to the `points_per_game` component **only** — `ep_next` already prices
minutes, and ADR-104 is explicit that it must not be double-discounted. The outer weight then becomes 1.0 for
this branch, as it already is for the `ep_next` tier today.

**Both endpoints reproduce today's behaviour exactly:**
- at `c = 0`: `rate = ep_next`, outer weight 1.0 → bit-for-bit ADR-104.
- at `c = 1`: `rate = w × points_per_game`, outer weight 1.0 → bit-for-bit today's `current` tier.

So the change is strictly an **interpolation between two behaviours that are already agreed**. Only the middle is
new. On the live data that middle is **47 players**; the other **81** cold-start players sit at `c = 0`.

That is the whole safety case, so it was checked against the live board rather than argued: replaying the old
`max(ep_next, ppg)` rule over the same 604 players, **all 81 zero-evidence players come out bit-for-bit
identical**, and **31** players' xP actually shifts (the 47 minus 3 who are unavailable, 1 with no
points-per-game, and a tail whose `ppg` was already close to their `ep_next`).

The two tier labels `ep_next` and `current` collapse into one — proposed name **`cold_start`** — since they are
no longer distinct rules. `rate_source` is near-invisible in the UI (only `hist` is surfaced, as a `*` in
`ui/xp.py`), so this touches a handful of tests and nothing a user sees.

#### Verified on the live data

The five inflated players clear the top of the board, and the established players return:

```
   TODAY                          PROPOSED
1. M.Sangaré    43.4   →      1. Haaland       17.1
2. Tzolakis     30.0          2. B.Fernandes   16.0
3. Emersonn     25.2          3. Watkins       14.5
4. Muharemović  18.6          4. Semenyo       13.7
5. Slater       18.0          5. Mbeumo        13.7
6. Haaland      17.1          6. Palmer        13.3
```

Crucially it still **tells the cold-start players apart** — it damps them without flattening them:

```
player          mins   ppg    ep_next    proposed
Mendy             63  15.0       0.8        1.79     ← FPL expects little; stays low
M.Sangaré         75  14.0       2.0        3.00
Tzolakis          90  10.0       1.9        2.71
Muharemović       90   6.0       2.2        2.58
Slater            90   6.0       1.0        1.50     ← same ppg as Muharemović, lower ep_next
```

And it converges on the truth as evidence arrives — a genuine 6.0-ppg signing reaches their real rate by ~game
10, while a one-game fluke that reverts is damped throughout:

```
games:            1     3     5    10    15    20
real 6.0 ppg   2.40  3.20  4.00  6.00  6.00  6.00      → converges
fluke (→2.0)   3.20  2.99  2.70  2.60  2.30  2.30      → never spikes
```

---

### 🔀 Alternatives Considered

- **Shrink toward the flat replacement prior (2.0) instead of `ep_next`,** exactly mirroring `fallback_rate`.
  Rejected: it discards a player-specific signal we already hold. Mendy (15.0 ppg but `ep_next` 0.8 — FPL does
  not expect him to feature) lands at **1.79** under the proposal but **2.91** shrinking to a flat prior, which
  quietly promotes a player FPL is telling us to avoid. It would also abandon ADR-104 rather than subsume it.
- **A hard minutes gate — no `points_per_game` until 900 minutes.** Rejected: it is a cliff. A genuine 6.0-ppg
  signing would be pinned at their `ep_next` for ten gameweeks and then jump the whole way in one refresh
  (`2.00 … 2.00 → 6.00` in the table above). Same bar, but discontinuous, and wrong for longer.
- **Cap the cold-start rate at a multiple of `ep_next`.** Rejected: a magic constant with no story behind it, and
  it still lets one game set the rate — just a smaller one.
- **Turn on the ADR-060 form blend and let it correct this.** Rejected as the fix: form is a *blend toward
  recent scoring*, so it would pull further toward the one game, not away. (It is also dormant —
  `player_history` is empty.)
- **Do nothing; it self-heals by ~GW10.** Rejected: ten gameweeks of a visibly inverted top-of-board during the
  weeks new testers are forming their opinion of whether the tool's numbers can be trusted.

---

### 🧭 Consequences

**Positive** — one rule where there were two; the ranking stops being led by single-game noise; the ADR-040
shrinkage lesson finally covers every tier; both endpoints are provably unchanged, so the risk surface is 47
players rather than the whole pool; converges on the truth automatically as minutes accrue, with no GW-number
special-casing and nothing for the owner to flip later.

**Negative / risks (mitigations)** — a genuinely excellent new signing is under-rated for their first weeks
(*mitigation:* that is the honest position at one game of evidence, and it is what we already do to every player
with a short history via ADR-040; `ep_next` carries FPL's own optimism in the meantime); `ep_next` becomes
load-bearing for longer, so an FPL quirk in it propagates further (*mitigation:* it is already load-bearing for
all 81 zero-minute players under ADR-104, and its weight *falls* as real evidence arrives); the 900-minute bar is
reused on in-season minutes where it means "~10 games" rather than "a trustworthy season" (*mitigation:* that is
the same reading `_MIN_SEASON_MINUTES` already has in `baseline_rate`, and the interpolation means the bar is a
soft ramp, not a threshold anything snaps at).

**Explicitly not in scope** — the xMins minutes *share* still defaults to 1.0 for a player with no history
(`availability_weight`, ADR-038), even though in-season minutes could now inform it. That is a real second
defect, it compounds this one, and it deserves its own gate rather than being smuggled in here.

---

### 🧾 Status & follow-ups

- **Accepted — built (Sprint 174 / US-431).** `cold_start_rate` in `analytics/xp.py` (pure, alongside
  `baseline_rate` / `fallback_rate`), wired into `player_xp` with the merged `cold_start` label. 8 new tests:
  both endpoints pinned against today's behaviour, the one-game damping, the convergence trajectory, the
  `ep_next`-still-separates-equal-scorers property that ruled out the flat prior, the `w`-on-`ppg`-only
  placement, empty-safety, and the reported `minutes_weight`. 1115 → **1123 tests**, ruff clean.
- **One thing the build changed from the plan:** `minutes_weight` is *surfaced* (it drives the expected-minutes
  display), and forcing the outer multiplier to 1.0 would have made it report 1.0 for every cold-start player
  even when the blend had discounted their `ppg` term. It now reports the **effective** weight — weighted ÷
  unweighted — which still reads 1.0 at zero evidence and `w` at full, so both endpoints hold for the displayed
  field too, not just the rate.
- **Test fixtures gained a `minutes` field.** Six helpers built player dicts without one, so under the blend
  they all fell to the zero-evidence end and stopped exercising the paths they were written for. They now
  default to `minutes=900` — "a player whose rate is their points-per-game" now has to *say* it has the evidence
  for that, which is the point of the ADR.
- **Follow-ups, not this ADR:** in-season minutes feeding the xMins share (ADR-038); turning on the ADR-060 form
  blend once `backfill` has populated `player_history`.
