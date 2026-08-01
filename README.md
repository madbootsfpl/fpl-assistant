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
python app.py refresh                       # re-fetch FPL data and store it locally
python app.py table --limit 20              # show stored players as a table
python app.py search haaland                # (coming in US-008)
python app.py filter --pos MID --max-price 8  # (coming in US-008)
```

`refresh` is the only command that touches the network; every view reads from the
local database (`data/fpl.db`).

Created by Tony Sheridan.