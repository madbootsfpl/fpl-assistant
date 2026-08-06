# Backlog

Captured ideas not yet scheduled into a sprint. *(The larger unbuilt features live in the
consolidated [Roadmap](04_Roadmap/Roadmap.md) — "Next / Then / Later"; this file holds the small
nice-to-haves and tech-debt.)*

## Enhancements

- ~~**Differential archetype**~~ — **DONE** (Sprint 043, **ADR-044**). Ingested `selected_by` and added a
  `min_differentials` constraint (≤5% owned — pinned so it bites); `squad --full --differential N` +
  NL "… with N differentials". Completes the archetype trio (low-cost / premium / differential).

- **Bench order** — which bench player subs on first (Sprint 012 sequel).
- **Availability flags in the ranking views** — surface injury/suspension flags in
  `table`/`xg`/etc. the way `squad` does (Sprint 022 sequel).
- **Ceiling / "differential" captaincy** — `captain` (Sprint 027, ADR-029) ranks by *mean* xP,
  which favours nailed-on premiums. A ceiling/variance view would surface high-upside punts — but
  it needs variance/form data we don't have yet. Revisit once in-season data accrues.
- **Multi-move transfer *planner*** — ◑ *partly done.* A **coordinated greedy plan** shipped (Sprint 033,
  **ADR-035**: `transfer --count N`, shared bank, no repeats) and it now ranks by **XI improvement**
  (Sprint 046, ADR-046). Still open: the **−4-hit vs roll / banking** maths and chip-aware sequencing —
  a bigger optimisation (wants the real bank + xMins) → Roadmap *Later*.
- **Differentials / value `ask` intent** — extend the shortlist with ownership + points-per-£m lenses
  ("best differentials", "is X worth the money?"). Reuses `selected_by` (ADR-044) + value; overlaps the
  existing shortlist a little. A live Phase-4 option.
- **Persisted / pronoun-aware chat** — `chat` (Sprint 047, ADR-047) holds the last turn in memory only.
  A later step: resolve pronouns ("is **he** worth captaining?") and/or persist context across runs.
- **Team-level squad-fixtures view** — the alternative lens deferred at Sprint 049 (ADR-049): rank a
  squad's **teams** (with player-counts) rather than one row per player. A small option on the existing
  squad-scoped fixtures mode.

### Web UI ideas (from the Sprint 054 review — owner's notes)

- ~~**Home tab + full landing**~~ — **DONE** (Sprint 059). The Streamlit landing is **Home** and lists
  every page.
- ~~**Team badges + player photos**~~ — **DONE** (Sprint 059). `team.code` ingested → badges; player
  photos via `code`; shown across Players / Fixtures / the squad tabs (shared `badges` helper +
  `st.column_config.ImageColumn`).
- ~~**Deploy & share**~~ — **DONE** (Sprint 053, **ADR-053**). Deployed on **Streamlit Community Cloud**,
  public + read-only; a committed `data/seed.db` + `seed_squads.json` seed it; Ollama absent → degrades to
  decision + facts. Runbook: `docs/DEPLOY.md`. *(A custom domain via CNAME remains an optional extra.)*

- ~~**Crowd & Sentiment Signals (Phase 6) — Tier 1 & 2**~~ — **DONE** (Sprints 060–068). A *lens, not a
  rewrite of xP* (a test asserts `decision_xp` is untouched). **Tier 1** (ADR-057): ingested
  `transfers_in/out_event` · `cost_change_*` · `form` · `ict_index` (+ components) · `value_form`; crowd
  **flags** on Players/Build/Analyse/My Squad/Captain/Transfer; a **"trends"** `ask` intent + a **Trending**
  page. **Tier 2** (ADR-058/059): an FPL **news lens**, **manager-ID import**, and **Community Signals**
  (Reddit RSS buzz). **Tier 3** (backtest crowd-follow vs xP-only) + **keyed** Reddit/pundit sentiment
  remain open → Roadmap *Phase 6 / Later*. Momentum/form boards light up at **GW1 (2026-08-21)**.

- **Cloud squads — server-side persistence (Path 2)** — the seamless upgrade to Sprint 057's
  download/upload squads: a **"Save as `<name>` / Load `<name>`"** backed by a free external DB (e.g.
  Supabase/Postgres via `st.connection`) + a secret in Streamlit; persistent across sessions/devices, no
  files to manage. *Needs:* an external DB account, a secret, a persistence adapter, and the first
  server-side writes; optionally light per-user identity later. Revisit once download/upload friction
  proves it's worth it.

### Done (kept for the trail)

- ~~Include / exclude players~~ — **DONE** (Sprint 008, ADR-009).
- ~~`xp`/`squad` objective toggle~~ — **DONE** (Sprint 010, ADR-011).
- ~~Full 15-man squad~~ — **DONE** (Sprint 011, `squad --full`, ADR-012).
- ~~Declared bench~~ — **DONE** (Sprint 012, `squad --bench`, ADR-013).
- ~~Flexible formations~~ — **DONE** (Sprint 013, `squad --formation` + flexible default,
  ADR-014). Ranges (DEF 3–5, MID 2–5, FWD 1–3); the bench-implied shape shown in `--full`.
- ~~Validate a declared bench yields a legal XI~~ — **DONE** (Sprint 021, `legal_xi_issues`,
  ADR-022). Warns (not blocks) when a full 4-man bench leaves an illegal XI; reuses `XI_FLEX`.
