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

# ClubElo — the second (external) data source: team Elo ratings (ADR-010).
# The API returns CSV for a given date at CLUBELO_BASE_URL/<YYYY-MM-DD>.
CLUBELO_BASE_URL = "http://api.clubelo.com"

# How long (in seconds) to wait for the API before giving up.
REQUEST_TIMEOUT = 10

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
