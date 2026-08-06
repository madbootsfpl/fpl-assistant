# ADR Index

An index of all Architectural Decision Records in this project. Add a row for each
new ADR as it is created.

| ADR | Title | Status |
|-----|-------|--------|
| [001](./ADR-001-single-user-vs-multi-user.md) | Single-user vs Multi-user architecture | Accepted |
| [002](./ADR-002-ui-approach.md) | UI approach | Accepted |
| [003](./ADR-003-cli-approach.md) | Command-line interface approach | Accepted |
| [004](./ADR-004-fixtures-and-fdr.md) | Fixtures data model & FDR approach | Accepted |
| [005](./ADR-005-custom-fdr.md) | Custom (overall) fixture difficulty | Accepted |
| [006](./ADR-006-expected-points-v0.md) | Expected Points (xP v0) | Accepted |
| [007](./ADR-007-multi-week-xp.md) | Multi-week xP (fixture horizon) | Accepted |
| [008](./ADR-008-squad-selector.md) | Optimal squad selector (ILP) | Accepted |
| [009](./ADR-009-squad-include-exclude.md) | Squad selector include / exclude | Accepted |
| [010](./ADR-010-clubelo-external-source.md) | ClubElo — first external data source | Accepted |
| [011](./ADR-011-squad-objective.md) | Squad objective toggle (points/value/xp) | Accepted |
| [012](./ADR-012-full-squad.md) | The full 15-man squad (`squad --full`) | Accepted |
| [013](./ADR-013-declared-bench.md) | A declared bench (`squad --bench`) | Accepted |
| [014](./ADR-014-flexible-formations.md) | Flexible formations (`squad --formation`) | Accepted |
| [015](./ADR-015-expected-goals.md) | Expected goals (xG/xA/xGI) from the FPL API | Accepted |
| [016](./ADR-016-soccerdata-evaluation.md) | soccerdata as a data source — **Defer** | Accepted |
| [017](./ADR-017-over-under-performance.md) | Over/under-performance (expected vs actual attacking points) | Accepted |
| [018](./ADR-018-defensive-contribution.md) | Defensive Contribution (DefCon reliability) | Accepted |
| [019](./ADR-019-clean-sheet-solidity.md) | Clean-sheet / defensive-solidity lens (xGC) | Accepted |
| [020](./ADR-020-clubelo-retry.md) | ClubElo retry-with-backoff (transient failures) | Accepted |
| [021](./ADR-021-importance-scaled-retry.md) | Importance-scaled retry (FPL tries hard, ClubElo fails fast) | Accepted |
| [022](./ADR-022-validate-legal-bench.md) | Validate a legal bench (warn, not block) | Accepted |
| [023](./ADR-023-player-availability.md) | Player availability (skip injured; opt-out) | Accepted |
| [024](./ADR-024-saved-squad.md) | Saved / persistent squad (user state, JSON) | Accepted |
| [025](./ADR-025-shared-table-renderer.md) | Shared table renderer (`Col` + `render_rows`) | Accepted |
| [026](./ADR-026-phase1-cli-mvp.md) | Declare Phase 1 (CLI Analytics MVP) complete; reframe the Roadmap | Accepted |
| [027](./ADR-027-historical-past-seasons.md) | Historical past-season data (`history --backfill`) | Accepted |
| [028](./ADR-028-xp-historical-baseline.md) | xP historical baseline (multi-season rate) | Accepted |
| [029](./ADR-029-captain-suggestions.md) | Captain suggestions (recommend + explain; xP, GK-excluded) | Accepted |
| [030](./ADR-030-transfer-suggestions.md) | Transfer suggestions (best single legal upgrades; xP gain, `--bank`) | Accepted |
| [031](./ADR-031-team-analyser.md) | Team Analyser (a saved squad's health check; indicators, not a grade) | Accepted |
| [032](./ADR-032-per-gameweek-xp.md) | Per-gameweek xP breakdown (+ `analyse --sort xp`) | Accepted |
| [033](./ADR-033-llm-grounded-narration-spike.md) | LLM grounded-narration spike (local Ollama; analytics decide, LLM narrates) | Accepted |
| [034](./ADR-034-ask-command-grounded-nl.md) | The `ask` command — grounded NL answers (routing; LLM optional) | Accepted |
| [035](./ADR-035-multi-transfer-plan.md) | Multi-transfer plan (coordinated, greedy; `transfer --count` / `ask` N transfers) | Accepted |
| [036](./ADR-036-per-gameweek-plan-table.md) | Per-gameweek transfer-plan table + a structured detail in `ask` | Accepted |
| [037](./ADR-037-grounding-verification.md) | Grounding verification (verify the LLM narration; a ✓/⚠ trust line) | Accepted |
| [038](./ADR-038-expected-minutes-v0.md) | Expected minutes (xMins) v0 — weight recommendations by playing time (chance% × minutes share; default-on at the decision edge) | Accepted |
| [039](./ADR-039-start-bench-compare-intents.md) | Two new `ask` intents — start/bench (best legal XI vs declared) + compare (robust name-matching; analytics decide, LLM narrates) | Accepted |
| [040](./ADR-040-low-evidence-xp-and-transfer-dedup.md) | Sane low-evidence xP (shrink the no-baseline fallback toward a replacement prior) + transfer dedup (no repeated incoming) + consistency clarity | Accepted |
| [041](./ADR-041-one-xp-metric-and-squad-build-intent.md) | One xP metric — unify the optimiser with the decision layer (`decision_xp`; `xp` the default `squad` objective) + `ask "build me a squad"` | Accepted |
| [042](./ADR-042-shortlist-intent.md) | A "best players" shortlist `ask` intent — `best <position> [under £X]` ranked by xP (or xP/£m for "value"); grounded | Accepted |
| [043](./ADR-043-squad-archetype-constraints.md) | Squad archetypes — min-count price-band constraints in the optimiser (`--cheap`/`--premium`, NL); differential defined + deferred (needs ownership) | Accepted |
| [044](./ADR-044-differential-archetype.md) | The differential archetype — ingest ownership; a ≤5%-owned min-count constraint (`--differential N`, NL); completes ADR-043 | Accepted |
| [045](./ADR-045-bench-aware-optimisation.md) | Bench-aware squad optimisation — a `start`-variable ILP + weighted objective; `--weekly` (max XI + playing bench) / `--bench-boost` (max-15); default unchanged | Accepted |
| [046](./ADR-046-xi-aware-transfers.md) | XI-aware transfers — rank swaps by XI-gain (best-XI change) via a fast `best_xi_points`; the default (`--raw` for the old ranking) | Accepted |
| [047](./ADR-047-conversational-ask-follow-ups.md) | Conversational `ask` — a `chat` REPL with grounded follow-ups (why / next / what-about); a pre-route resolver + rank offset; analytics still decide, verifier runs each turn | Accepted |
| [048](./ADR-048-fixtures-fdr-ask-intent.md) | A fixtures / FDR `ask` intent — league FDR ranking + single-team schedule (reuse `team_fdr`/`team_schedule` + renderers); team resolution never guesses; FPL difficulty; squad-scoped deferred | Accepted |
| [049](./ADR-049-squad-scoped-fixtures.md) | Squad-scoped fixtures — a third `fixtures` mode: rank a saved squad's **players** by their team's FDR (player-level); precedence team→squad→league; `_squad_name` possessive-aware; works in `ask` + `chat` | Accepted |
| [050](./ADR-050-thin-web-ui.md) | A thin web UI — a read-only, local-only **FastAPI** (sync) edge in `src/web/` reusing the analytics/`ask` (core stays web-free); slice 1 reuses the text renderers in `<pre>`; `/` + `/ask` flagship | Accepted |
| [051](./ADR-051-web-track-streamlit.md) | The web track — a measured spike (Streamlit vs FastAPI) decides: **adopt Streamlit** (pure-Python, interactive; ~⅓ the code) and **freeze the FastAPI edge** as a lean reference; graduate the spike to `src/web_streamlit/` next | Accepted |
| [052](./ADR-052-streamlit-edge-structure.md) | The Streamlit edge structure — multipage `pages/`; a clean `python -m src.web_streamlit` runner (no `sys.path` hack); filterable table + chat-style Ask; `streamlit` web-only; the two-edge guardrail; FastAPI frozen | Accepted |
| [053](./ADR-053-deploy-streamlit-community-cloud.md) | Deploy & share — **Streamlit Community Cloud** (owner relaxed the custom domain), a committed **seed DB**, fully **public/read-only**; no secrets, Ask degrades without Ollama; going live is owner-executed via a runbook | Accepted |
| [054](./ADR-054-cloud-squads-session-and-files.md) | Cloud squads — a session **"active squad"** (build/upload) + **download/upload** persistence (the user's file; no server writes); a committed demo seed (`SQUADS_PATH` fallback); Transfer/Analyse/Captain consume the dict | Accepted |
| [055](./ADR-055-editable-session-squad.md) | An **editable** session squad — mutate in `session_state` (name · apply-transfer · manual-swap · set-captain · bench; no server writes); a generic **`squad_15_issues`** validator (budget = warn, not block); `captain_id` superset + **(C)**; edit inline (Transfer/Captain) + a **My Squad** hub; fixes the Build xP/xMins bug | Accepted |
| [056](./ADR-056-local-refresh-and-freshness.md) | A **local-only** data-refresh button (gated by `FPL_LOCAL`, set by the runner; writable non-seed DB) reusing `ingest.refresh` + a **"Data as of \<date\>"** freshness caption on every tab (DB mtime); the cloud stays read-only (caption only) — the first, narrowly-scoped web write path | Accepted |
| [057](./ADR-057-crowd-signals-lens.md) | **Phase 6** opener — crowd/sentiment signals as a **complementary lens + flags, never blended into xP**; Tier-1 **free FPL** fields (`transfers_*_event` · `cost_change_*` · `form` · `ict_index`+components · `value_form`); a pure `crowd_flags` helper (template ≥20% / differential ≤5% / trending / price / in-form; tunable, GW1-calibrated); external social + pundit deferred (Tier 2/3) | Accepted |
| [058](./ADR-058-tier2-fpl-news-and-manager-import.md) | **Phase 6 Tier 2** (start) — an FPL official-**news lens** (surface the ingested `player.news` + scout links) + **import a team by manager-ID** (public FPL entry API → a `SquadStore`-shaped session squad; **GW1-gated** picks; no auth/secret); degrade-gracefully (ClubElo pattern); not xP; no server writes; keyed social (Reddit/X) + pundit NLP deferred | Accepted |
| [059](./ADR-059-community-signals-reddit-rss.md) | **Community Signals** — a Reddit **RSS** buzz counter (`r/FantasyPL/.rss`, **no auth/secret** — the `.json` API 403s); count current-player mentions → "most talked about"; **degrade-gracefully** (403/429/parse → "unavailable"), **cached + button-gated** + a descriptive UA; a Trending "💬 Talked about" board; buzz (frequency) not sentiment; not xP; cloud-IP may block → degrades | Accepted |
| [060](./ADR-060-per-gameweek-history-and-dormant-form-blend.md) | **Data Hardening** step 1 — a per-GW `player_history` table (`PlayerGameweek`, keyed code+round; additive/idempotent) filled by the **existing** throttled `element-summary` walk (empty preseason → live GW1); a **dormant** in-season **form blend** in the one `decision_xp` recipe (a computed minutes-aware **rolling pp90**, not FPL's `form`) behind `FORM_WEIGHT = 0` → `rate` unchanged today; the one-xP invariant (ADR-041) preserved, pinned by an invariance test; GW1 flip = backfill + set the weight | Accepted |
| [061](./ADR-061-differentials-and-value-ask-intent.md) | **Differentials / value `ask` intent** — extend the shortlist (ADR-042) with a **differential** lens (filter ≤ `DIFFERENTIAL_OWN` owned, +Own% column; the plain shortlist stays byte-identical) + a new single-player **`worth`** intent ("is X worth the money?" → xP/£m · rank among position peers · vs the position median · a tiered fact-derived verdict; degrades on no match); routing `worth` before `shortlist`, "differentials"→shortlist, "most owned"→trends; grounded (ADR-037); preseason-honest (ownership sharpens at GW1) | Accepted |
| [062](./ADR-062-web-build-parity-and-tab-reorg.md) | **Web build parity + tab reorg** — expose the full CLI `squad` options as **form widgets on "Build Squad"** (include/exclude/bench/objective/no-xmins/weekly/bench-boost/include-unavailable) feeding the *same* `select_squad`/`decision_xp` (no engine change); the saveable build stays a full **15** (formation = an XI-only **display preview**); My Squad stays the tweaker + a "Rebuild in Build Squad →" link; rename Squads→**Squad Health**, Build→**Build Squad**, grouped; an optional Ask-build → session-squad bridge; no server writes | Accepted |
| [063](./ADR-063-player-stats-page-and-pagination.md) | **Player Stats page + pagination** — a new **Player Stats** page (tabs: Over/under · DefCon · Clean sheets · xG) reusing `over_under`/`defcon_reliability`/`defensive_solidity` + the xGI ranking (no analytics change; season-to-date, team badges), placed at sidebar **position 2** (renumber); a shared **`paginate`** helper (`page_labels` pure) so **Players** (page all + sort by team/position) and **Trending** (four boards page past 30) can see everything; no server writes | Accepted |
| [064](./ADR-064-shared-player-filter.md) | **Shared player filter** — one `web_streamlit/filters.py` (`filter_controls` + `apply`): **Team · Position · Player** multiselects (+ optional max-price), **AND**-combinable (empty dim = any), tolerant of Row/dict rows; applied to **Player Stats** (all four tabs) and **Players**; the Players scatter → a filter-responsive **top-15 bar** (Altair, rank-ordered) by the sort metric; no analytics change, no server writes | Accepted |
| [065](./ADR-065-help-tooltips.md) | **Help tooltips (ⓘ)** — a concise, action-oriented `help=` on **every input control** (selectbox/multiselect/slider/number_input/text_input/checkbox/radio) across the web, added at the shared components (`filters`/`paginate`/`squads`) + per page; key buttons too; `st.tabs`/`st.chat_input` exempt (captions cover them); a coverage test (`.help` via AppTest) enforces "all options have a tooltip"; no behaviour change | Accepted |
| [066](./ADR-066-tech-debt-pulp-and-squad-renderer.md) | **Tech debt — PuLP + squad renderer** (revises 2 Backlog items on real behaviour): migrate `LpVariable`→`problem.add_variable`, **keep `PULP_CBC_CMD`** (COIN_CMD fails — needs an external CBC; would break the Cloud), and narrow the blanket DeprecationWarning ignore to a **targeted** PULP_CBC_CMD filter; share the squad renderers' **header/divider + bench-heading** but **don't** fold into `render_rows` (not byte-identical-feasible — mid-table heading, glued markers, divergent price cells); no behaviour/output change | Accepted |
