# MADBOOTS Roadmap

*Consolidated 2026-08-05 (Sprint 050) into a single forward-looking page; kept current through Sprint 068.
Phase 1 was delivered as a **CLI** (ADR-002/003), not the original web-first plan; that original 5-phase
plan and its bullet-by-bullet reconciliation live in git history and the per-sprint docs — this page looks
**forward**.*

**Where we are:** a mature CLI FPL assistant — an analytics + optimisation core, a decision-support suite,
and a grounded natural-language layer (`ask` + `chat`) — now with a **deployed read-only Streamlit web UI**
and a **Crowd & Community Signals** layer (trends · flags · an FPL news lens · manager-ID import · Reddit
buzz), plus a grounded **"this week" gameweek recommendation** (captain · lineup · a transfer · flags —
ADR-070; the **AI Tips** tab) and **casual-readable stat boards** (a relative 🟢…🔴 quality rating —
ADR-071/073; consistently formatted numbers — ADR-072; **🚑 availability flags** in every player table —
ADR-074, incl. the CLI ranking tables + a chance% on ❓; a **projected-XI score + formation comparison** on
Build — ADR-075; a **configurable prediction horizon** across the Squads tab — ADR-077; a **My Squad quick-stats summary** +
a **bench order** you can see, **set**, and that starts sensibly — ADR-078/079; a **pronoun-aware**,
follow-up-capable chat in the browser — ADR-080). **80 ADRs · 640 tests · CI green.** Preseason (0
gameweeks; **GW1 deadline 2026-08-21**), so
form/per-GW insight — and the momentum boards — are still ahead, but the **Data Hardening plumbing is now
wired dormant** (Sprint 069): GW1 is a switch-flip.

**Status legend:** ✅ Done · ◑ Partial · ⬜ Not started

---

## ✅ Delivered

### Analytics & optimisation core (the CLI engine)
- **Data:** FPL API client (`bootstrap-static`, `fixtures`, `element-summary`) + SQLite cache (upsert,
  generic migrations). FPL is the source of truth; ClubElo is a best-effort second source that degrades
  gracefully (retry-then-degrade, importance-scaled). Past-season history backfill.
- **Analytics:** custom FDR (overall + ClubElo Elo), Points-per-£m value, **Expected Points (xP)** over a
  multi-week horizon, xG/xA/xGI/xGC, over/under-performance, Defensive Contribution, clean-sheet solidity.
- **One xP metric (ADR-041):** the optimiser and the decision layer share a single `decision_xp` recipe
  (baseline + a sane low-evidence fallback + xMins) — so a squad built on xP has no phantom free transfers.
- **Expected minutes (xMins) v0 (ADR-038):** `chance%` × a recency-weighted historical minutes share
  weights xP **default-on** at every decision edge; shown as expected minutes; `--no-xmins` opts out.
- **Optimisation:** an ILP squad selector (PuLP) — best XI or full 15, flexible formations, declared
  bench, include/exclude, pluggable objective; **archetypes** (`--cheap`/`--premium`/`--differential`,
  ADR-043/044) and **bench-aware** builds (`--weekly`/`--bench-boost`, ADR-045).
- **User state:** saved / reloadable squads (re-priced, with current injuries + departures).

### Decision support
- **`captain`** (ADR-029) — top picks by next-GW xP; opponent, venue, penalty duty.
- **`transfer`** (ADR-030) — best single legal upgrades, **ranked by XI improvement** (XI-gain via
  `best_xi_points`, ADR-046; `--raw` for the old ranking); a coordinated multi-move **plan** (`--count`,
  ADR-035).
- **`analyse`** (ADR-031) — projected XI xP over N GW (per-GW breakdown, ADR-032), weak links, injuries.
- **gameweek plan** (ADR-070) — a grounded **"this week"** recommendation for a squad: who to **captain**,
  any **lineup** change, one **transfer** to consider, and **flagged** players — an *assembler* over the
  above primitives (no new analytics), narrated + verified; an `ask`/`chat` intent + a **Squads → This
  week** web view.