- ~~Saved / persistent squad~~ — **DONE** (Sprint 023, `squad --save`/`--load`, ADR-024).
  User state in `data/squads.json` (gitignored), separate from the FPL cache; reload re-prices +
  flags injuries + notes departures.
- ~~`xp` per-gameweek breakdown~~ — **DONE** (Sprint 030, ADR-032). A `by_gameweek` breakdown on
  `player_xp` (a faithful decomposition of the total); shown in `analyse` and `xp --by-gameweek`,
  plus `analyse --sort xp`. (From Tony's Sprint 006 reflection.)

## Expected minutes (xMins) — the owner's Sprint-35 request

*Predicting playing time is often harder than predicting performance.* Rotation/minutes is the single
biggest source of FPL variance, and "assumes they play" is the recurring caveat in
`captain`/`transfer`/`analyse`. **Value: very high.** Assessed in Sprint 036 (US-108); recommended in
**two steps** so most of the value lands early, the heavy modelling waits for data.

- ~~**xMins v0 — lightweight, FPL-native, no ML *(near-term, Phase 3)*.**~~ **DONE** (Sprint 037,
  **ADR-038**). `availability_weight = chance_factor × recency-weighted minutes share` (**minutes-only**
  — the planning probe proved `starts` is unreliable pre-2022/23, correcting the original "minutes/starts
  ratio" sketch). Weights xP by expected minutes **default-on** at the decision edge
  (captain/transfer/analyse/`ask`), shown as **expected minutes** with a **`--no-xmins`** opt-out; the
  raw `xp` view stays pure. Backfill broadened 29% → 87%. *Honest limits (→ Phase 5):* role change +
  coverage. It's an estimate from chance% + history, **not** the full probabilistic model.
- **Full probabilistic xMins — the ML model *(later, dedicated phase — Roadmap Phase 5)*.** A trained
  model producing per-fixture expected-minutes *probabilities* from schedule density (hours between
  kickoffs), European-match congestion, historical manager rotation profiles, and substitution
  tendencies. **Needs:** in-season per-GW minutes to train (post-GW1, ties to Data Hardening), external
  European-fixture data (not in the FPL API), and a genuine ML effort. Gated on data → a later phase.

**Placement:** v0 as a near-term Phase 3 enhancement (immediately improves every recommendation); the
ML model as a later Phase 5 item (post-GW1). It's the highest-value deferred item — worth doing
properly, lightweight first. *(This supersedes the terse "Richer xP: … expected minutes" line under
Deferred below.)*

## Validated, deferred

- **soccerdata / npXG** — evaluated in Sprint 015 ([ADR-016](06_Decisions/ADR-016-soccerdata-evaluation.md)).
  Matching works (~95% FPL↔Understat) and npXG is real, **but** the value is narrow
  (penalties score points in FPL, so penalty-inclusive xG is the relevant signal) and the
  cost is high (14 → 72 packages incl. a selenium/pandas stack, scraping fragility, a
  season-alignment trap). **Deferred.** Revisit only if a decision-driving need appears
  that FPL can't meet — and prefer a *lightweight* direct Understat fetch over the full
  library. Evidence: `spikes/015-soccerdata/`.

## Tech debt

- **Migrate to the PuLP 4.0 API** — use `prob.add_variable(...)` / `COIN_CMD` instead of
  `LpVariable(...)` / `PULP_CBC_CMD` (currently the 4.0 deprecation notices are
  scope-suppressed in `src/analytics/optimizer.py`).
- **Shared *squad* renderer** — `render_squad` / `render_loaded_squad` still duplicate a little
  row logic. The ranking views were unified in Sprint 024 (`ui/_table.py`), but the squad views
  are a different shape (position groups, bench, markers) and were left out — fold them in later.
- ~~Shared table renderer for the ranking views~~ — **DONE** (Sprint 024, `ui/_table.py`
  `Col` + `render_rows`, ADR-025). Five near-duplicate renderers → one; output byte-identical.

## Deferred (data-dependent — need season-start data)

- Richer xP: recent `form` + expected minutes (xMins — now assessed in its own section above).
- Attack/Defence FDR split (needs `strength_attack_*` / `strength_defence_*`).
- ~~**Per-GW history ingestion**~~ — **DONE (wired, dormant)** (Sprint 069, US-196, **ADR-060**). A
  `player_history` table filled by the *existing* `element-summary` backfill (the one call already carries
  `history`); empty preseason → live at GW1. Still open: a `history <player>` season-trend / rolling-form
  **view** over the new per-GW data.
- ~~**In-season form blend into xP**~~ — **DONE (wired, dormant)** (Sprint 069, US-197, ADR-060). A
  rolling-**pp90** form term in the one `decision_xp` recipe behind `FORM_WEIGHT = 0`. Still open at GW1:
  set the weight + **calibrate** the weight/window on real form.
- **Data Hardening — the GW1 flip + calibration** — prep is done (per-GW ingest + form blend, wired dormant,
  Sprint 069). At **GW1 (2026-08-21):** `history --backfill` (now also per-GW) + raise `FORM_WEIGHT` +
  calibrate; then the crowd/form-vs-xP **backtest** (Tier 3). The full 567-player backfill can ride any time.
