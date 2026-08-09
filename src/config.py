"""Central configuration for the FPL Assistant.

Keeping endpoints, timeouts and headers in one place means the rest of the code
never hard-codes URLs, and tests (or a future config file) can override them
easily. See docs/03_Architecture/Architecture.md (§4 Components — "Config").
"""

import os

# The app version, stamped on analytics events (ADR-100) so usage/perf can be read per release.
APP_VERSION = "0.0.1"

# Base URL for the official FPL API.
FPL_BASE_URL = "https://fantasy.premierleague.com/api"

# Static endpoint: all players, teams and gameweeks in a single payload.
BOOTSTRAP_STATIC_PATH = "/bootstrap-static/"

# Fixtures endpoint: all matches (home/away teams, difficulty, gameweek).
FIXTURES_PATH = "/fixtures/"

# Per-player endpoint (ADR-027): a player's fixtures, this-season per-GW history, and
# `history_past` (past-season summaries). `{}` is the per-season element id.
ELEMENT_SUMMARY_PATH = "/element-summary/{}/"

# A manager's public entry (Sprint 064, ADR-058): metadata (name, current_event) and their squad picks for
# a gameweek. Picks are **public only after that gameweek's deadline** (404 before) — GW1 = 2026-08-21.
# `{}` is the manager (entry) id; the picks path takes (entry_id, gameweek).
ENTRY_PATH = "/entry/{}/"
ENTRY_PICKS_PATH = "/entry/{}/event/{}/picks/"

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

# Community Signals (Sprint 067, ADR-059) — the public Reddit RSS feed (no auth; the `.json` API 403s).
# `{}` is the subreddit. Best-effort + rate-limited → cache + degrade gracefully. 5s budget like ClubElo.
REDDIT_RSS_URL = "https://www.reddit.com/r/{}/.rss"
REDDIT_SUBREDDIT = "FantasyPL"
REDDIT_TIMEOUT = 5
# How many recent posts to pull for the "Talked about" buzz count (ADR-076). Reddit's RSS max is 100;
# a bigger sample makes mention counts meaningful (the default 25 posts left most players at "1 mention").
REDDIT_RSS_LIMIT = 100
# The weekly "top discussions" variant (Sprint 115, US-292) — the same public RSS, `top` sorted over the week.
REDDIT_TOP_WEEK_URL = "https://www.reddit.com/r/{}/top/.rss?t=week"

# Media-headlines lens (Sprint 115, ADR-093) — public RSS/Atom feeds, no auth, best-effort (cached + gated +
# degrade). A display lens (never xP). Add/remove a feed by editing this list. To add a YouTube creator, find
# its channel id (open the channel → View source → search "channelId", a `UC…` value) and append:
#   {"name": "YouTube — <creator>", "url": MEDIA_YOUTUBE_URL.format("UCxxxxxxxxxxxxxxxxxxxxxx")}
MEDIA_YOUTUBE_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
MEDIA_FEEDS = [
    {"name": "Fantasy Football Scout", "url": "https://www.fantasyfootballscout.co.uk/feed/"},
    {"name": "BBC Football", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml"},
]
MEDIA_FEED_TIMEOUT = 5        # per-feed budget (best-effort, like Reddit/ClubElo)
MEDIA_FEED_LIMIT = 6         # headlines shown per source

# In-season form blend (ADR-060) — DORMANT until GW1 (2026-08-21). The one xP recipe (ADR-041)
# blends a rolling, minutes-aware points-per-90 (from per-GW `player_history`) into a player's rate:
#     rate = (1 − w)·base + w·form_pp90,   w = FORM_WEIGHT × confidence
# Preseason there is no per-GW history AND FORM_WEIGHT is 0, so xP is unchanged (an invariance test
# pins this). The GW1 flip: run `history --backfill` (now also per-GW), then raise FORM_WEIGHT
# (calibrate then — start small, e.g. 0.3). FORM_GAMEWEEKS is the rolling window (last N GWs).
FORM_WEIGHT = 0.0
FORM_GAMEWEEKS = 5

# Set-piece xP term (ADR-096) — DORMANT (SET_PIECE_WEIGHT = 0). The one xP recipe adds a small per-90
# rate bonus for set-piece takers (penalties > corners/free-kicks) — but ONLY on the fallback/current
# rate tiers, NOT the trusted historical baseline (which already prices an established taker's pens →
# double-counting). At 0 it's a no-op, so xP is unchanged today (an invariance test pins this). GW1:
# raise the weight + backtest on real returns; start small.
SET_PIECE_WEIGHT = 0.0

# DefCon fixture magnifier (ADR-097) — DORMANT (DEFCON_MAGNIFIER_WEIGHT = 0). The one xP recipe re-weights
# the DefCon points ALREADY in the baseline by fixture — a delta `defcon_pts_per_match · (magnifier − 1)`
# (more DefCon vs a strong opponent, less vs a weak one). 0 at neutral / weight 0 → no delta, so xP is
# unchanged today (an invariance test pins this) and it never double-counts. GW1: raise the weight +
# calibrate DEFCON_P_SCALE / the magnifier band on real DefCon returns.
DEFCON_MAGNIFIER_WEIGHT = 0.0

# How long (in seconds) to wait for the API before giving up.
REQUEST_TIMEOUT = 10

# ClubElo is best-effort, so it gets a tighter budget than the required FPL source
# (ADR-021): a shorter timeout + fewer retries → a sustained outage degrades fast.
# A healthy ClubElo answers in ~1–2s, so 5s is a safe margin.
CLUBELO_TIMEOUT = 5

# Where the user's saved squads live (ADR-024). This is *user state*, kept separate from the reference
# cache (fpl.db), gitignored. On a fresh clone / a public deploy it's absent — fall back to the committed
# **demo** squads (seed_squads.json) so the web pages have a squad to show (ADR-054).
SQUADS_PATH = "data/squads.json" if os.path.exists("data/squads.json") else "data/seed_squads.json"

# Where the CLI persists the last conversational turn (ADR-091) so a follow-up ("why?", "and the next?") works
# across separate `ask`/`chat` runs. Local, single-user, git-ignored (data/*.json). The multi-user web never
# writes it — it keeps per-session `st.session_state`.
CHAT_CONTEXT_PATH = "data/chat_context.json"

# The FPL API can reject requests that don't look like they came from a browser,
# so we send a simple, honest User-Agent that identifies this project.
USER_AGENT = "fpl-assistant/0.1 (learning project)"

# Where the local SQLite cache lives. The live cache (fpl.db) is a generated file, gitignored (see
# .gitignore). On a fresh clone / a public deploy it's absent, so fall back to the committed **seed
# snapshot** (seed.db) — so the app still has data to show (ADR-053). `SEED_DB_PATH` is named so the web
# can tell "read-only demo (seed)" from "a live cache" (ADR-056 — the local-only refresh).
SEED_DB_PATH = "data/seed.db"
# The live cache written by `refresh` (gitignored). Named so `reseed` can target it explicitly —
# even when it doesn't exist yet and DB_PATH has fallen back to the seed.
LIVE_DB_PATH = "data/fpl.db"
DB_PATH = LIVE_DB_PATH if os.path.exists(LIVE_DB_PATH) else SEED_DB_PATH

# FPL encodes a player's position as element_type 1-4. We store a readable
# label instead of the magic number (mapped once, at ingestion).
POSITION_MAP = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}
