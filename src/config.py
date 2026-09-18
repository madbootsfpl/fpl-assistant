"""Central configuration for MADBOOTS (the fpl-assistant package — internal name kept, ADR-103).

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
ENTRY_TRANSFERS_PATH = "/entry/{}/transfers/"

# A classic league's standings (ADR-141). Public for classic leagues; H2H is a different endpoint and is not
# used. One page is 50 rows and carries `rank`, `last_rank`, `total` and `event_total` — so the league table
# *and* who is climbing cost a single call.
LEAGUE_STANDINGS_PATH = "/leagues-classic/{}/standings/"

# The global "Overall" league. Every FPL manager is in it, so its first page IS the top 50 in the world —
# which makes the "elite manager comparison" the same code as any other league, pointed at this id (ADR-141).
ELITE_LEAGUE_ID = 314

# Seconds to wait between element-summary calls during a history backfill (ADR-027).
# A full backfill is one call per player (~567), so we throttle to respect rate limits
# (~0.3s ≈ a few minutes). It's a fetch-once-per-season job, kept out of `refresh`.
HISTORY_THROTTLE = 0.3

# Local LLM for the `ask` command (ADR-034). Ollama's generate endpoint; the model is one
# pulled locally. The LLM is OPTIONAL — `ask` degrades to the analytics decision if it's absent.
OLLAMA_URL = "http://localhost:11434/api/generate"
# ADR-168 §🔬 — narration moved llama3.2 → qwen3:8b (2026-08-30). Measured side by side on four answers:
# llama3.2 reframed a risk as a benefit ("selling Hume frees £0.5m"), dropped a differential warning, and
# wrote "increases projected points by £25.4" — a currency symbol on a points figure. qwen3:8b named the
# risk *as* a risk and carried the units. It is the model the extraction already uses (ADR-157).
OLLAMA_MODEL = "qwen3:8b"

# …and the timeout has to rise with it. **60s was silently failing**: qwen3 needs ~90s on the longest prompt
# (the chip strategy, whose facts dict is the biggest), so narration returned None and the UI showed
# "Start Ollama for a written summary" on a machine where Ollama was running perfectly. A silent timeout that
# blames the user for a missing service is the worst of both.
OLLAMA_TIMEOUT = 240

# …and a SEPARATE model for headline extraction (ADR-151/157). The two jobs want different things and one
# constant was quietly making that choice for both: narration wants warmth, speed and a sentence, and runs
# while a person waits; extraction wants the same answer every time and runs once, in `refresh`, unattended.
# Measured on the live feed rather than assumed — see ADR-157 for the numbers.
OLLAMA_EXTRACT_MODEL = "qwen3:8b"
OLLAMA_EXTRACT_TIMEOUT = 120

# How long extraction may hold `refresh` (ADR-151, raised in ADR-157). Measured, not guessed: the live feed
# offers 112 headlines and the chosen model reads one in ~1.0s median, so a full read is ~110-150s. At the
# old 180s that was 60-80% of the budget — and running out is silent truncation, the failure mode six sprints
# have been spent removing. `refresh` is a manual, local, occasional command; the headroom is worth more.
EXTRACT_BUDGET_SECONDS = 300.0

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
# pins this). The GW1 flip (ADR-101 / docs/GW1_RUNBOOK.md): run `history --backfill`, then at ~GW4+
# `python app.py calibrate --weight form` — it backtests + recommends a value; set it here + update the
# invariance test + commit. FORM_GAMEWEEKS is the rolling window (last N GWs).
FORM_WEIGHT = 0.0
FORM_GAMEWEEKS = 5

# 🚫 There is no SET_PIECE_WEIGHT, and that is a decision (ADR-096 → CLOSED by ADR-190, 2026-09-13).
# The term priced a per-90 bonus for dead-ball takers, on the fallback/cold-start tiers only — never on the
# trusted historical baseline, which already contains an established taker's penalties.
#
# That exclusion is correct and it is also what made the term impossible to calibrate. Of 43 first-choice
# duty-holders it could reach **9**; `history_by_code` holds only completed seasons, so those 9 are fixed for
# the season. Nine players cannot shift a rank correlation over 626 — at weight 0.5 the term produced a
# ranking **0.99998** correlated with the baseline's. §B0's bar was not unmet, it was **unreachable**, and it
# would have stayed unreachable at GW6, at GW10 and at any n.
#
# So the weight is gone rather than left at 0 forever, which is the furniture ADR-101's stopping rule exists
# to prevent. **Set-piece duty is still shown** — the ⚽/🚩/🎯 glyphs on the pitch (`crowd.SET_PIECES`) are
# independent of this and always were. The app tells you who takes the penalties; it no longer claims to know
# what that is worth. ⚠️ Re-adding a weight here needs a way to *measure* it first (ADR-190 Option 3: score a
# scoped term on the population it scopes to), not just a plausible per-90 number.

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
USER_AGENT = "madboots/0.1 (learning project)"   # brand courtesy string sent to the FPL API (ADR-103)

# Where the local SQLite cache lives. The live cache (fpl.db) is a generated file, gitignored (see
# .gitignore). On a fresh clone / a public deploy it's absent, so fall back to the committed **seed
# snapshot** (seed.db) — so the app still has data to show (ADR-053). `SEED_DB_PATH` is named so the web
# can tell "read-only demo (seed)" from "a live cache" (ADR-056 — the local-only refresh).
SEED_DB_PATH = "data/seed.db"
# The live cache written by `refresh` (gitignored). Named so `reseed` can target it explicitly —
# even when it doesn't exist yet and DB_PATH has fallen back to the seed.
LIVE_DB_PATH = "data/fpl.db"
# ⭐ **Postgres, when configured — and the DSN travels in the same variable as the path** (ADR-211 2b).
# `src/db.py` already decides backend from the string, so setting this one environment variable points every
# `Storage()` in the CLI and the web app at Postgres without a second parameter or a mode flag anywhere.
#
# ⭐ **This variable IS the fallback mechanism.** Unset it and the app is byte-for-byte what it was: the live
# cache if one exists, else the committed seed. That is deliberately simpler — and safer — than an automatic
# runtime failover, because a failover that silently serves last month's snapshot while the pipeline is dead
# is the failure mode this phase exists to remove. Where a *configured* Postgres cannot be reached, `Storage`
# falls back to the seed and says so loudly (`storage.fallback_reason()`), rather than quietly.
DATABASE_URL = os.environ.get("FPL_DATABASE_URL") or None

DB_PATH = DATABASE_URL or (LIVE_DB_PATH if os.path.exists(LIVE_DB_PATH) else SEED_DB_PATH)

# FPL encodes a player's position as element_type 1-4. We store a readable
# label instead of the magic number (mapped once, at ingestion).
POSITION_MAP = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}

# Club clean-sheet term for DEF/GK (ADR-188) — DORMANT (CLEAN_SHEET_WEIGHT = 0). A defender's xP is his own
# pts/90 × minutes × OPPONENT difficulty; nothing prices the defence he plays behind. Team DNA has shown the
# number for weeks (Arsenal 75% vs Sunderland 25% the day this was written) without the recommendation engine
# using it — owner-reported, on a suggestion to sell the Arsenal defender for the Sunderland one.
#
# Applied as a DELTA against the league mean, because a player's own pts/90 already contains the clean sheets
# he kept at his old rate; only the difference is new information (the same shape as ADR-097's DefCon term).
#
# ⚠️ **The INPUT changed 2026-09-17 (ADR-195): the club rate is now xGC/90 through a Poisson step, not the
# clean-sheet rate.** ADR-188 measured the rate, read a null, and a second look (ADR-190 Option 3) read a null
# too — so the owner was told twice his instinct was unsupported. The rate is the reason: over four gameweeks
# it takes **5 distinct values across 20 clubs**, and its 0.00 bucket holds **six clubs spanning the 4th-best
# defence and the worst**. Arsenal and Hull share a rate of 0.75 on xGC of 0.68 and 1.49.
# ⭐⭐ A NULL IS A STATEMENT ABOUT THE INSTRUMENT AS MUCH AS ABOUT THE WORLD.
#
# ⚠️ Swept at the **GW6** sitting, not GW4: three weights are already queued there and a fourth on the same
# thin sample is how a noise result ships. Prediction recorded in GW1_RUNBOOK §B0 *before* the sweep —
# small positive ≈0.05-0.20, quite possibly zero, and **a large gain is a warning, not a win** (it would mean
# the term is re-ranking by club quality rather than adding defensive information — that caveat survives the
# instrument change, because it was never the thing that was wrong).
CLEAN_SHEET_WEIGHT = 0.0

# How far forward an availability flag is evidence (ADR-206 §2/§3). FPL publishes `chance_of_playing` about
# the UPCOMING match — it is a *now* field with no "as of" (ADR-203) — so applying it to a fixture five weeks
# out states something the source never said. Beyond this window a flagged player reverts to his ordinary
# minutes weight; within it he keeps the discount.
#
# ⚠️ **DECLARED, NOT MEASURED** (ADR-199's rule, stated rather than hidden). It cannot be measured yet: it
# would need a history of flags against what players went on to do, and ADR-203 only began recording that on
# 2026-09-17. 8 days is one fixture cycle — the flag covers the match it was published for and the one that
# may follow in the same week, and nothing further. **Re-measure at the GW8 review**, when the availability log
# has a month in it.
#
# ⭐ Measured in DAYS, not gameweeks, which is what makes an international break need no concept of its own:
# GW6 kicks off 19 days after GW5, so a flag raised today simply cannot reach it.
FLAG_HORIZON_DAYS = 8
