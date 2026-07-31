# Master FPL Assistant Roadmap

*(Original structure preserved + gaps, risks, and refinements integrated)*

---

## Phase 1 – Foundations & Infrastructure

**Goal:** Establish reliable data pipelines, local persistence, auto-refresh scheduling, and the base dashboard UI.

### Environment & CI/CD
- Set up repository structure, virtual environments, pre-commit hooks, and GitHub Actions (linting/tests).
- Configure environment variables for local vs. production environments.

### FPL API Ingestion & Local Cache
- Implement client wrapper for static endpoints (`/bootstrap-static/`, `/fixtures/`, `/element-summary/{id}/`).
- Build session/cookie auth handler to fetch user-specific data (`/my-team/{id}/`) safely.
- Add a local caching layer (Redis or SQLite with TTLs) to prevent 429 rate-limiting.

### Database Schema (SQLite / PostgreSQL)
- Design schema for players, fixtures, historical gameweek statistics, and price trends.
- Implement historical backfills (incorporating past season stats for long-term modeling).
- Design schema from day one to support multi-manager / league analysis later (even if Phase 1 only uses a single manager ID).

### Base Dashboard UI
- Set up web app boilerplate (FastAPI/Flask + React/Next.js preferred long-term; Streamlit/Dash acceptable only for rapid prototyping).
- Display live player tables, raw stats, and basic gameweek countdown timer.
- Decide early whether this is an internal tool or a multi-user product — this choice drives later UI decisions.

### Risks / Mitigations
- External data sources (especially later xG) will break → plan for graceful degradation and source versioning from the start.

---

## Phase 2 – Analytics Engine

**Goal:** Transform raw FPL points into granular predictive metrics, custom rating models, and expected value indicators.

### Advanced Metric Ingestion
- Integrate xG, xA, and xGI via open datasets or scrapers.
- Account for recent rules changes (updated Bonus Point System rules for clearances, blocks, interceptions, and goalkeeper saves).
- Build clear confidence scoring and fallback behaviour when external sources are unavailable.

### Value & Form Ranking
- Calculate Points per £m (season-long) and Form per £m (short-term).
- Build short-term rolling averages (3-GW vs. 6-GW trendlines).

### Custom Fixture Difficulty Rating (FDR)
- Decouple into separate Attack FDR and Defense FDR.
- Incorporate home/away bias and recent team defensive/attacking metrics.

### Price Change Predictor
- Track net transfer deltas to flag upcoming rises/falls before daily cutoffs.
- Treat early versions as **directional flags only** — the real FPL price algorithm is more nuanced (ownership %, thresholds, timing).

### Explicit xP Engine (new first-class deliverable)
- Build a robust per-player, per-fixture Expected Points model (with uncertainty estimates).
- This becomes the single source of truth for every downstream recommendation, captain pick, and optimizer.

---

## Phase 3 – Decision Support Engine

**Goal:** Translate analytics into actionable manager recommendations (captains, transfers, squad health).

### Expected Minutes (xMins) & Rotation Model
- Incorporate rotation risk (European matches, manager tendencies, injury news).
- Build baseline predicted minutes per player per gameweek.
- Injury/news data is noisy → require secondary sources + manual override capability + confidence scores.

### Captain Suggestion Algorithm
- Rank top 3–5 captains using the Phase 2 xP model, fixture strength, form, and penalty duties.

### Transfer Recommendation Engine
- Evaluate squad weaknesses (injuries, poor fixture runs, low xMins).
- Fully respect FPL constraints (budget, max 3 per team, free transfers, hits).

### Team Analyser Tool
- Upload/link manager ID to grade team health over the next 1–5 gameweeks.
- Highlight bench strength and potential starting XI headaches.

### Live Event Layer (new)
- Lightweight layer that can invalidate or re-rank recommendations when injuries, lineups, or price changes occur without a full recompute.

---

## Phase 4 – AI & Natural Language Layer

**Goal:** Add an intelligent interface that explains data outputs using grounded Retrieval-Augmented Generation (RAG).

### Grounded RAG Pipeline
- Pass structured analytics outputs (JSON from Phases 2 & 3) directly into the LLM context.
- Never let the LLM calculate prices, points, or deadlines itself — this is the primary defence against hallucination.

### Chat Interface & Query Parser
- Conversational UI for natural language queries (“Who should I start between Palmer and Saka?” / “Analyze my defense for GW8”).
- Intent-matching system to route queries to the correct analytics module.

### Strategy & Decision Justification
- Generate short, human-readable explanations of why one option is mathematically preferred.

---

## Phase 5 – Advanced Optimization & Long-Term Planning

**Goal:** Solve complex multi-week squad decisions using mathematical optimization.

### Linear Programming Solver (Integer Programming)
- Build optimization pipeline (PuLP / scipy.optimize) under strict budget and positional constraints.
- Start with single-week + simple heuristics in Phase 3; graduate to full integer programming only once the xP objective function is proven.

### Chip Strategy Optimizers
- Wildcard / Free Hit: full 15-man squad generation for a defined horizon.
- Bench Boost: identify double-gameweek or high-value bench setups.
- Triple Captain: flag peak single-match or double-gameweek opportunities.

### Multi-Week Horizon Planning
- 3-to-6 gameweek lookahead with decaying weights.
- Simulate transfer paths (taking a –4 now vs rolling) to evaluate long-term net yield.

---

## Cross-Cutting Additions (apply across all phases)

### Evaluation & Feedback Loops (critical missing piece)
- Track real-world performance: “Did the suggested captain beat the template?”, “Did the multi-week plan outperform a simple rolling strategy?”
- Maintain a set of historical “golden” gameweeks for regression testing.
- Collect live manager feedback. Without measurement, sophisticated models can look clever while underperforming.

### Data Reliability Philosophy
- Official FPL API is the source of truth for ownership, prices, points, and fixtures.
- External sources (xG, injuries, news) are best-effort and must degrade gracefully.
- Version all external data sources.

### Success Metrics to Define Early
- Accuracy of price-change flags
- Calibration of xP vs actual points
- Hit rate of captain suggestions vs popular templates
- Net points gained by following transfer / chip recommendations over a season