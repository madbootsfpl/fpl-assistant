# FPL Assistant

[![CI](https://github.com/tesheridan/fpl-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/tesheridan/fpl-assistant/actions/workflows/ci.yml)

A personal Fantasy Premier League analytics assistant — a command-line tool.

**Status:** Phase 1 (*CLI Analytics MVP*) **complete**; Phase 3 (*decision support* —
captain · transfer · squad analysis) **complete** (2026-08-04). See the
[Roadmap](docs/04_Roadmap/Roadmap.md).

## What it does today

**Analytics**
- Rank players by points / value (Points per £m) and **Expected Points (xP)** over a fixture
  horizon — now with a **per-gameweek breakdown** (`--by-gameweek`)
- Expected goals (xG / xA / xGI / xGC), over/under-performance, Defensive Contribution, clean sheets
- Custom fixture difficulty (overall + ClubElo Elo)
- **Past-season history** (a throttled backfill) feeding a multi-season xP baseline

**Optimisation**
- Pick an optimal XI or full 15-man squad (ILP), with formations, bench, and availability handling
- Save and reload your own squad (re-priced, with current injuries + departures)

**Decision support (Phase 3)** — recommend *and explain*, composed on the above:
- **`captain`** — the best captain picks for the next GW (by xP), with opponent + penalty duty
- **`transfer`** — the best single legal transfers for your squad (≤3/club, budget, by xP gain)
- **`analyse`** — a saved squad's health over N GWs (projected XI xP, weak links, injuries), cross-linked
- **Expected minutes (xMins v0)** — every recommendation **weights xP by expected playing time**
  (`chance_of_playing%` × a historical minutes share), so rotation risks don't out-rank nailed-on
  starters. Shown as expected minutes; use `--no-xmins` for the raw "assumes 90" number.

**Natural language (Phase 4)** — grounded, and optional:
- **`ask "..."`** — ask a question in plain English (captain / transfer / squad health / start-bench /
  compare / **build a squad** / **best players in a position**). The
  **analytics decide**; a **local LLM (Ollama) only narrates** — and every answer is **checked
  against the data** (a ✓/⚠ trust line: figures and names are verified, not just instructed). `ask`
  works without the LLM (it falls back to the decision + facts).

## Planned (not yet built)

- A web dashboard UI (Phase 2); in-season form (needs the season started); the full probabilistic
  xMins model — schedule/European congestion, rotation profiles (Phase 5, post-GW1). *(xMins **v0** —
  chance% × historical minutes — is built; see above.)*

See the [Roadmap](docs/04_Roadmap/Roadmap.md) and
[Phase 1 reconciliation](docs/04_Roadmap/Phase1_Reconciliation.md).

## Technology

- Python (standard library + `requests`)
- SQLite (local cache)
- PuLP (integer-programming squad optimiser)
- pytest (offline test suite)
- VS Code · GitHub · Claude Code

## Getting Started

```bash
# 1. Activate the virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. See the available commands
python app.py --help

# 4. Run the tests (offline — no live API calls)
pytest
```

## Development

CI (GitHub Actions) runs `ruff` (lint) and the offline test suite on every push and PR
across Python 3.13/3.14. To mirror it locally:

```bash
pip install ruff pre-commit
ruff check .            # lint (config in ruff.toml)
pre-commit install      # optional: run the same checks on every git commit
```

## Commands

The app is driven by subcommands (see ADR-003):

```bash
python app.py refresh                          # fetch FPL data (players, teams, fixtures)
python app.py history --backfill               # backfill past-season history (once per season)
python app.py table --sort value --limit 20    # players, ranked by points or value (£m)
python app.py search haaland                   # find players by name
python app.py filter --pos DEF --max-price 6   # filter players (position / team / max price)
python app.py fdr --type elo --next 5           # teams by fixture difficulty (FPL / custom / ClubElo)
python app.py fixtures --team ARS --type custom # a team's upcoming fixtures + difficulty
python app.py xp --type custom --next 5         # players by expected points over the next N gameweeks
python app.py xp --next 5 --by-gameweek         # xP split per gameweek (GW1 GW2 … + total)
python app.py xg --pos FWD                       # players by expected goal involvement (xGI = xG + xA)
python app.py overperf                           # over/under-performers: actual vs expected attacking points
python app.py defcon                             # reliable Defensive Contribution earners (per-90 vs threshold)
python app.py cleansheet                         # best clean-sheet prospects (DEF/GK by expected goals conceded / 90)
python app.py squad --budget 80                 # pick the optimal starting XI (1-4-4-2) within a budget
python app.py squad --include Haaland --exclude Salah  # the optimal XI built around your picks
python app.py squad --objective xp              # xP is the DEFAULT objective (forward-looking; consistent with transfer)
python app.py squad --objective points          # optimise last season's total points instead
python app.py squad --full --cheap 3 --premium 1  # shape it: ≥3 low-cost (≤£4.5m) + ≥1 premium (≥£9m)
python app.py squad --full --differential 3       # ≥3 off-template picks (≤5% owned)
                                                  #   (a full build shows Starting XI xP vs Bench xP —
                                                  #    the weekly-relevant number for comparing builds)
python app.py squad --full --include <4 cheap>  # the full 15-man squad (2/5/5/3, £100m); you pick the bench
python app.py squad --bench Dubravka Diop        # declare your bench (marked **, shown last); implies --full
python app.py squad --formation 3-5-2            # pin the XI shape (default: the best legal formation)
python app.py squad --objective xgi              # optimise on expected goal involvement (attacking)
python app.py squad --include-unavailable        # also consider injured/suspended (excluded by default)
python app.py squad --full --save my-team        # save your squad (persists across refreshes)
python app.py squad --load my-team               # reload it — re-priced, with current injuries + departures

# Decision support (Phase 3) — work on a saved squad:
python app.py captain --squad my-team            # best captain picks next GW (xP + opponent + penalty)
python app.py transfer --squad my-team --bank 2  # best single legal transfers by xP gain (bank £2m)
python app.py transfer --squad my-team --count 3 # a coordinated plan of 3 transfers (shared bank),
                                                 #   with each incoming player's points per gameweek
python app.py analyse --squad my-team --sort xp  # squad health over N GWs (per-GW xP, weak links, injuries)
python app.py captain --squad my-team --no-xmins # raw xP (don't weight by expected minutes / xMins v0)

# Natural language (Phase 4) — grounded in the analytics; local LLM optional:
python app.py ask "who should I captain from my-team?"
python app.py ask "what transfer should I make for my-team?"
python app.py ask "which 3 transfers for my-team?"
python app.py ask "analyse my-team"
python app.py ask "who should I start from my-team?"   # best legal XI (xMins-weighted) vs your bench
python app.py ask "Haaland or Saka?"                   # compare two players side by side
python app.py ask "build me a squad for £100m"         # the optimal 15 on xP, within budget
python app.py ask "build me a squad for £100m with 3 low cost players and 1 premium player"
python app.py ask "best midfielders under £8m"         # top players by xP (position + price filters)
```

`refresh` is the only command that touches the network; every view reads from the
local database (`data/fpl.db`).

Created by Tony Sheridan.