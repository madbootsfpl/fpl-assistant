"""Storage for FPL data — SQLite locally, Postgres for the autonomous pipeline (ADR-211).

This is the project's storage layer. It knows about the database but nothing
about HTTP or how data is displayed (Architecture §3, §6). Rows are upserted on
the stable FPL id, so re-running the fetch refreshes existing rows instead of
creating duplicates.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src import config, db
from src.fpl_rules import DEADLINE_LEAD
from src.models import Fixture, Player, PlayerGameweek, PlayerSeason, Team

CREATE_TEAMS = """
CREATE TABLE IF NOT EXISTS teams (
    id                    INTEGER PRIMARY KEY,
    name                  TEXT NOT NULL,
    short_name            TEXT NOT NULL,
    strength_overall_home INTEGER,
    strength_overall_away INTEGER,
    elo                   REAL,
    code                  INTEGER
)
"""

# Columns added to tables after they first shipped. On an existing database,
# CREATE TABLE IF NOT EXISTS leaves old tables untouched, so we add any missing
# columns with a light migration (see _migrate). Keyed by table name.
_MIGRATIONS = {
    # ADR-211 2d — added after `data_status` shipped in 2b, and the first columns this project has ever had to
    # migrate onto a *Postgres* database. `_migrate` gained that ability in the same stage; see its note.
    "data_status": {
        "backfilled_at": "TEXT",
        "backfilled_event": "INTEGER",
    },
    "teams": {
        "strength_overall_home": "INTEGER",
        "strength_overall_away": "INTEGER",
        "elo": "REAL",
        "code": "INTEGER",              # the FPL asset code, for the badge URL (Sprint 055)
    },
    # Per-GW columns added in Sprint 179 (ADR-128): the season aggregates on `players` are a running total,
    # so a trend line and a W-D-L dot need the *week itself*. Existing databases gain them without a reseed.
    "player_history": {
        # ADR-201 — the column an older cache gains before `_rekey_history` folds it into the key.
        "season": "TEXT NOT NULL DEFAULT ''",
        "team_h_score": "INTEGER",
        "team_a_score": "INTEGER",
        "goals_scored": "INTEGER",
        "assists": "INTEGER",
        "clean_sheets": "INTEGER",
        "goals_conceded": "INTEGER",
        "saves": "INTEGER",
        "bonus": "INTEGER",
        "bps": "INTEGER",
        "xg": "REAL",
        "xa": "REAL",
        "xgi": "REAL",
        "xgc": "REAL",
        "ict_index": "REAL",
        "influence": "REAL",
        "creativity": "REAL",
        "threat": "REAL",
        "defcon": "INTEGER",
        "value": "INTEGER",
    },
    "players": {
        "points_per_game": "REAL",
        "status": "TEXT",
        "ep_next": "REAL",
        "xg": "REAL",
        "xa": "REAL",
        "xgi": "REAL",
        "xgc": "REAL",
        "goals_scored": "INTEGER",
        "assists": "INTEGER",
        "minutes": "INTEGER",
        "defcon": "INTEGER",
        "defcon_per90": "REAL",
        "cbi": "INTEGER",
        "tackles": "INTEGER",
        "recoveries": "INTEGER",
        "chance": "INTEGER",
        "news": "TEXT",
        "scout_news_link": "TEXT",       # source link for the news (Sprint 064, ADR-058)
        "code": "INTEGER",
        "penalties_order": "INTEGER",
        "corners_order": "INTEGER",       # first-choice set-piece takers (Sprint 095, ADR-081)
        "freekicks_order": "INTEGER",
        "selected_by": "REAL",
        # Crowd & sentiment signals (Sprint 060, ADR-057) — a display lens, not xP inputs.
        "transfers_in_event": "INTEGER",
        "transfers_out_event": "INTEGER",
        "cost_change_event": "INTEGER",
        "cost_change_start": "INTEGER",
        "form": "REAL",
        "ict_index": "REAL",
        "influence": "REAL",
        "creativity": "REAL",
        "threat": "REAL",
        "value_form": "REAL",
    },
}

CREATE_PLAYERS = """
CREATE TABLE IF NOT EXISTS players (
    id              INTEGER PRIMARY KEY,
    first_name      TEXT,
    second_name     TEXT,
    web_name        TEXT,
    team_id         INTEGER REFERENCES teams(id),
    position        TEXT,
    price           REAL,
    total_points    INTEGER,
    points_per_game REAL,
    status          TEXT,
    ep_next         REAL,
    xg              REAL,
    xa              REAL,
    xgi             REAL,
    xgc             REAL,
    goals_scored    INTEGER,
    assists         INTEGER,
    minutes         INTEGER,
    defcon          INTEGER,
    defcon_per90    REAL,
    cbi             INTEGER,
    tackles         INTEGER,
    recoveries      INTEGER,
    chance          INTEGER,
    news            TEXT,
    scout_news_link TEXT,
    code            INTEGER,
    penalties_order INTEGER,
    corners_order   INTEGER,
    freekicks_order INTEGER,
    selected_by     REAL,
    transfers_in_event  INTEGER,
    transfers_out_event INTEGER,
    cost_change_event   INTEGER,
    cost_change_start   INTEGER,
    form                REAL,
    ict_index           REAL,
    influence           REAL,
    creativity          REAL,
    threat              REAL,
    value_form          REAL
)
"""

# Past-season history (ADR-027). Keyed by element_code (stable across seasons) +
# season_name. NO foreign key to players — history outlives a player's presence in
# the current game (a departed player still has past seasons), like ADR-024's squads.
CREATE_HISTORY_PAST = """
CREATE TABLE IF NOT EXISTS player_history_past (
    element_code               INTEGER NOT NULL,
    season_name                TEXT NOT NULL,
    total_points               INTEGER,
    minutes                    INTEGER,
    goals_scored               INTEGER,
    assists                    INTEGER,
    clean_sheets               INTEGER,
    goals_conceded             INTEGER,
    expected_goals             REAL,
    expected_assists           REAL,
    expected_goal_involvements REAL,
    expected_goals_conceded    REAL,
    defensive_contribution     INTEGER,
    starts                     INTEGER,
    start_cost                 REAL,
    end_cost                   REAL,
    PRIMARY KEY (element_code, season_name)
)
"""

# Per-GW history (ADR-060) — the current season, one row per player per gameweek. Keyed by
# element_code (stable id, so form joins by the same code the xP baseline uses) + round. A
# current-season working set: a new season re-backfills and overwrites round-for-round (the
# per-GW payload carries no season name). No FK to players — history outlives presence (ADR-027).
CREATE_HISTORY = """
CREATE TABLE IF NOT EXISTS player_history (
    element_code   INTEGER NOT NULL,
    round          INTEGER NOT NULL,
    minutes        INTEGER,
    total_points   INTEGER,
    was_home       INTEGER,
    opponent_team  INTEGER,
    fixture        INTEGER NOT NULL,
    kickoff_time   TEXT,
    team_h_score   INTEGER,
    team_a_score   INTEGER,
    goals_scored   INTEGER,
    assists        INTEGER,
    clean_sheets   INTEGER,
    goals_conceded INTEGER,
    saves          INTEGER,
    bonus          INTEGER,
    bps            INTEGER,
    xg             REAL,
    xa             REAL,
    xgi            REAL,
    xgc            REAL,
    ict_index      REAL,
    influence      REAL,
    creativity     REAL,
    threat         REAL,
    defcon         INTEGER,
    value          INTEGER,
    -- ⚠️ **`season` is part of the identity (ADR-201), and without it this table could only ever hold one.**
    -- FPL restarts `fixture` ids at 1 every August, so `(element_code, fixture)` silently collided across
    -- seasons: GW1 of the new season would overwrite GW1 of the old, row for row, with no error. The
    -- per-match record is unrecoverable once gone — `element-summary` serves per-match detail for the
    -- CURRENT season only; past seasons come back as one aggregate row per player. Every rollover was
    -- destroying a season of training data that FPL will not sell back.
    season         TEXT NOT NULL DEFAULT '',
    -- Keyed by the FIXTURE, not the gameweek (ADR-129). FPL's `element-summary` sends one entry per match, so
    -- in a double gameweek a player has two rows sharing a `round` — keying on the round made the second
    -- silently overwrite the first, turning a 20-point double into a 12-point single. `round` stays a column
    -- because grouping by gameweek is what the analytics want; it just isn't an identity.
    PRIMARY KEY (element_code, season, fixture)
)
"""

# Resolved news events (ADR-151), written at refresh time and read by the app. Keyed by (element_id, title)
# so re-running an enrichment is idempotent: the same headline about the same player updates rather than
# duplicating. `title` is stored so a claim can always be checked against its source — a flag that says
# "Romano reports a move" must be able to show the sentence it came from.
CREATE_HEADLINE_EVENTS = """
CREATE TABLE IF NOT EXISTS headline_events (
    element_id  INTEGER NOT NULL,
    title       TEXT    NOT NULL,
    kind        TEXT    NOT NULL,
    source      TEXT,
    seen_at     TEXT,
    PRIMARY KEY (element_id, title)
)
"""

UPSERT_HEADLINE_EVENT = """
INSERT INTO headline_events (element_id, title, kind, source, seen_at)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(element_id, title) DO UPDATE SET
    kind    = excluded.kind,
    source  = excluded.source,
    seen_at = excluded.seen_at
