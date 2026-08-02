# FPL Assistant

A personal Fantasy Premier League analytics platform.

## Goals

- Analyse FPL players
- Calculate value metrics
- Recommend transfers
- Recommend captains
- Provide AI-assisted analysis

## Technology

- Python
- FastAPI
- VS Code
- GitHub
- Claude Code

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
python app.py squad --budget 80                 # pick the optimal starting XI (1-4-4-2) within a budget
python app.py squad --include Haaland --exclude Salah  # the optimal XI built around your picks
python app.py squad --objective xp              # optimise the XI on points / value / xp
python app.py squad --full --include <4 cheap>  # the full 15-man squad (2/5/5/3, £100m); you pick the bench
```

`refresh` is the only command that touches the network; every view reads from the
local database (`data/fpl.db`).

Created by Tony Sheridan.