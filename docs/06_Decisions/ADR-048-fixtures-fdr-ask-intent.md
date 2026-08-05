# Architectural Decision Record: A fixtures / FDR `ask` intent

**Decision ID:** ADR-048
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Adds an eighth intent to `ask` (ADR-034); reuses the FDR analytics
(ADR-004/005 `team_fdr`, `team_schedule`) and their renderers; grounded per ADR-037; works in the
conversational `chat` (ADR-047) via the shared dispatch.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

A routing probe over Sprint 047 showed that **every fixtures question falls straight through to the help
message** — *"who has the best fixtures over the next 5?"*, *"when does Arsenal play?"*, *"who does Man
City play?"* — even though the fixtures analytics have existed since Sprint 003–004. `ask` can talk about
captains, transfers, squads and players, but not the fixtures that drive all of them. It's the single
biggest visible gap, and closing it is **pure Phase-4 wiring** — no new analytics.

#### A planning probe pinned the analytics, the renderers, and team resolution
- **Both engines are grounded and ready.** `team_fdr(upcoming, next_n=5, source="fpl")` ranks the league
  (easiest *LIV 2.6 · TOT 2.8 · MUN 2.8*; hardest *BOU/FUL 3.6*), each row carrying `avg_difficulty` +
  the `opponents` list; `team_schedule(upcoming, "ARS")` gives *GW1 COV (H) diff 2, GW2 AVL (A) diff 4…*.
- **The renderers exist** — `render_fdr_table` and `render_team_fixtures` — so the `ask` `detail` table
  is a reuse (like the transfer plan / shortlist).
- **A clean routing slot** — every fixtures phrasing routes to None today, so a `fixtures` intent
  collides with nothing.
- **Team names resolve** — a full `name` + a `short_name` (ARS/MCI/TOT); a few colloquial (*Spurs*=TOT,
  *Man City*=MCI, *Man Utd*=MUN) need a small alias set. The only genuinely ambiguous bare token
  (*"City"* — Man/Hull/Coventry) safely resolves to **nothing** (full-name matching needs the real full
  name present), so we never guess.

#### Decision Drivers
- **Close the biggest gap** with the least new code — reuse the analytics + renderers.
- **Grounded, deterministic, optional-LLM** — the same `ask` discipline (ADR-034/037).
- **Never a wrong guess** on a team name (the `compare` lesson, ADR-039).
- **Simple** — FPL difficulty by default; ClubElo stays out of the NL layer.

---

### ✅ Decision

**1. One `fixtures` intent, two modes.**
- **Team named → its schedule.** Resolve the team, call `team_schedule(upcoming, code, source="fpl")`,
  render with `render_team_fixtures` as the `detail`; facts humanise venue (H/A → home/away) + difficulty.
- **No team → the league FDR ranking.** `team_fdr(upcoming, next_n=N, source="fpl")`, rendered with
  `render_fdr_table`; **easiest by default**, **hardest** when the question says *hard/tough/avoid/worst*.

**2. Team resolution — `_match_team(question, teams)`.** Match on the full `name`, the `short_name` (a
whole word), and a small alias set (*Tottenham/Spurs*→TOT, *Man United/Man Utd/Manchester United*→MUN,
*Manchester City/Man City*→MCI, *Forest*→NFO). **Zero matches** → no team → the FDR-ranking mode (or a
"couldn't find that team" message when a team was clearly intended). **≥2 matches** → a clear "which
team?" message. Never a silent wrong guess.

**3. Horizon + source.** Parse "next N" (default 5); **FPL difficulty only** — the `custom` (ClubElo)
source is deferred (intermittent, and it keeps the NL layer simple).

**4. Surfaces.** Wired through the shared `_dispatch`, so it works in **both** `ask` and `chat`;
grounded facts + the ADR-037 verifier run every turn. Fixtures has **no `next`-offset follow-up** (it
isn't a ranked-pick list) — a fresh fixtures turn in `chat` simply works.

**5. Scope — two modes only (owner's call).** **Squad-scoped fixtures** (*"which of my players have the
best fixtures?"*) is **deferred** — it's more work (squad → player teams → filtered FDR + a new render)
and overlaps the existing `analyse`. The two league/team modes ship this sprint.

---

### 🔀 Alternatives Considered

- **Squad-scoped fixtures now.** Deferred by the owner — useful, but more code and it overlaps `analyse`;
  the two clean modes are the high-value core.
- **Expose the custom (ClubElo) difficulty in `ask`.** Rejected for now — ClubElo is intermittent and the
  NL layer stays simple; the `fdr`/`fixtures` CLI commands already offer `--type custom` for power users.
- **Full fuzzy team matching / every nickname.** Rejected — a pragmatic name/code/alias set is enough;
  ambiguity/none returns a message rather than a guess.
- **A `next` follow-up for fixtures in `chat`.** Not applicable — fixtures isn't a ranked-pick list, so
  there's no natural "and the next?".

---

### 🧭 Consequences

**Positive**
- `ask`/`chat` can finally answer the fixtures questions that underpin every other decision — with no new
  analytics, reusing the existing engines *and* renderers.
- Grounded + verified like every other intent; degrades to the decision + facts without the LLM.
- Team resolution never guesses — ambiguity/none is a clear message.

**Negative / risks (mitigations)**
- **Team mis-resolution** → name/code/alias matching; ambiguity/none → a message (the `compare` lesson).
- **"best fixtures" ambiguity (easiest vs hardest)** → default easiest (who to target); *hard/tough/avoid*
  → the hard end; the header states which.
- **Squad-scoped gap** → deferred deliberately; the league/team modes cover the common questions.

---

### 📊 Validation

Prototyped on the live DB: `team_fdr` ranks the league (LIV 2.6 easiest … FUL/BOU 3.6 hardest);
`team_schedule("ARS")` returns GW1 COV (H) … ; a candidate `_match_team` resolves Arsenal/Man City/Man
Utd/Tottenham/Spurs/Forest and safely returns nothing for the ambiguous bare *"City"* and the
out-of-league *"Wolves"*. Acceptance for the sprint: `ask "who has the best fixtures over the next 5?"`
and `ask "when does Arsenal play?"` answer correctly, in both `ask` and `chat`, each with the ✓/⚠ trust
line.
