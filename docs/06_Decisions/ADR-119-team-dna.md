# Architectural Decision Record: Team DNA — a team-level analysis companion

**Decision ID:** ADR-119
**Date:** 2026-08-18
**Status:** Accepted — owner-approved from a real-data preview (`scratchpad/team_dna_gen.py` → Artifact). Build =
a lean sprint (slots around Player-DNA tester feedback + the GW1 runbook).
**Superseded By / Replaces:** A team-level companion to **Player DNA (ADR-118)** — reuses its whole engine
(percentile-in-a-pool ranking, the server-built SVG radar, the verdict heuristic, the grounded insights). Reads the
same player rows + fixtures; **complements** the Fixtures ticker / FDR (ADR-049) and the 🎯 Radar (ADR-107) rather
than replacing them. Does **not** touch `decision_xp` (ADR-041) or the FDR model.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner idea (2026-08-18), the morning after Player DNA shipped: a **Team DNA** — the same "fingerprint" treatment for
a *club*. FPL decisions are team-driven (which attacks to buy into, which defences for clean sheets, whose fixtures
turn), yet the app has no single **team-strength** view — and **defence / clean-sheet picking is underserved**.

The question was **"does it add enough value, given Fixtures + Radar already exist?"** A real-data preview (Liverpool
& Arsenal from our aggregates + a My-Squad "Your teams" strip) answered it: the **squad-scoped "Your teams" strip**
is genuinely new and actionable; the full browse card's *new* value is the **defensive / whole-team** picture (its
fixtures + target-players overlap what we ship). Owner approved the direction ("good call" · "excellent").

#### Decision Drivers
- **Cheap** — reuses the entire DNA engine built S168–S171; the marginal cost is small.
- **Fills the real gap** — team defence / clean-sheet strength + a one-glance whole-team read.
- **Actionable where it's yours** — a health check on the teams behind *your* squad = a transfer signal.
- **No tab bloat** (owner steer, standing) + **don't duplicate** Fixtures/Radar.
- **Honest** — build on data we hold (with labelled proxies); defer event-data viz; don't fake it.

---

### ✅ Decision *(owner-approved: lead with the My-Squad "Your teams" strip; full card under Fixtures; defence-led)*

**1. One component, two doorways (no new tab).**
- **Fixtures ▸ 🧬 Team DNA** — pick *any* team → the **full card**: the 8-axis radar + an **AI Verdict grade** + a
  grounded **Insight** + **next-N fixtures** + a **Key-players-to-target** table (links to the Player DNA we built).
- **My Squad ▸ Health ▸ "Your teams" strip** — scoped to the clubs *you own players in*: one compact row per club
  (a **grade** + **Attack / Defence / Fixture** dots + **your players** there) that **drills into** the Fixtures
  card. **This is the lead** — the standout, actionable half.

**2. The engine (`analytics/team_dna.py`, pure — mirrors `player_dna`).** Aggregate the player pool + fixtures to
per-team metrics, then rank each as a **percentile across the 20 PL teams**. The **8 axes** (owner's), on data we
hold via labelled proxies:

| Axis | Metric (what we hold) |
|---|---|
| Attacking Threat | team xG (Σ players' xg) |
| Chance Creation | team xA (Σ players' xa) |
| Defensive Strength | team xGA (the keeper's xGC — a clean proxy; lower = better) |
| Clean-Sheet Potential | a blend of defence + fixture-ease (both drive clean sheets) |
| Fixture Strength | next-5 FDR (lower = better) |
| Set-Piece Threat | Σ the team's set-piece takers' involvement |
| FPL Output | team total points |
| Squad Depth | count of regulars (minutes ≥ threshold) |

**Works preseason** on last-season aggregates (same basis as Player DNA). Plus a team **verdict grade** (A+…D from
the key axes) + grounded **insights** (elite axes, the fixture swing, a miserly-defence note, set-piece load).

**3. Build tiers.**
- 🟢 **Now:** the radar · grade/verdict · insights · next-N fixtures · key-players table · the "Your teams" strip.
- 🟡 **From GW1:** *real* clean-sheet rate (vs the fixture-blend proxy) · team **form** (points / xPTS per GW).
- 🔴 **Not v1 (event data — a future `soccerdata` ADR):** the attacking/defensive **metric bars** (shots, big
  chances, shots-in-box, touches, possession, shots-conceded) · the **attacking-zones heatmap** · the **shot map**.

**4. Reuse.** The percentile ranking, the SVG radar, the band colours, the verdict-gauge and insights renderers all
come from ADR-118 — Team DNA generalises them; it does **not** re-invent them.

**What this is *not*.** Not a new tab. Not an event-data dashboard (v1). Not a change to `decision_xp`, the FDR
model, or the Radar algorithm — it's a display lens that **composes** existing signals.

---

### 🔀 Alternatives Considered

- **A full browse-only Team DNA (no My-Squad strip).** Rejected — the strip is the standout value; browse-only
  leans too much on what Fixtures/Radar already do.
- **The whole mockup incl. metric bars / zones / shot map.** Rejected for v1 — those need Opta/Understat event data
  (ADR-016); bundling them would delay the feature or force proxies-dressed-as-real (breaks the brand).
- **A new top-level "Teams" tab.** Rejected (owner steer) — too many tabs; it belongs with Fixtures (team-centric)
  + My Squad (your teams).
- **Park it entirely.** Considered (pending Player-DNA tester feedback) — but the preview cost ≈ nil and the
  direction is clear, so gate now and time the *build* around feedback + GW1.

---

### 🧭 Consequences

**Positive** — a genuinely new team-strength lens (esp. defence/clean-sheets) + a scoped squad health-check /
transfer signal; near-free via DNA reuse; a nice through-line (Team DNA → its players to target → their Player DNA);
works preseason.
**Negative / risks (mitigations)** — proxy axes (xGA via keeper xGC; CS-potential blend; depth = regular count)
(*mitigation:* label them; upgrade the 🟡 ones at GW1); overlap with Fixtures/Radar (*mitigation:* lead with the
strip + the defensive angle; **link** to Radar, don't duplicate); another surface to keep honest (*mitigation:*
grounded-only, no event-data fakes).

---

### 🧾 Status & follow-ups

- **Accepted.** Build (a lean sprint — plan next): `analytics/team_dna.py` (the pure engine + grade + insights);
  a `team_dna_card` renderer (reusing the DNA radar/verdict/insights); the **Fixtures ▸ Team DNA** browse view; the
  **My Squad ▸ Health "Your teams" strip** drilling into it; the 3-part DoD (tests + smoke + docs).
- **Not this ADR / follow-ups:** 🟡 real clean-sheet rate + team form at GW1; the 🔴 event-data viz (metric bars /
  zones / shot map) → a future gated `soccerdata` ADR; possibly tinting the radar by team colour.