### Natural-language layer (grounded)
- **`ask`** — eight intents (captain · transfer · analyse · start/bench · compare · build-a-squad ·
  best-players · **fixtures**), all **analytics-decide, LLM-narrates**, every answer **verified** against
  the data (✓/⚠ trust line, ADR-037). The LLM (local Ollama) is optional — degrades to decision + facts.
- **`chat`** (ADR-047) — a conversational mode where follow-ups build on the last turn (why / next /
  what-about), still analytics-decided each turn.
- ✅ **AI Chat Assistant** (Sprint 100, ADR-085) — the Ask tab also answers **FPL rules** from a curated
  knowledge base (`src/fpl_rules.py`, **verified ✓**) and open **tactics** questions free-form, clearly
  labelled **ℹ not verified** (never a specific pick). Grounded squad/player questions unchanged — three
  honest states: ✓ grounded · ✓ rules · ℹ tactics.
- **`fixtures`** (ADR-048/049/067) — a league FDR ranking, a single team's schedule, a **squad's players by
  their fixture run**, or a **squad's teams** ranked by their run (with player-counts, via a "teams" cue);
  team names resolve or ask, never guess.

### Engineering
- **CI (GitHub Actions):** ruff + pytest on push (Py 3.13/3.14). Layered one-way architecture
  (`api → ingest → storage → analytics → ui → cli`); 49 ADRs; 421 offline tests; shared table renderer.

---

## ▶ The web track — Streamlit (ADR-051)

A read-only, local web view over the analytics — the web as a new *edge* over the same core (**the CLI
stays the engine**). Two steps taken:
- ✅ **A thin FastAPI slice** (Sprint 051, ADR-050) — `src/web/`, server-rendered, reusing the CLI text
  renderers in `<pre>`. Now **frozen** as the lean "also-serves-HTTP" reference.
- ✅ **A Streamlit spike + decision** (Sprint 052, ADR-051) — measured head-to-head (58 vs ~130+ LOC;
  interactive vs static; +21 vs lean deps). Verdict: **adopt Streamlit** as the UI we grow (pure-Python,
  interactive; fits "architecture over frontend syntax") — the heavier deps kept optional/web-only.
- ✅ **The Streamlit edge, graduated + grown** (`src/web_streamlit/`, ADR-052; tests + `requirements.txt`)
  — a multipage app: Home · Players · Fixtures (ticker) · Analyse · Transfer · Build · Captain · My Squad
  (formation pitch) · News · Trending (+ Community Signals) · Ask (chat). Session **squads** (build / upload
  / manager-ID import; edit — all in `session_state`, no server writes), photos + badges, charts.
- ✅ **Deployed** to Streamlit Community Cloud (Sprint 053, ADR-053; runbook: `docs/DEPLOY.md`) — public,
  read-only; a committed `data/seed.db` + `seed_squads.json` seed it. The core stays the one engine; the
  guardrail test (core imports no web) carries over.
- ✅ **A redesigned My Squad pitch** (Sprint 099, ADR-084) — a green FFH-style CSS pitch (kits in formation,
  xP chips, (C) armband + sub badges), now reused on **Build** too (Sprint 101, US-261); and a **⏳ next-
  deadline countdown** banner on Home + Squads, derived from fixtures (Sprint 101, ADR-086).

---

## Then — Data Hardening (post-GW1)

The substance that comes alive once the season runs (GW1 = 2026-08-21). **Prep done, dormant** (Sprint 069,
ADR-060) — GW1 is a flip (`history --backfill` + calibrate the weights). **The calibration tooling is now built**
(Sprint 138, ADR-101): a walk-forward backtest (`analytics/backtest.py`) + `python app.py calibrate` + the
**[GW1_RUNBOOK](../GW1_RUNBOOK.md)** — the flip is documented and measurable, no longer a guess. Real calibration
runs at ~GW4–6 (no per-GW data preseason); the harness **recommends**, the owner **commits** (weights stay 0).
- ◑ **Per-GW `history` ingestion** — a `player_history` table filled by the *existing* `element-summary`
  walk (empty preseason → live GW1). *(Full 567-player backfill can ride sooner.)* (Sprint 069, US-196.)
