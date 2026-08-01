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
python app.py fdr --next 5                      # teams ranked by upcoming fixture difficulty
python app.py fixtures --team ARS              # a team's upcoming fixtures
```

`refresh` is the only command that touches the network; every view reads from the
local database (`data/fpl.db`).

Created by Tony Sheridan.