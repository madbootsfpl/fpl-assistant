"""Central configuration for the FPL Assistant.

Keeping endpoints, timeouts and headers in one place means the rest of the code
never hard-codes URLs, and tests (or a future config file) can override them
easily. See docs/03_Architecture/Architecture.md (§4 Components — "Config").
"""

# Base URL for the official FPL API.
FPL_BASE_URL = "https://fantasy.premierleague.com/api"

# Static endpoint: all players, teams and gameweeks in a single payload.
BOOTSTRAP_STATIC_PATH = "/bootstrap-static/"

# Fixtures endpoint: all matches (home/away teams, difficulty, gameweek).
FIXTURES_PATH = "/fixtures/"

# Per-player endpoint (ADR-027): a player's fixtures, this-season per-GW history, and
# `history_past` (past-season summaries). `{}` is the per-season element id.
ELEMENT_SUMMARY_PATH = "/element-summary/{}/"

# Seconds to wait between element-summary calls during a history backfill (ADR-027).
# A full backfill is one call per player (~567), so we throttle to respect rate limits
# (~0.3s ≈ a few minutes). It's a fetch-once-per-season job, kept out of `refresh`.
HISTORY_THROTTLE = 0.3

# Local LLM for the `ask` command (ADR-034). Ollama's generate endpoint; the model is one
# pulled locally. The LLM is OPTIONAL — `ask` degrades to the analytics decision if it's absent.
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"
OLLAMA_TIMEOUT = 60

# ClubElo — the second (external) data source: team Elo ratings (ADR-010).
# The API returns CSV for a given date at CLUBELO_BASE_URL/<YYYY-MM-DD>.
CLUBELO_BASE_URL = "http://api.clubelo.com"

# How long (in seconds) to wait for the API before giving up.
REQUEST_TIMEOUT = 10

# ClubElo is best-effort, so it gets a tighter budget than the required FPL source
# (ADR-021): a shorter timeout + fewer retries → a sustained outage degrades fast.
# A healthy ClubElo answers in ~1–2s, so 5s is a safe margin.
CLUBELO_TIMEOUT = 5

# Where the user's saved squads live (ADR-024). This is *user state*, kept separate
# from the reference cache (fpl.db) so it survives a refresh — and gitignored.
SQUADS_PATH = "data/squads.json"

# The FPL API can reject requests that don't look like they came from a browser,
# so we send a simple, honest User-Agent that identifies this project.
USER_AGENT = "fpl-assistant/0.1 (learning project)"

# Where the local SQLite cache lives. This is a generated file, not source, so
# it is gitignored (see .gitignore).
DB_PATH = "data/fpl.db"

# FPL encodes a player's position as element_type 1-4. We store a readable
# label instead of the magic number (mapped once, at ingestion).
POSITION_MAP = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}