- ◑ **In-season form blend into xP** — a dormant rolling-**pp90** form term in the one `decision_xp` recipe
  behind `FORM_WEIGHT = 0` (Sprint 069, US-197). Still ahead: **calibration** at GW1 + rolling 3-GW/6-GW
  *trend views* over the new per-GW data.
- ◑ Attack/Defence FDR split + recent-form weighting (preseason strengths are 0 — ADR-005).
- ⬜ Price-change predictor (directional flags from net-transfer deltas — flags, not truth).

---

## New — Crowd & Sentiment Signals (Phase 6)

Fold *"what managers are doing"* + expert/pundit signals into the tools — as a **complementary lens, not a
rewrite of xP**. xP stays grounded & verified; sentiment is shown **alongside** it and never overrides it
(owner's calls: *lens + flags*; *free FPL signals first*). Investigation confirmed most of this is already
**free & structured in the FPL API** — no scraping needed to start.

**Tier 1 — free & structured (already in the API; start here).** Season-time (0 preseason → live at GW1):
- ✅ Ingest crowd/momentum fields: `transfers_in/out_event`, `cost_change_event`/`_start`, `form`,
  `ict_index` (+ Influence / Creativity / Threat), `value_form` (Sprint 060, US-182). (`selected_by`
  already stored, ADR-044.)
- ✅ A **lens + flags** — `crowd_flags` (🔥 trending · 💰 price · 📈 form · template/differential), on
  **Players · Build · Analyse · My Squad** (Sprint 060, US-183) + **Captain · Transfer** (Sprint 061,
  US-184).
- ✅ A **template-risk** captaincy lens — the ownership flags + a "safe template vs differential swing"
  caption on Captain (Sprint 061, US-184). *(A full captaincy-% EO model is later.)*
- ✅ A **"trends"** `ask`/`chat` intent + a **Trending page** — most-owned / transferred in-out / in-form
  boards over a pure `trending` helper (Sprint 067, US-193/194). Ownership works now; momentum/form light up
  at GW1.
- ✅ **Set-piece takers + a differential lens** — ingest the corner/FK order fields + `set_piece_flags`; a
  Players **"Set pieces"** view (pen/corner/FK takers + Own%/Val/£m, filterable) + a Pool flag; find
  low-ownership set-piece takers (Sprint 095, US-249/250, ADR-081). Display-only; a gated set-piece xP boost
  is a possible later modelling step.

**Tier 2 — external / extended signals (started Sprint 064, ADR-058; degrade gracefully like ClubElo).**
- ✅ **Community Signals** — a Reddit **RSS** buzz counter (`r/FantasyPL/.rss?limit=100`, **no auth/secret**
  — the `.json` API 403s), surfaced as a paginated Trending "💬 Talked about" board that counts mentions
  across the latest ~100 posts (Sprint 087, ADR-076); degrade-gracefully + cached + button-gated (Sprint
  068, US-195, ADR-059). *Cloud-IP may block → degrades. Buzz, not sentiment.*
- ✅ FPL official **news lens** — the stored `player.news` + `scout_news_link` on a **News** page
  (Sprint 064, US-190).
- ✅ **Import your team by manager-ID** — the public FPL entry API → the session active squad (Sprint 064,
  US-191; picks GW1-gated → live 2026-08-21).
- ⬜ Reddit **r/FPL** aggregate sentiment (Reddit API + a Cloud secret). X/Twitter (paid/restricted — skip).
- ⬜ Pundit / video NLP — LLM-summarise FPL YouTube / articles into structured signals (research-heavy).

**Tier 3 — evaluation (before trusting any of it).**
- ⬜ Backtest: does **following vs fading the crowd** beat xP-only? (ties to *Evaluation & feedback loops*).

**Principle:** analytics decide; the crowd is a **lens**. *Flags, not truth* (echoes the price-change note).

---

## Later — advanced optimisation & evaluation

- ◑ **Chip optimisers** — ✅ a v0 **chip-timing advisor** (`chip_advisor`, a grounded `ask` intent + a Squads
  "Chips" view): when to play Wildcard / Free Hit / Bench Boost / Triple Captain, from the squad's per-GW xP +
  fixture run (Sprint 096, US-251/252, ADR-082). Deferred: **DGW/BGW** detection (in-season) + **mini-league
  position** (leagues API, GW1) to sharpen it; a season-long (38-GW) scan; a standalone CLI `chips` command.
- ⬜ **Probabilistic xMins (the full ML model)** — per-fixture expected-minutes *probabilities* from
  schedule density, European congestion, rotation profiles. Needs in-season per-GW minutes to train
  (post-GW1) + external European-fixture data + a real ML effort — a later, data-gated phase. The rigorous
  successor to xMins v0.
- ⬜ Multi-week horizon **decay weights**; transfer-path simulation (a −4 now vs rolling).
- ⬜ **Evaluation & feedback loops** — did the suggested captain beat the template? Golden-gameweek
  regression; success metrics (xP calibration, captain hit-rate, net season points). *Critical before
  fully trusting recommendations.*

---

## Infrastructure (carried)

- ✅ **Cross-device squad persistence** — **DONE (Sprint 124, ADR-094).** A handle-keyed free store
  (`cloud_store`, Supabase, no login) so a squad follows you between devices — the first opt-in, secret-gated
  server write (the read-only invariant revised + tested); off by default. Owner setup: `docs/CLOUD_SQUADS.md`.
  Native `st.login()` = the deferred "product" upgrade (the adapter interface fits it). **Beta ops** also decided
  (ADR-095): a prod/staging split, public + PolyForm-NC LICENSE, a mirror backup, an uptime monitor.
- ✅ **"Remember me" across a refresh** — **DONE + owner-verified on Safari + Chrome (Sprint 132 built, ADR-099;
  read-path fixed Sprint 134, US-330).** A refresh keeps a tester in; the value is re-validated on load (pruned
  tester / rotated code locked out); off by default. Sprint 132's native read didn't persist (a cookie-jar mismatch
  — component-iframe write vs top-level read); now read + write both go through the component. `st.login()` (native
  persistence + verified identity) stays a *future option*, no longer a needed escalation.
- ✅ **Beta usage & experience analytics** — **DONE (Sprint 136 foundation + Sprint 137 coverage, ADR-100).**
  Anonymous, opt-in (`FPL_ANALYTICS`), fail-silent: `session_started`/`page_viewed` + the feature events
  (`analysis_run`/`squad_*`/`feedback_submitted`) + `error` + `perf` timers → a Supabase `events` table (reuses the
  store, no new secret); a gated **📊 Admin** view (`FPL_ADMIN_KEY`) reads + summarises (sessions/returning/top
  pages/success/median-P95). Foundation write **owner-verified** (rows landing); **⏳ admin-read owner smoke** (add
  the anon SELECT policy + set the key). Deferred: batching, a BI dashboard, cohorts.
- ✅ **"Log out" link** — **DONE (Sprint 133, extends ADR-099).** A sidebar "Log out" clears the cookie + session
  and re-shows the gate (reset a shared device); deferred clear + a `_beta_forgotten` re-admit guard; off on the
  open deploy. Deferred: a confirm dialog, a **signed token**; native `st.login()` (hard identity) is still the
  product-path upgrade above.
- ⬜ Session/cookie **auth** for user-specific data (`/my-team/{id}/`) — unlocks a manager-ID fetch in
  `analyse`/`transfer`.
- ⬜ **Source versioning** — formalise "version all external sources"; confidence scoring on fallback.
- ⬜ Cache TTLs + a gameweek countdown.

---

## Guiding principles (unchanged)

- **The CLI stays the engine** — new surfaces (web) are edges over the same analytics; generic core, policy
  at the edge.
- **Analytics decide; the LLM only narrates** — grounded, verified, optional.
- **FPL is the source of truth**; external sources degrade gracefully.
- **Learn by building, sprint by sprint** — a gate (ADR) per feature; simple over clever.
