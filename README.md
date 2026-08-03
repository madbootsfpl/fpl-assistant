# FPL Assistant

A personal Fantasy Premier League analytics assistant — a command-line tool.

**Status:** Phase 1 — *CLI Analytics MVP* — **complete** (2026-08-03). See the
[Roadmap](docs/04_Roadmap/Roadmap.md).

## What it does today (the MVP)

- Analyse FPL players (points, value, form-free rankings)
- Calculate value metrics (Points per £m) and Expected Points (xP) over a fixture horizon
- Expected goals (xG / xA / xGI / xGC), over/under-performance, Defensive Contribution, clean sheets
- Custom fixture difficulty (overall + ClubElo Elo)
- Pick an optimal XI or full 15-man squad (ILP), with formations, bench, and availability handling
- Save and reload your own squad (re-priced, with current injuries + departures)

## Planned (Phase 2+ — not yet built)

- Recommend transfers · recommend captains (Phase 3)
- AI-assisted natural-language analysis (Phase 4)
- A web dashboard UI, CI/CD, historical data (Phase 2)

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

## Commands

The app is driven by subcommands (see ADR-003):

```bash
python app.py refresh                          # fetch FPL data (players, teams, fixtures)
python app.py table --sort value --limit 20    # players, ranked by points or value (£m)
python app.py search haaland                   # find players by name
python app.py filter --pos DEF --max-price 6   # filter players (position / team / max price)
python app.py fdr --type elo --next 5           # teams by fixture difficulty (FPL / custom / ClubElo)
python app.py fixtures --team ARS --type custom # a team's upcoming fixtures + difficulty
python app.py xp --type custom --next 5         # players by expected points over the next N gameweeks (vs FPL's ep_next at N=1)
python app.py xg --pos FWD                       # players by expected goal involvement (xGI = xG + xA)
python app.py overperf                           # over/under-performers: actual vs expected attacking points
python app.py defcon                             # reliable Defensive Contribution earners (per-90 vs threshold)
python app.py cleansheet                         # best clean-sheet prospects (DEF/GK by expected goals conceded / 90)
python app.py squad --budget 80                 # pick the optimal starting XI (1-4-4-2) within a budget
python app.py squad --include Haaland --exclude Salah  # the optimal XI built around your picks
python app.py squad --objective xp              # optimise the XI on points / value / xp
python app.py squad --full --include <4 cheap>  # the full 15-man squad (2/5/5/3, £100m); you pick the bench
python app.py squad --bench Dubravka Diop        # declare your bench (marked **, shown last); implies --full
python app.py squad --formation 3-5-2            # pin the XI shape (default: the best legal formation)
python app.py squad --objective xgi              # optimise on expected goal involvement (attacking)
python app.py squad --include-unavailable        # also consider injured/suspended (excluded by default)
python app.py squad --full --save my-team        # save your squad (persists across refreshes)
python app.py squad --load my-team               # reload it — re-priced, with current injuries + departures
```

`refresh` is the only command that touches the network; every view reads from the
local database (`data/fpl.db`).

Created by Tony Sheridan.