"""

CREATE_AVAILABILITY = """
CREATE TABLE IF NOT EXISTS player_availability (
    element_code INTEGER NOT NULL,
    -- ⚠️ **`observed_at`, not `changed_at`, and the distinction is the whole honesty of this table.**
    -- ADR-201 stamps a match with its own kickoff, because a match HAS a time. Availability does not:
    -- FPL serves `status` / `chance` / `news` as a *now* field with no "as of", so the only timestamp
    -- that exists is when we looked. Calling it `changed_at` would claim knowledge of a moment nobody
    -- recorded — the flag may have gone up hours before the refresh that first saw it.
    observed_at  TEXT    NOT NULL,   -- when this value was first SEEN
    last_seen_at TEXT    NOT NULL,   -- when it was last CONFIRMED still true
    status       TEXT,
    chance       INTEGER,
    news         TEXT,
    PRIMARY KEY (element_code, observed_at)
)
"""

CREATE_TRANSFER_FLOW = """
CREATE TABLE IF NOT EXISTS player_transfer_flow (
    element_code INTEGER NOT NULL,
    -- The gameweek the counter is accumulating TOWARD — i.e. the next deadline at the moment we looked, not
    -- the gameweek being played. FPL resets `transfers_in_event` / `transfers_out_event` at every deadline,
    -- so this column is what makes two readings comparable at all: without it the table is a pile of numbers
    -- from different weeks that look like one series.
    event        INTEGER NOT NULL,
    observed_at  TEXT    NOT NULL,   -- when we looked (never "when it changed" — ADR-203's distinction)
    -- ⭐⭐ **The phase, and it is the whole reason this table exists.** These counters are an ACCUMULATION:
    -- they start at zero after a deadline and climb all week. A reading is therefore meaningless without
    -- knowing how far through the cycle it was taken — the same week's data gives p10 −3,901 on day one and
    -- −14,992 on day five (ADR-210). Storing the value without the phase would build a series that cannot be
    -- compared with itself, which is the fault ADR-190 hit when it tried to re-measure the constant.
    hours_to_deadline REAL,
    transfers_in      INTEGER,
    transfers_out     INTEGER,
    selected_by       REAL,          -- the divisor: `price_pressure` is net transfers per 1% owned (ADR-092)
    -- One row per player per event, upserted. So the row for event N settles on the LAST reading taken
    -- before N's deadline — the end-of-cycle total, which is the one point in the week that is comparable
    -- across weeks. Intermediate readings are deliberately not kept: the live threshold no longer needs the
    -- ramp (ADR-210), and a row per refresh is ~330k a season to describe a curve nothing reads.
    PRIMARY KEY (element_code, event)
)
"""

CREATE_DATA_STATUS = """
CREATE TABLE IF NOT EXISTS data_status (
    -- A single row. ⭐ **Freshness has to be a VALUE once the data stops being a file** (ADR-211 2b): the
    -- Streamlit sidebar read the SQLite file's mtime, and a Postgres table has no mtime. More than that, an
    -- mtime says when someone *wrote*, never whether the write succeeded — which is the distinction this
    -- phase turns on, because an unattended pipeline can fail unattended.
    id            INTEGER PRIMARY KEY,
    refreshed_at  TEXT,      -- when the last SUCCESSFUL refresh completed
    attempted_at  TEXT,      -- when a refresh last RAN, successful or not
    event         INTEGER,   -- the gameweek the data describes
    ok            INTEGER,   -- did the last attempt pass validation?
    note          TEXT,      -- why not, when it did not
    -- The per-gameweek history walk is a different job on a different clock (ADR-211 2d): ~659 throttled
    -- requests, once per gameweek, after the results post. Its own stamp so a slow or failed backfill is
    -- visible without being mistaken for a stale core refresh.
    backfilled_at    TEXT,
    backfilled_event INTEGER
)
"""

CREATE_FIXTURES = """
CREATE TABLE IF NOT EXISTS fixtures (
    id                INTEGER PRIMARY KEY,
    event             INTEGER,
    team_h            INTEGER REFERENCES teams(id),
    team_a            INTEGER REFERENCES teams(id),
    team_h_difficulty INTEGER,
    team_a_difficulty INTEGER,
    finished          INTEGER,
    kickoff_time      TEXT
)
"""

# Upsert: insert a new row, or refresh the existing one if the id already exists.
UPSERT_TEAM = """
INSERT INTO teams (id, name, short_name, strength_overall_home, strength_overall_away, code)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name                  = excluded.name,
    short_name            = excluded.short_name,
    strength_overall_home = excluded.strength_overall_home,
    strength_overall_away = excluded.strength_overall_away,
    code                  = excluded.code
"""

UPSERT_PLAYER = """
INSERT INTO players
    (id, first_name, second_name, web_name, team_id, position, price, total_points,
     points_per_game, status, ep_next, xg, xa, xgi, xgc,
     goals_scored, assists, minutes,
     defcon, defcon_per90, cbi, tackles, recoveries,
     chance, news, scout_news_link, code, penalties_order, corners_order, freekicks_order, selected_by,
     transfers_in_event, transfers_out_event, cost_change_event, cost_change_start,
     form, ict_index, influence, creativity, threat, value_form)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    first_name      = excluded.first_name,
    second_name     = excluded.second_name,
    web_name        = excluded.web_name,
    team_id         = excluded.team_id,
    position        = excluded.position,
    price           = excluded.price,
    total_points    = excluded.total_points,
    points_per_game = excluded.points_per_game,
    status          = excluded.status,
    ep_next         = excluded.ep_next,
    xg              = excluded.xg,
    xa              = excluded.xa,
    xgi             = excluded.xgi,
    xgc             = excluded.xgc,
    goals_scored    = excluded.goals_scored,
    assists         = excluded.assists,
    minutes         = excluded.minutes,
    defcon          = excluded.defcon,
    defcon_per90    = excluded.defcon_per90,
    cbi             = excluded.cbi,
    tackles         = excluded.tackles,
    recoveries      = excluded.recoveries,
    chance          = excluded.chance,
    news            = excluded.news,
    scout_news_link = excluded.scout_news_link,
    code            = excluded.code,
    penalties_order = excluded.penalties_order,
    corners_order   = excluded.corners_order,
    freekicks_order = excluded.freekicks_order,
    selected_by     = excluded.selected_by,
    transfers_in_event  = excluded.transfers_in_event,
    transfers_out_event = excluded.transfers_out_event,
    cost_change_event   = excluded.cost_change_event,
    cost_change_start   = excluded.cost_change_start,
    form                = excluded.form,
    ict_index           = excluded.ict_index,
    influence           = excluded.influence,
    creativity          = excluded.creativity,
    threat              = excluded.threat,
    value_form          = excluded.value_form
"""

UPSERT_HISTORY_PAST = """
INSERT INTO player_history_past
    (element_code, season_name, total_points, minutes, goals_scored, assists,
     clean_sheets, goals_conceded, expected_goals, expected_assists,
     expected_goal_involvements, expected_goals_conceded, defensive_contribution,
     starts, start_cost, end_cost)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(element_code, season_name) DO UPDATE SET
    total_points               = excluded.total_points,
    minutes                    = excluded.minutes,
    goals_scored               = excluded.goals_scored,
    assists                    = excluded.assists,
    clean_sheets               = excluded.clean_sheets,
    goals_conceded             = excluded.goals_conceded,
    expected_goals             = excluded.expected_goals,
    expected_assists           = excluded.expected_assists,
    expected_goal_involvements = excluded.expected_goal_involvements,
    expected_goals_conceded    = excluded.expected_goals_conceded,
    defensive_contribution     = excluded.defensive_contribution,
    starts                     = excluded.starts,
    start_cost                 = excluded.start_cost,
    end_cost                   = excluded.end_cost
"""

UPSERT_HISTORY = """
INSERT INTO player_history
    (element_code, season, round, minutes, total_points, was_home, opponent_team, fixture, kickoff_time,
     team_h_score, team_a_score, goals_scored, assists, clean_sheets, goals_conceded, saves, bonus, bps, xg,
     xa, xgi, xgc, ict_index, influence, creativity, threat, defcon, value)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(element_code, season, fixture) DO UPDATE SET
    minutes        = excluded.minutes,
    total_points   = excluded.total_points,
    was_home       = excluded.was_home,
    opponent_team  = excluded.opponent_team,
    fixture        = excluded.fixture,
    kickoff_time   = excluded.kickoff_time,
    team_h_score   = excluded.team_h_score,
    team_a_score   = excluded.team_a_score,
    goals_scored   = excluded.goals_scored,
    assists        = excluded.assists,
    clean_sheets   = excluded.clean_sheets,
    goals_conceded = excluded.goals_conceded,
    saves          = excluded.saves,
    bonus          = excluded.bonus,
    bps            = excluded.bps,
    xg             = excluded.xg,
    xa             = excluded.xa,
    xgi            = excluded.xgi,
    xgc            = excluded.xgc,
    ict_index      = excluded.ict_index,
    influence      = excluded.influence,
    creativity     = excluded.creativity,
    threat         = excluded.threat,
    defcon         = excluded.defcon,
    value          = excluded.value
"""

UPSERT_FIXTURE = """
INSERT INTO fixtures
    (id, event, team_h, team_a, team_h_difficulty, team_a_difficulty, finished, kickoff_time)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    event             = excluded.event,
    team_h            = excluded.team_h,
    team_a            = excluded.team_a,
    team_h_difficulty = excluded.team_h_difficulty,
    team_a_difficulty = excluded.team_a_difficulty,
    finished          = excluded.finished,
    kickoff_time      = excluded.kickoff_time
"""


# ⭐ **Why a reader never creates the schema** (ADR-211 2b). On SQLite the database *is* the app's own cache
# and bootstrapping it is right. On Postgres it is a shared database the **pipeline** owns, and a reader that
# runs `CREATE TABLE IF NOT EXISTS` against a DSN pointing somewhere unexpected would build eight empty tables
# and then render "no data" — reporting an empty league instead of a misconfiguration. ⭐ *The thing that owns
# a schema should be the only thing that creates it*, so the web app asks whether the schema is there and
# declines to invent it.
#
# Set by `Storage` when a configured Postgres could not be used and the committed seed was served instead.
# ⚠️ Module-level on purpose: every `Storage()` in the web app is short-lived, so the *instance* cannot carry
# this to the sidebar that has to display it.
_FALLBACK_REASON: str | None = None


def _schema_present(conn) -> bool:
    """Does this database already carry the MadBoots schema? One cheap query, not eight DDL round trips.

    `players` stands in for all eight tables: they are created together in `_init_schema`, so a database with
    that table and not the rest is not a state this app can produce.
    """
    try:
        conn.execute("SELECT 1 FROM players LIMIT 1").fetchall()
    except db.MISSING_TABLE:
        return False
    return True


def fallback_reason() -> str | None:
    """Why the app is serving the seed instead of the Postgres it was configured for — or None (ADR-211).

    ⭐ **This exists so the degradation cannot be silent.** Serving a month-old snapshot while the pipeline is
    dead, and looking healthy doing it, is precisely the failure this phase was created to remove — so the
    sidebar renders this as a warning, and a test asserts that it does.
    """
    return _FALLBACK_REASON


class Storage:
    """The storage layer — SQLite by default, Postgres when handed a DSN (ADR-211).

    One body of SQL, two backends. `db_path` takes either a file path or a `postgresql://…` URL; `src/db.py`
    is the only module that knows which is which. Nothing above this class changes, because the DSN travels in
    the argument every call site already passes.
    """

    def __init__(self, db_path: str = config.DB_PATH, *, ensure_schema: bool | None = None):
        """Open `db_path` — a SQLite file or a Postgres DSN.

        `ensure_schema` decides whether this connection may **create** tables. It defaults to *yes* for SQLite
        (the local cache has to bootstrap itself) and *no* for Postgres (the pipeline owns that schema, see the
        note above). The pipeline passes `ensure_schema=True` explicitly, which is the one place the decision
        is worth stating out loud.
        """
        global _FALLBACK_REASON

        # ⭐ **A configured Postgres that cannot be used falls back to the seed — visibly.** Two failures are
        # worth telling apart and both end here: the server is unreachable, or it is reachable and holds no
        # MadBoots schema (a DSN pointing at the wrong database). Either way the app still renders, and
        # `fallback_reason()` makes the sidebar say why.
        if db.is_postgres(db_path):
            # ⭐⭐ **A READER may degrade; a WRITER must not.** `ensure_schema=True` marks the pipeline, and a
            # refresh that cannot reach Postgres has to **fail loudly** — because the fallback path is the
            # committed `seed.db`, so degrading here would quietly write a live refresh into the repo's
            # snapshot and report success. ⭐ *The safe direction to fail differs by what the caller is for.*
            if ensure_schema:
                self.conn = db.connect(db_path)
                self.is_postgres = True
                self._init_schema()
                _FALLBACK_REASON = None
                return
            try:
                conn = db.connect(db_path)
                if not _schema_present(conn):
                    conn.close()
                    raise RuntimeError("no MadBoots schema in that database — has the pipeline run?")
            except Exception as exc:                       # noqa: BLE001 — any failure degrades the same way
                _FALLBACK_REASON = f"{type(exc).__name__}: {exc}"
                db_path = config.SEED_DB_PATH
            else:
                _FALLBACK_REASON = None
                self.conn = conn
                self.is_postgres = True
                return

        # Make sure the parent folder exists (e.g. data/) before connecting — a file path only.
        if not db.is_postgres(db_path) and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = db.connect(db_path)
        # ⭐ **Ask the CONNECTION what it is, not the path.** The first version read the path string, and the
        # Postgres test harness broke it immediately: the suite asks for `:memory:` while `db.connect` is
        # patched to hand back Postgres, so path and connection disagreed and the SQLite-only migrations ran
        # against Postgres. ⭐ *A derived fact should be read from the thing it describes* — the path is a
        # request, the connection is the answer.
        self.is_postgres = isinstance(self.conn, db.PgConnection)
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute(CREATE_TEAMS)
            self.conn.execute(CREATE_PLAYERS)
            self.conn.execute(CREATE_FIXTURES)
            self.conn.execute(CREATE_HISTORY_PAST)
            self.conn.execute(CREATE_HISTORY)
            self.conn.execute(CREATE_HEADLINE_EVENTS)
            self.conn.execute(CREATE_AVAILABILITY)
            self.conn.execute(CREATE_TRANSFER_FLOW)
            self.conn.execute(CREATE_DATA_STATUS)
            # ⭐ **The two migrations below repair OLD SQLITE FILES, and a Postgres database has no old files.**
            # `_migrate` adds columns that post-date a table, and `_rekey_history` rebuilds a primary key that
            # changed in ADR-129 — both exist because a cache on someone's laptop may have been created in
            # July. A Postgres database is created here, now, from the statements above, so there is no earlier
            # schema for either to converge from and running them would be answering a question nobody asked.
            #
            # ⚠️ **Stated so it is not mistaken for coverage: this is "not applicable", not "handled".** The day
            # a column is added *after* Postgres is carrying real data, that needs a real migration — and this
            # skip is where someone will look for one. See ADR-211's staging.
            self._migrate()                # ⭐ both backends since ADR-211 2d — see the note in `_migrate`
            if not self.is_postgres:
                self._rekey_history()      # after _migrate, so the copy sees every column (ADR-129)

    def _migrate(self) -> None:
        """Add any columns missing from an older database, table by table.

        CREATE TABLE IF NOT EXISTS won't alter a table that already exists, so we
        bring older caches up to the current schema by adding missing columns.
        Idempotent: only columns not already present are added.

        ⭐ **Now runs on Postgres too, and that gap was flagged before it bit** (ADR-211 2a said *"Postgres has
        no migration story — that stops being fine the first time a column is added while it holds real
        data"*, and 2d is the stage that adds two). The only part that was ever SQLite-specific was asking a
        table for its columns, which `db.columns` now answers on either backend.

        ⚠️ What this still cannot do is change a **primary key** — `_rekey_history` remains SQLite-only,
        because a Postgres database has never held the old key it repairs.
        """
        for table, cols in _MIGRATIONS.items():
            existing = db.columns(self.conn, table)
            for column, col_type in cols.items():
                if column not in existing:
                    # table/column/type are fixed constants, never user input.
                    self.conn.execute(
                        f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                    )

    def _rekey_history(self) -> None:
        """Rebuild `player_history` on `(element_code, fixture)` if it still carries the old gameweek key.

        SQLite cannot alter a primary key, so this is the standard four-step rebuild: create, copy, drop,
        rename. **Self-detecting and idempotent** — it inspects the current key and does nothing once the table
        is already right, so opening a database of any age converges on the current schema with no flag to set
        and no script to remember (ADR-129).

        Runs *after* `_migrate`, so the old table has already gained every column and the copy is complete.
        Rows with no `fixture` cannot be keyed and are not copied; FPL always sends one, so this is theoretical
        (verified: 0 such rows across the live database).
        """
        # ⚠️ **Compare as a SET.** `PRAGMA table_info` lists columns in *table* order and this filters to the
        # primary-key ones, so the result is ordered by position, not by key ordinal — `season` was appended to
        # the table, so it reads `[element_code, fixture, season]` however the key was declared. An equality
        # test against the declared order never matched, and the table was dropped and rebuilt on **every
        # open**: a silent, permanent migration loop that leaves the data correct and the cost invisible.
        pk = {row[1] for row in self.conn.execute("PRAGMA table_info(player_history)") if row[5]}
        if pk == {"element_code", "season", "fixture"}:
            return
        # ⚠️ **Backfill `season` BEFORE it joins the key (ADR-201).** Rows written before this migration carry
        # `''`, and folding a blank into the primary key would merge every season's GW1 into one row — the
        # exact loss the column exists to prevent, performed once, during the fix.
        self.conn.execute(
            "UPDATE player_history SET season = substr(kickoff_time, 1, 4) || '/' || "
            "substr(cast(cast(substr(kickoff_time, 1, 4) as integer) + 1 as text), 3, 2) "
            "WHERE (season IS NULL OR season = '') AND kickoff_time IS NOT NULL "
            "AND cast(substr(kickoff_time, 6, 2) as integer) >= 7")
        self.conn.execute(
            "UPDATE player_history SET season = "
            "cast(cast(substr(kickoff_time, 1, 4) as integer) - 1 as text) || '/' || "
            "substr(substr(kickoff_time, 1, 4), 3, 2) "
            "WHERE (season IS NULL OR season = '') AND kickoff_time IS NOT NULL "
            "AND cast(substr(kickoff_time, 6, 2) as integer) < 7")
        cols = [row[1] for row in self.conn.execute("PRAGMA table_info(player_history)")]
        names = ", ".join(cols)
        self.conn.execute(CREATE_HISTORY.replace("player_history", "player_history_rekeyed"))
        self.conn.execute(
            f"INSERT OR REPLACE INTO player_history_rekeyed ({names}) "
            f"SELECT {names} FROM player_history WHERE fixture IS NOT NULL"
        )
        self.conn.execute("DROP TABLE player_history")
        self.conn.execute("ALTER TABLE player_history_rekeyed RENAME TO player_history")


    def save_teams(self, teams: list[Team]) -> None:
        rows = [
            (t.id, t.name, t.short_name,
             t.strength_overall_home, t.strength_overall_away, t.code)
            for t in teams
        ]
        # `with self.conn` is a transaction: commit on success, roll back on error.
        with self.conn:
            self.conn.executemany(UPSERT_TEAM, rows)

    def save_players(self, players: list[Player]) -> None:
        rows = [
            (p.id, p.first_name, p.second_name, p.web_name,
             p.team_id, p.position, p.price, p.total_points,
             p.points_per_game, p.status, p.ep_next,
             p.xg, p.xa, p.xgi, p.xgc,
             p.goals_scored, p.assists, p.minutes,
             p.defcon, p.defcon_per90, p.cbi, p.tackles, p.recoveries,
             p.chance, p.news, p.scout_news_link, p.code, p.penalties_order,
             p.corners_order, p.freekicks_order, p.selected_by,
             p.transfers_in_event, p.transfers_out_event, p.cost_change_event, p.cost_change_start,
             p.form, p.ict_index, p.influence, p.creativity, p.threat, p.value_form)
            for p in players
        ]
        with self.conn:
            self.conn.executemany(UPSERT_PLAYER, rows)

    def save_availability(self, players, now: str) -> int:
        """Record each player's availability, **only when it changes** (ADR-203). Returns rows inserted.

        ⚠️ **A change log, not a poll log.** A row per player per refresh is ~480k rows a season and says
        nothing a change log does not; availability actually changes a few dozen times a week league-wide.

        ⭐ **But a change log cannot tell "unchanged" from "not observed"** — three silent weeks and three
        weeks of a stable squad produce identical tables, and that ambiguity would land squarely on the
        measurement this exists for. So each row is an **interval**: `observed_at` when the value first
        appeared, `last_seen_at` every time a refresh confirmed it still held. A reader can then ask both
        *"what did we know before this deadline"* and *"how stale was it"* — and the second question is the
        one that decides whether the answer is evidence.

        `now` is passed in rather than read here, so a caller (and a test) fixes the clock.
        """
        # ⚠️⚠️ **Three round trips per player is free locally and costs three minutes over a network.**
        # This ran a SELECT then a write for each of ~667 players — about 1,300 round trips. Against a local
        # SQLite file that is microseconds; against Supabase from a GitHub runner it was **3m31s of a 3m44s
        # job**, for a refresh that takes 3.6 seconds.
        # ⭐ *A cost that is invisible on the developer's machine is not a small cost — it is an unmeasured
        # one.* The audit timed every analytics call and never timed a write over a wire.
        #
        # Now: one query for every player's latest row, the comparison in Python (where it always was), and
        # two `executemany` calls. Same semantics, ~3 round trips instead of ~1,300.
        latest_by_code = {}
        for row in self.conn.execute(
                "SELECT a.element_code, a.observed_at, a.status, a.chance, a.news "
                "FROM player_availability a "
                "JOIN (SELECT element_code, MAX(observed_at) AS m FROM player_availability "
                "      GROUP BY element_code) b "
                "  ON a.element_code = b.element_code AND a.observed_at = b.m").fetchall():
            latest_by_code[row["element_code"]] = row

        touch, insert = [], []
        for p in players:
            # ⭐ **The failure path of a recorder must not take down the thing it observes.** `refresh` is the
            # app's lifeline — everything downstream degrades to stale data if it dies — and this is a
            # side-record, not the payload. A player FPL sends without a `code` cannot be keyed, so he is
            # skipped and the refresh completes.
            if getattr(p, "code", None) is None:
                continue
            latest = latest_by_code.get(p.code)
            if latest is not None and (latest["status"], latest["chance"], latest["news"]) == (
                    p.status, p.chance, p.news):
                touch.append((now, p.code, latest["observed_at"]))
            else:
                insert.append((p.code, now, now, p.status, p.chance, p.news))

        with self.conn:
            if touch:
                self.conn.executemany(
                    "UPDATE player_availability SET last_seen_at = ? "
                    "WHERE element_code = ? AND observed_at = ?", touch)
            if insert:
                # A second change inside one refresh timestamp would collide on the key; ON CONFLICT keeps
                # the write total rather than raising mid-refresh, and the later value is the current one.
                self.conn.executemany(
                    "INSERT INTO player_availability "
                    "(element_code, observed_at, last_seen_at, status, chance, news) VALUES (?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(element_code, observed_at) DO UPDATE SET "
                    "last_seen_at = excluded.last_seen_at, status = excluded.status, "
                    "chance = excluded.chance, news = excluded.news", insert)
        return len(insert)

    def availability_as_of(self, when: str) -> dict:
        """`element_code → (status, chance, news, observed_at, last_seen_at)` as known at `when` (ADR-203).

        The row whose observation window starts at or before `when` and is the latest such — i.e. what the app
        would have believed at that moment. Returns the staleness columns with the value **deliberately**: a
        status last confirmed three weeks ago is not the same evidence as one confirmed this morning, and a
        caller that cannot see the difference will treat them alike.
        """
        rows = self.conn.execute(
            "SELECT element_code, status, chance, news, observed_at, last_seen_at "
            "FROM player_availability WHERE observed_at <= ? ORDER BY element_code, observed_at", (when,))
        return {r["element_code"]: (r["status"], r["chance"], r["news"], r["observed_at"], r["last_seen_at"])
                for r in rows}

    def save_transfer_flow(self, players, event, observed_at: str, hours_to_deadline=None) -> int:
        """Record this week's transfer counters per player, keyed by the event they accumulate toward.

        ⭐ **ADR-203's lesson, in the one other place the app was letting data expire** (ADR-210).
        `transfers_in_event` / `transfers_out_event` / `selected_by` live on the single mutable `players` row,
        FPL resets them at every deadline, and there is no history endpoint — so every refresh destroyed the
        only copy of last week's answer. ADR-190 discovered this the hard way: its instruction to *"re-measure
        `EXODUS_PRESSURE` on ≥4 gameweeks"* had no data to run on, and produced a second single-week sample.

        ⚠️ **`event` is the gameweek the counter is climbing toward, not the one being played.** Pass the next
        deadline's gameweek. Getting this wrong does not raise — it silently files a reading under the wrong
        week, which is the one error this table cannot survive.

        `observed_at` and `hours_to_deadline` are passed in rather than read here, so a caller (and a test)
        fixes the clock — the same contract as `save_availability`.

        Returns the number of rows written. **Never raises on a malformed player**: this is a side-record and
        `refresh` is the app's lifeline, so a player FPL sends without a `code` is skipped (ADR-203).
        """
        if event is None:
            return 0                     # no next deadline (season over, or no fixtures) — nothing to key on
        # ⚠️ **One `executemany`, not 667 round trips.** Same reason as `save_availability` above: a per-row
        # write is free against a local file and was costing minutes against Supabase from a runner.
        rows = [(code, event, observed_at, hours_to_deadline,
                 getattr(p, "transfers_in_event", None), getattr(p, "transfers_out_event", None),
                 getattr(p, "selected_by", None))
                for p in players if (code := getattr(p, "code", None)) is not None]
        if not rows:
            return 0
        with self.conn:
            self.conn.executemany(
                "INSERT INTO player_transfer_flow "
                "(element_code, event, observed_at, hours_to_deadline, transfers_in, transfers_out, "
                " selected_by) VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(element_code, event) DO UPDATE SET "
                "observed_at = excluded.observed_at, hours_to_deadline = excluded.hours_to_deadline, "
                "transfers_in = excluded.transfers_in, transfers_out = excluded.transfers_out, "
                "selected_by = excluded.selected_by", rows)
        return len(rows)

    def transfer_flow(self, event=None) -> list:
        """Stored transfer-flow rows, for one `event` or every one (oldest first). Read-only (ADR-210).

        Returns the staleness columns with the values **deliberately**, exactly as `availability_as_of` does:
        a reading taken four days from the deadline and one taken four hours from it are not the same
        evidence, and a caller that cannot see which it has will average them as though they were.
        """
        if event is None:
            return self.conn.execute(
                "SELECT * FROM player_transfer_flow ORDER BY event, element_code").fetchall()
        return self.conn.execute(
            "SELECT * FROM player_transfer_flow WHERE event = ? ORDER BY element_code", (event,)).fetchall()

    def data_status(self):
        """The one `data_status` row, or None when the table is absent or empty (ADR-211 2b).

        ⚠️ **None is the normal state today**, not a failure: nothing writes this until the scheduled pipeline
        lands in 2c, and a database that predates the table must still render. Callers degrade to what they
        showed before.
        """
        try:
            return self.conn.execute("SELECT * FROM data_status WHERE id = 1").fetchone()
        except db.MISSING_TABLE:
            return None

    def set_data_status(self, *, refreshed_at=None, attempted_at=None, event=None, ok=None, note=None,
                        backfilled_at=None, backfilled_event=None) -> None:
        """Record the outcome of a refresh attempt — **including a failed one** (ADR-211 2b).

        ⭐ *Recording only successes would make a dead pipeline indistinguishable from a quiet one*, which is
        the exact ambiguity ADR-203 designed `last_seen_at` to remove for availability. `attempted_at` moves
        every run; `refreshed_at` moves only when the data was actually published.
        """
        with self.conn:
            self.conn.execute(
                "INSERT INTO data_status "
                "(id, refreshed_at, attempted_at, event, ok, note, backfilled_at, backfilled_event) "
                "VALUES (1, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "refreshed_at = COALESCE(excluded.refreshed_at, data_status.refreshed_at), "
                "attempted_at = COALESCE(excluded.attempted_at, data_status.attempted_at), "
                "event = COALESCE(excluded.event, data_status.event), "
                # ⚠️ `ok`/`note` are the CORE refresh's verdict and are overwritten deliberately; the backfill
                # never touches them, so a failed backfill cannot make a healthy refresh look broken.
                "ok = COALESCE(excluded.ok, data_status.ok), "
                # ⚠️ **`note` follows `ok`, and COALESCE would be wrong here.** A successful refresh reports
                # `note=None` *to clear* the previous failure's reason — under COALESCE that None would mean
                # "leave it", so the app would keep showing a stale failure after a healthy run. So: when this
                # write carries a verdict, it owns the note; when it does not (a backfill), it leaves both.
                "note = CASE WHEN excluded.ok IS NULL THEN data_status.note ELSE excluded.note END, "
                "backfilled_at = COALESCE(excluded.backfilled_at, data_status.backfilled_at), "
                "backfilled_event = COALESCE(excluded.backfilled_event, data_status.backfilled_event)",
                (refreshed_at, attempted_at, event, None if ok is None else int(ok), note,
                 backfilled_at, backfilled_event))

    def save_history_past(self, seasons: list[PlayerSeason]) -> None:
        """Upsert past-season history rows (ADR-027). Idempotent on (code, season)."""
        rows = [
            (s.element_code, s.season_name, s.total_points, s.minutes,
             s.goals_scored, s.assists, s.clean_sheets, s.goals_conceded,
             s.expected_goals, s.expected_assists, s.expected_goal_involvements,
             s.expected_goals_conceded, s.defensive_contribution, s.starts,
             s.start_cost, s.end_cost)
            for s in seasons
        ]
        with self.conn:
            self.conn.executemany(UPSERT_HISTORY_PAST, rows)

    def save_history(self, rows: list[PlayerGameweek]) -> None:
        """Upsert per-GW history rows (ADR-060). Idempotent on (element_code, round)."""
        # ADR-201 — stamp each row with the season its MATCH belongs to, from the kickoff. Not the clock: a
        # re-read of an old row must not relabel it with today's season. A row with no kickoff gets '' and is
        # still stored (it simply cannot be attributed), which keeps the write total-safe.
        from src.analytics.last_season import season_from_kickoff
        values = [
            (r.element_code, season_from_kickoff(r.kickoff_time) or "", r.round, r.minutes, r.total_points,
             r.was_home, r.opponent_team, r.fixture,
             r.kickoff_time, r.team_h_score, r.team_a_score, r.goals_scored, r.assists, r.clean_sheets,
             r.goals_conceded, r.saves, r.bonus, r.bps, r.xg, r.xa, r.xgi, r.xgc, r.ict_index,
             r.influence, r.creativity, r.threat, r.defcon, r.value)
            for r in rows
        ]
        with self.conn:
            self.conn.executemany(UPSERT_HISTORY, values)

    def get_history(self, element_code: int) -> list[sqlite3.Row]:
        """A player's per-GW rows this season (earliest round first), by stable element_code."""
        return self.conn.execute(
            "SELECT * FROM player_history WHERE element_code = ? ORDER BY round, kickoff_time",
            (element_code,),
        ).fetchall()

    def count_history(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM player_history").fetchone()[0]

    def get_gw_history_by_code(self) -> dict[int, list[sqlite3.Row]]:
        """All per-GW rows grouped by element_code, earliest round first within each player.

        One query for the whole season — the in-season form term (ADR-060) needs every player's
        gameweeks, keyed by the same `code` the xP baseline (ADR-028) uses. Empty preseason.

        ⚠️ **A row exists once its fixture is scheduled, not once it is played** (ADR-125). FPL creates the
        gameweek's rows up front with `minutes = 0`, so a player whose match kicks off tonight is, by minutes
        alone, indistinguishable from one who sat on the bench through a match that finished. On 2026-08-24 that
        was every Chelsea and Fulham player — 61 rows reading 0 minutes for a fixture yet to start.

        So **never infer "played" from a row's presence, or "didn't play" from its 0 minutes.** Anything counting
        appearances or averaging over gameweeks must first check that the row's `kickoff_time` has passed;
        otherwise it reads two whole clubs as never playing for the two days their gameweek is in flight.
        `form_rate` (ADR-060) is safe because it filters on `minutes > 0` — a not-yet-played row and a benched
        one both correctly carry no rate — but that safety is incidental, not a pattern to copy.
        """
        grouped: dict[int, list[sqlite3.Row]] = {}
        for row in self.conn.execute(
            "SELECT * FROM player_history ORDER BY element_code, round, kickoff_time"
        ):
            grouped.setdefault(row["element_code"], []).append(row)
        return grouped

    def get_player_codes(self) -> dict[int, int]:
        """A map of (per-season) id → stable element_code — used to key per-GW history (ADR-060)."""
        return {row["id"]: row["code"] for row in self.conn.execute("SELECT id, code FROM players")}

    def get_player_ids(self) -> list[int]:
        """Every stored player's (per-season) id — the backfill's work list."""
        return [row[0] for row in self.conn.execute("SELECT id FROM players ORDER BY id")]

    def get_history_past(self, element_code: int) -> list[sqlite3.Row]:
        """A player's past seasons (oldest first), by stable element_code."""
        return self.conn.execute(
            "SELECT * FROM player_history_past WHERE element_code = ? ORDER BY season_name",
            (element_code,),
        ).fetchall()

    def count_history_past(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM player_history_past").fetchone()[0]

    def get_history_by_code(self) -> dict[int, list[sqlite3.Row]]:
        """All past seasons grouped by element_code, oldest first within each player.

        One query for the whole backfill — the xP baseline (ADR-028) needs every
        player's seasons, so this avoids a per-player round-trip.
        """
        grouped: dict[int, list[sqlite3.Row]] = {}
        for row in self.conn.execute(
            "SELECT * FROM player_history_past ORDER BY element_code, season_name"
        ):
            grouped.setdefault(row["element_code"], []).append(row)
        return grouped

    def save_team_elo(self, elo_by_team: dict) -> None:
        """Update only the `elo` column for the given team ids.

        Kept separate from save_teams (which handles FPL data) so a refresh never
        overwrites Elo — and so a ClubElo failure simply leaves the last-known Elo.
        """
        rows = [(elo, team_id) for team_id, elo in elo_by_team.items()]
        with self.conn:
            self.conn.executemany("UPDATE teams SET elo = ? WHERE id = ?", rows)

    def save_fixtures(self, fixtures: list[Fixture]) -> None:
        rows = [
            (f.id, f.event, f.team_h, f.team_a, f.team_h_difficulty,
             f.team_a_difficulty, int(f.finished), f.kickoff_time)
            for f in fixtures
        ]
        with self.conn:
            self.conn.executemany(UPSERT_FIXTURE, rows)

    def get_players(
        self,
        name: str | None = None,
        position: str | None = None,
        team: str | None = None,
        max_price: float | None = None,
    ) -> list[sqlite3.Row]:
        """Return stored players (with their team short_name), top points first.

        Any provided argument narrows the result via a parameterised WHERE clause;
        with no arguments this returns every player (so `table` is unaffected).
        Filters combine with AND. Values always go through `?` placeholders — never
        string-formatted into the SQL — so this is safe from injection.

        The LEFT JOIN carries each player's team short_name, and keeps a player even
        if its team is missing.
        """
        clauses: list[str] = []
        params: list = []
        if name:
            # ⚠️ **`LIKE` is case-insensitive in SQLite and case-SENSITIVE in Postgres.** The old comment
            # here said "LIKE is case-insensitive for names" — true of the engine it was written against, and
            # stated as though it were a property of SQL. On Postgres the same line silently made player
            # search case-sensitive, so `search haaland` found nobody. ⭐ *Second time today a
            # case-sensitivity assumption crossed an engine boundary* (see docs/SUPABASE_RLS.md on
            # `beta_users`). `LOWER()` on both sides is exact on either backend.
            clauses.append("LOWER(p.web_name) LIKE LOWER(?)")
            params.append(f"%{name}%")
        if position:
            clauses.append("p.position = ?")
            params.append(position)
        if team:
            clauses.append("t.short_name = ?")
            params.append(team)
        if max_price is not None:
            clauses.append("p.price <= ?")
            params.append(max_price)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            "SELECT p.*, t.short_name AS team "
            "FROM players p "
            "LEFT JOIN teams t ON p.team_id = t.id "
            f"{where} "
            "ORDER BY p.total_points DESC"
        )
        return self.conn.execute(sql, params).fetchall()

    def get_upcoming_fixtures(self, team: str | None = None,
                              now: datetime | None = None) -> list[sqlite3.Row]:
        """Fixtures in gameweeks you can still act on, with both team short-names, ordered by gameweek.

        Answers "which fixtures are upcoming?" (a stored-column filter). With a
        `team` short-name, only that team's fixtures are returned; without one,
        all upcoming fixtures. The per-team aggregation and the home/away
        perspective live in the analytics layer, not here.

        "Upcoming" means **the gameweek's deadline has not passed** — not FPL's `finished`
        flag, and not the individual fixture's kickoff (ADR-123).

        Not `finished`, because FPL holds that flag back until a gameweek's bonus points are
        confirmed — it sets `finished_provisional` at full-time instead. So for the couple of
        days a gameweek is in flight, every played match still reads as unfinished, and a
        "next 3 gameweeks" projection quietly spends one of them on football already played.

        Not per-fixture kickoff either, because a gameweek is played over several days. Cutting
        fixture by fixture leaves a *stub* gameweek at the head of the horizon — GW1 with one
        match left, belonging to two teams — and every caller that reasonably assumes "the next
        gameweek" means "every team's next fixture" then quietly disagrees with itself: the
        player card's per-team next-3 outruns a global 3-gameweek horizon, and the captain
        double lands on a gameweek whose deadline has gone (a 0.0 double for anyone who has
        already played). The deadline is the honest line because it is the one that matters:
        once it passes you cannot transfer, captain or bench for that gameweek, so it is no
        longer a gameweek you are deciding about. Whole gameweeks in or out keeps every team on
        the same one.

        A gameweek's deadline is its earliest kickoff minus `DEADLINE_LEAD` — the same rule the
        countdown uses (`analytics.deadline`, ADR-086), shared from `fpl_rules` so the two
        cannot drift. `now` is injected (defaulting to the current UTC time) so the boundary is
        testable, the same convention `next_deadline` uses. Fixtures with no `event` or no
        `kickoff_time` are unscheduled, not played, so they stay upcoming.

        The cutoff is compared as a string, deliberately: kickoffs are stored exactly as the API
        sends them (`YYYY-MM-DDTHH:MM:SSZ`, all UTC), and for a fixed-width UTC format
        lexicographic order is chronological order — so SQLite can compare in-query with no date
        parsing. Rather than subtract the lead from each kickoff (which a string cannot do), we
        add it to `now`: a deadline has passed exactly when the earliest kickoff is at or before
        `now + DEADLINE_LEAD`.
        """
        cutoff = (now or datetime.now(timezone.utc)).astimezone(timezone.utc) + DEADLINE_LEAD
        clauses = ["f.finished = 0", """(f.event IS NULL OR f.event NOT IN (
                       SELECT event FROM fixtures
                       WHERE event IS NOT NULL AND kickoff_time IS NOT NULL
                       GROUP BY event HAVING MIN(kickoff_time) <= ?))"""]
        params: list = [cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")]
        if team:
            clauses.append("(th.short_name = ? OR ta.short_name = ?)")
            params.extend([team, team])

        sql = f"""
            SELECT f.event, f.team_h, f.team_a,
                   f.team_h_difficulty, f.team_a_difficulty, f.kickoff_time,
                   th.short_name AS home, ta.short_name AS away,
                   th.strength_overall_home AS home_team_strength,
                   ta.strength_overall_away AS away_team_strength
            FROM fixtures f
            JOIN teams th ON f.team_h = th.id
            JOIN teams ta ON f.team_a = ta.id
            WHERE {" AND ".join(clauses)}
            ORDER BY f.event, f.id
        """
        return self.conn.execute(sql, params).fetchall()

    def get_all_fixtures(self) -> list:
        """Every stored fixture, in kickoff order — **including ones already played** (ADR-211 2c).

        ⚠️ Deliberately not `get_upcoming_fixtures`, which filters to gameweeks you can still act on. The
        pipeline's cadence has to ask *"is a match in play right now?"*, and an in-play match is precisely the
        one "upcoming" has already excluded.
        """
        return self.conn.execute(
            "SELECT * FROM fixtures ORDER BY kickoff_time").fetchall()

    def get_fixtures_by_event(self, event: int) -> list[sqlite3.Row]:
        """All fixtures for one gameweek (finished or not), same shape as `get_upcoming_fixtures`.

        Used by the calibration backtest (ADR-101): to predict a *past* gameweek walk-forward, we need its
        fixtures — which `get_upcoming_fixtures` (finished = 0) excludes. A stored-column filter, no analytics."""
        sql = """
            SELECT f.event, f.team_h, f.team_a,
                   f.team_h_difficulty, f.team_a_difficulty, f.kickoff_time,
                   th.short_name AS home, ta.short_name AS away,
                   th.strength_overall_home AS home_team_strength,
                   ta.strength_overall_away AS away_team_strength
            FROM fixtures f
            JOIN teams th ON f.team_h = th.id
            JOIN teams ta ON f.team_a = ta.id
            WHERE f.event = ?
            ORDER BY f.id
        """
        return self.conn.execute(sql, [event]).fetchall()

    def count_players(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]

    def get_teams(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id, name, short_name, elo, code FROM teams ORDER BY short_name"
        ).fetchall()

    def count_teams(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]

    def count_fixtures(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM fixtures").fetchone()[0]

    def upsert_headline_events(self, events) -> int:
        """Store resolved news events (ADR-151). Idempotent on `(element_id, title)`; returns the row count.

        Called at **refresh** time, not per page view: extraction needs a language model, Streamlit Cloud has
        none, and the read-only snapshot (ADR-056) is how everything else gets there.
        """
        rows = [(e["element_id"], e["title"], e["kind"], e.get("source"), e.get("seen_at"))
                for e in events or []]
        if rows:
            self.conn.executemany(UPSERT_HEADLINE_EVENT, rows)
            self.conn.commit()
        return len(rows)

    def get_headline_events(self, element_id=None) -> list:
        """Stored news events, newest first — all of them, or one player's. `[]` when there are none.

        Empty is the normal state, not a failure: extraction only runs where a model is available, so a
        snapshot built without one simply carries no events and every surface degrades to what it said before.
        """
        sql = "SELECT element_id, title, kind, source, seen_at FROM headline_events"
        args = ()
        if element_id is not None:
            sql += " WHERE element_id = ?"
            args = (element_id,)
        sql += " ORDER BY seen_at DESC"
        try:
            return list(self.conn.execute(sql, args).fetchall())
        except db.MISSING_TABLE:              # a snapshot older than this table — degrade, never raise
            return []


    def headline_events_by_id(self) -> dict:
        """`{element_id: [event, …]}` — `get_headline_events` grouped, the shape every caller wanted.

        Added because four surfaces had each written the same three-line grouping loop, which is three chances
        for them to disagree about a fact they are all supposed to be reading from one table (ADR-155).
        """
        out = {}
        for row in self.get_headline_events():
            out.setdefault(row["element_id"], []).append(dict(row))
        return out
    def close(self) -> None:
        self.conn.close()
