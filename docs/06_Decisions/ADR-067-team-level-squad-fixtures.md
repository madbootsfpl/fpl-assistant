# Architectural Decision Record: Team-level squad fixtures

**Decision ID:** ADR-067
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** implements the **alternative lens deferred in ADR-049** (squad-scoped fixtures
by team, not by player). Reuses `team_fdr` (ADR-004/005). No new analytics.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The `fixtures` ask/chat intent (ADR-048/049) has three modes: a league FDR ranking, a single team's
schedule, and a **squad's players** ranked by their team's fixture run. ADR-049 deferred a fourth: ranking a
squad's **teams** (with player-counts) rather than one row per player — useful for "which of my clubs have
the good/bad runs?".

**Verified on real data (2026-08-06):** grouping the demo squad's owned players by team and joining
`team_fdr` produces the lens directly — Demo XI = 15 players across 12 teams, ranked easiest-first with a
player-count + next opponents per team (`LIV ×1 avgFDR 2.6`, `CRY ×2 avgFDR 3.0`, …).

#### Decision Drivers
- **Reuse** — it's the by-team grouping of the existing squad-scoped data; `team_fdr` already gives the FDR.
- **Grounded + verified** — analytics decide; the LLM narrates; figures trace to the facts (ADR-037).
- **Don't disturb** the existing player-level view or the other fixtures modes.

---

### ✅ Decision

**1. A team-level squad-fixtures mode.** `_decide_squad_team_fixtures(store, squad, upcoming, horizon,
hardest, active_squad)`: load the squad (session-aware), drop departed ids, group the owned players by
`team` (a player-count + names), join `team_fdr`, and rank the distinct teams by `avg_difficulty` (easiest
default; hardest on the existing cue). Facts = the ranked teams with counts + opponents; subjects = the team
codes. Degrades (no current players / no FDR) exactly like its player-level sibling.

**2. Cue-based routing.** Inside `_decide_fixtures`'s squad-scoped branch (`not match and squad`), a
**"teams" / "clubs" / "by team" / "by club"** cue selects the team-level view; otherwise the player-level
view (today's default). A possessive "my team's players" does **not** false-trigger (no `teams`/`by team`).

**3. A dedicated renderer.** `ui/fixtures.py` `render_squad_team_fixtures(rows, squad, next_n, hardest)` — a
small fixed-width table (`Team · #Players · Avg FDR · Next opponents`), mirroring `render_squad_fixtures`'s
style. Its own shape (per team), so a small renderer rather than reusing the per-player one.

---

### 🔀 Alternatives Considered

- **Fold into `_decide_squad_fixtures` with a flag.** Rejected — the row shape + renderer differ (per team
  vs per player); a sibling handler is clearer than branching one.
- **A separate intent.** Rejected — it's the same `fixtures` intent, just a different squad lens; a cue
  within the squad branch keeps routing simple.
- **Trigger on bare "team".** Rejected — "my team's players" contains "team"; require the plural/`by team`
  form so the player-level phrasing stays player-level.

---

### 🧭 Consequences

**Positive**
- Answers "which of \<squad>'s teams have the best/worst fixtures?" — the ADR-049 deferral, closed.
- Reuses `team_fdr`; grounded + verified; works in `ask` + `chat` (and the web Ask tab).
- The player-level view + other fixtures modes are untouched.

**Negative / risks (mitigations)**
- **Cue ambiguity** ("team" vs "teams") → require `teams`/`clubs`/`by team`/`by club`; a routing test pins
  team-level vs player-level.
- **A squad with departed/■ players** → same degrade path as the sibling (drop departed; message if none).

---

### 📊 Validation

Probed live: the by-team grouping + `team_fdr` join yields the ranked-teams lens with player-counts.
Acceptance: `_decide_squad_team_fixtures` groups + counts + ranks (easiest/hardest) and degrades on an
empty/absent squad; the `teams`/`by team` cue routes to it while `…players…` stays player-level; the new
renderer prints Team · #Players · Avg FDR · opponents; grounding holds; the player-level view + other modes
are unchanged; the existing 581 tests stay green.
