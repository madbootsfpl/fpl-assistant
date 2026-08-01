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

# 3. Run the app (fetches live player data from the FPL API)
python app.py

# 4. Run the tests (offline — no live API calls)
pytest
```

Expected output from `python app.py`:

```text
⚽ FPL Assistant starting...
Fetched <N> players across 20 teams from the FPL API.
```

Created by Tony Sheridan.