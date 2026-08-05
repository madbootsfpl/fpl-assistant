# Architectural Decision Record: Squad-scoped fixtures — rank your players by their fixture run

**Decision ID:** ADR-049
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Adds a third mode to the `fixtures` intent (ADR-048); reuses `team_fdr`
(ADR-004/005); grounded per ADR-037; works in `chat` (ADR-047) via the shared `_dispatch`.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The `fixtures` intent (ADR-048) answers a league FDR ranking and a single team's schedule, but not the
squad-relative question a manager actually asks: *"which of my players have good fixtures?"* — whose runs
are kind, and whose are hard. Deferred from Sprint 048; this closes it as a **third mode**.

#### A planning probe pinned the mode and surfaced a routing bug
- **A saved squad maps to a fixture view with no new analytics.** TS's 15 players cover 11 teams; joining
  each player to its team's FDR (next 5) and ranking gives, per player: *Virgil/Szoboszlai (LIV) 2.6 …
  Truffert (BOU) 3.6 · Kusi-Asare (FUL) 3.6*. The mode is a **join** (player → its team's FDR) **+ a
  sort** — a filter/join over an existing engine.
- **A routing bug the gate caught:** *"which of **TS's** players…"* routed with **squad `None`** — the
  possessive "TS's" is a single token, so `_squad_name` (whitespace split) never matched "TS". The most
  natural phrasing silently fell back to the league ranking. **`_squad_name` must be possessive-aware.**

#### Decision Drivers
- **Answer the squad-relative question** — the fixtures view a manager reads before a transfer/captain.
- **Reuse** — the league FDR + the routing/dispatch already exist; this is a join + a small renderer.
- **Same discipline** — grounded facts + the ADR-037 verifier; works in `ask` and `chat`.
- **No wrong routing** — the possessive must resolve, and the mode needs a named squad.

---

### ✅ Decision

**1. A third mode of `fixtures`, chosen by precedence.** In `_decide_fixtures`: a **specific team** named
→ its schedule (ADR-048); else a **saved squad** named → the squad-scoped ranking; else → the league
ranking. Squad names ("TS", "RoboTS") never collide with team codes/names.

**2. The lens — player-level (owner's call).** Rank the squad's **players**, one row each, by **their
team's** upcoming fixture difficulty (`team_fdr`), **easiest by default**, **hardest** on a
hard/tough/avoid cue. Each row shows **Player · Team · Avg FDR · Next opponents**. (Team-level with
counts was the alternative; the owner chose the per-player view — it names the players directly, which is
what a manager scans.)

**3. `_squad_name` becomes possessive-aware.** Strip a trailing `'s`/`’s` (and surrounding apostrophes)
when tokenising, so *"TS's fixtures"* resolves to **TS**. A general fix — it also helps *"TS's captain"*
etc.

**4. A small renderer.** `render_squad_fixtures(rows, squad, next_n, source, hardest)` — Player / Team /
Avg FDR / Next opponents; easiest default, hardest footer on a cue. A dedicated render (its own shape),
not a bent player table.

**5. Needs a named squad; horizon; source.** No named squad → the league ranking (a fine answer, not a
forced prompt). A squad naming only departed players / an unknown squad → a clear message. "next N"
parsed (default 5); FPL difficulty (ClubElo deferred).

**6. Surfaces.** `ask` + `chat` — `_dispatch` already threads the routed `squad` to `_decide_fixtures`;
grounded facts (players + their team + avg difficulty + opponents) + the verifier every turn.

---

### 🔀 Alternatives Considered

- **Team-level with player-counts** (rank the squad's *teams*, show ×N players). Concise, but the owner
  chose the per-player view — it names the players a manager acts on, even if it overlaps `analyse` a
  little (this stays a *fixtures* lens — team FDR — not per-player xP).
- **Prompt when no squad is named** (*"which of my players…"* with no name). Deferred — a league ranking
  is a reasonable fallback; a "name a squad" nudge is a later nicety.
- **Per-player xP × fixtures.** Out of scope — that's `analyse`'s job; this is the fixtures difficulty
  lens.
- **The custom (ClubElo) source in `ask`.** Still deferred (intermittent; keep the NL layer simple).

---

### 🧭 Consequences

**Positive**
- `ask`/`chat` answer *"which of my players have good fixtures?"* — a per-player, squad-relative view,
  reusing the league FDR with only a join + a small renderer.
- Fixing `_squad_name` for the possessive helps every squad-scoped intent, not just this one.
- Grounded + verified; works in both surfaces with no new dispatch wiring.

**Negative / risks (mitigations)**
- **Precedence confusion (team vs squad vs league)** → a clear order (team → squad → league); tests pin
  each.
- **Overlap with `analyse`** → this is a fixtures/FDR lens (team difficulty per player), not xP; `analyse`
  stays the health tool.
- **Departed players / unknown squad** → filter to current players; empty → a message.

---

### 📊 Validation

Prototyped on the live DB: TS's 15 players rank *Virgil/Szoboszlai (LIV) 2.6 … Truffert (BOU)/Kusi-Asare
(FUL) 3.6*, straight from `team_fdr` joined per player. The routing probe caught the possessive bug
(*"TS's"* → squad None) — fixed by a possessive-aware `_squad_name`. Acceptance for the sprint: `ask
"which of TS's players have the best fixtures?"` ranks the squad's players by their fixture run (and in
`chat`), with the ✓/⚠ trust line; a named team still returns its schedule; no squad still gives the
league ranking.
