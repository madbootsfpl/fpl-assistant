# Architectural Decision Record: Percentiles must not rank a tie at the top

**Decision ID:** ADR-127
**Date:** 2026-08-24
**Status:** ✅ **Accepted — owner-approved: formula **B** (percentile rank), and the team-grade drop accepted
rather than re-tuning the thresholds.** Built (Sprint 178). Every number below is measured on the live data.
**Superseded By / Replaces:** Corrects the ranking maths behind ADR-118 (Player DNA) and ADR-119 (Team DNA).
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

On the live app, **A.Becker — a goalkeeper — reads *Goal Threat: 96th percentile* on a raw xG/90 of 0.00**, and
*Set Pieces: 100th percentile* on a raw score of 0.

Both ranking functions count peers **"at or below"** the player:

```python
# player_dna._percentile                    # team_dna._rank
round(100 * sum(1 for v in vals if v <= value) / len(vals))
```

So when a pool is heavily tied — nearly every goalkeeper has 0 xG and no set-piece duty — a **0 counts as
beating everyone else on 0**, and lands in the 90s. The axis reads *elite* precisely because the player has
nothing there. Confirmed: `Set Pieces` for GK is the one **fully tied** pool in the current data (every peer
exactly 0.0), and it scores **100**.

This is pre-existing (ADR-118) and was invisible only while the peer pool was empty and every percentile was
`None`. Fixing that (ADR-126, Sprint 177) made percentiles visible again and surfaced it. It would have appeared
at ~GW5 regardless.

**There is a second, quieter fault in the same line.** The count includes the player themselves, so with
`n` peers everyone is inflated by `1/n`. At the 20-team scale of Team DNA that is **+5 points for the best team
and ~+2.5 through the middle** — the best team can only ever read exactly 100, and a mid-table side reads
better than it is.

#### Decision Drivers
- **It is visibly wrong on the live app**, on the differentiator feature, and a user reported it.
- **Two implementations, one bug** — `player_dna._percentile` and `team_dna._rank` have the same flaw written
  twice. That is the drift that `DEADLINE_LEAD` (ADR-123) was consolidated to prevent.
- **Percentile feeds more than the radar** — insight text, verdict scores and Team DNA letter grades all read
  from it, so the blast radius needs measuring, not guessing.

---

### ✅ Proposed Decision

**Rank ties at their average position, not at the top of the tie**, in **one shared function** that both DNA
modules import — the fix written once, not twice.

Two standard formulas were run end-to-end on live data:

| | formula | all-tied pool | best of 20 | worst of 20 |
|---|---|---|---|---|
| today | `(below + equal) / n` | **100** ❌ | 100 | 5 |
| **A — midrank** | `(below + 0.5·equal) / n` | **50** ✅ | 98 | 2 |
| **B — percentile rank** | `(avg_rank − 1) / (n − 1)` | **50** ✅ | **100** | 0 |

**Recommendation: B, the classic percentile rank.** Both fix ties identically. B additionally preserves the
**0–100 endpoints**, which matters because the insight copy is written as *"top {100 − percentile}%"* — under A
the best player in the game reads *"top 2%"*, which is wrong in a way a reader would notice. B keeps *"top 1%"*.

#### Measured on the live data

**Player DNA — the shift lands exactly where it should.** ~50% of percentiles move, and the movement is
concentrated in tied pools while genuine differentiation is left almost untouched:

```
A.Becker  GK   Goal Threat  96 → 48      Haaland  FWD  Goal Threat  100 → 100
A.Becker  GK   Set Pieces  100 → 50      Haaland  FWD  Set Pieces   100 →  89
Raya      GK   Goal Threat  96 → 48      Saka     MID  Creativity    97 →  96
```

The elite stay elite; the meaningless stop reading as elite. That is the whole intent.

**Insight text — 81 of 250 players sampled change.** Most move by a single point (*"top 15%"* → *"top 16%"*).
A few sit exactly on the 85 threshold and flip wording:

```
Kayode  before: Elite value: top 15% of defenders (pts/£m 25.11)
        after : Strong value: pts/£m 25.11 (84th percentile)
```

**Team DNA — this is the part that needs your call.** All 160 axes shift, and **9 of 20 teams drop one letter
grade**: BHA A+→A · ARS, LIV, MCI A→B · HUL, IPS, NEW, CRY B→C · CHE C→D.

That is *not* the tie fix. It is the second fault — removing the self-count inflation — and it is identical
under both formulas. **The old grades were simply too generous**, because every team was scored ~2.5 points
above its true position. The ordering of teams does not change at all; only the absolute numbers, and the
letters cut from them.

So there is a sub-decision: **accept the drop, or re-tune the grade thresholds** (currently 85 / 72 / 58 / 42)
to preserve today's distribution. **My recommendation is to accept it** — re-tuning to reproduce known-inflated
output would be fitting the scale to the bug. But every user with an A-grade team is about to have a B, which
is the kind of change worth being deliberate about.

---

### 🔀 Alternatives Considered

- **Leave it.** Rejected: it is wrong, it is visible on the differentiator feature, and a user found it.
- **Unrank a fully-tied pool** (return `None` when every peer is identical). Considered, and a real option — it
  is arguably the most honest answer, since a percentile over identical values carries no information. Rejected
  as the *primary* fix because it only helps the fully-tied case (exactly one axis today: GK set pieces) and
  does nothing for the heavily-but-not-fully tied pools that produce the 96th-percentile keeper. Midrank/rank-pct
  handles both. Worth revisiting as a refinement if a 50 on a meaningless axis proves confusing.
- **Special-case goalkeepers** (drop Goal Threat / Set Pieces from a GK radar). Rejected: it treats one symptom
  of a general bug, and the general bug affects every position wherever values bunch.
- **Re-tune the grade thresholds to preserve today's letters.** Available as a sub-decision above; rejected as a
  default because it fits the scale to the defect.

---

### 🧭 Consequences

**Positive** — a tie stops reading as a triumph; the maths matches the standard definition of a percentile, so
it can be explained to a user in one sentence; the fix lives in one shared function instead of two divergent
copies; genuine elites are untouched, so nothing that was right becomes wrong.

**Negative / risks (mitigations)** — 9 of 20 team grades drop a letter (*mitigation:* the ordering is unchanged
and the old values were inflated; the alternative is fitting thresholds to a bug — but it is a visible change
and it is the owner's call); ~50% of player percentiles and a third of sampled insight strings change
(*mitigation:* almost all by one point; the wording flips only at the 85 boundary, where the two labels are
adjacent by design); a fully-tied axis now reads 50, which is honest but may still look odd on a keeper's set
pieces (*mitigation:* the "unrank a tied pool" refinement above stays available).

---

### 🧾 Status & follow-ups

- **Accepted and built (Sprint 178).** `analytics/ranking.py::percentile_rank` — one function, imported by both
  `player_dna._percentile` and `team_dna._rank`, which are now thin aliases keeping their local names. 15 new
  tests + 4 existing DNA tests updated to the new semantics. 1155 → **1170**, ruff clean.
- **One thing the build added beyond the plan.** `value` need not be a member of `values` — Player DNA ranks a
  below-the-floor target against a floored pool — and on a small pool the arithmetic can fall *below zero*
  (`pr(-5, [1, 2])` computes −50 before clamping). The result is clamped into 0-100 rather than trusted to land
  there, with a test for it.
- **The resulting team-grade distribution** (early season, so several axes are still degraded): **A 2 · B 4 ·
  C 7 · D 7**. BHA A(84) and BRE A(73) lead; ARS B(67), MCI B(69), LIV B(70). Re-tuning the 85/72/58/42
  thresholds remains available as a separate small change if that skew reads too harshly once real data accrues.
- **Not this ADR:** the "unrank a fully-tied pool" refinement; whether `Squad Depth` should be unranked early
  season (it reads 0 for all 20 teams right now — an ADR-126-shaped problem, currently masked and about to
  become visible as a flat 50 across the league).
