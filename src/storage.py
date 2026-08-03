"""Local SQLite storage for FPL data.

This is the project's storage layer. It knows about the database but nothing
about HTTP or how data is displayed (Architecture §3, §6). Rows are upserted on
the stable FPL id, so re-running the fetch refreshes existing rows instead of
creating duplicates.
"""

import sqlite3
from pathlib import Path

from src import config
from src.models import Fixture, Player, Team

CREATE_TEAMS = """
CREATE TABLE IF NOT EXISTS teams (
    id                    INTEGER PRIMARY KEY,
    name                  TEXT NOT NULL,
    short_name            TEXT NOT NULL,
    strength_overall_home INTEGER,
    strength_overall_away INTEGER,
    elo                   REAL
)
"""

# Columns added to tables after they first shipped. On an existing database,
# CREATE TABLE IF NOT EXISTS leaves old tables untouched, so we add any missing
# columns with a light migration (see _migrate). Keyed by table name.
_MIGRATIONS = {
    "teams": {
        "strength_overall_home": "INTEGER",
        "strength_overall_away": "INTEGER",
        "elo": "REAL",
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
    news            TEXT
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
INSERT INTO teams (id, name, short_name, strength_overall_home, strength_overall_away)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name                  = excluded.name,
    short_name            = excluded.short_name,
    strength_overall_home = excluded.strength_overall_home,
    strength_overall_away = excluded.strength_overall_away
"""

UPSERT_PLAYER = """
INSERT INTO players
    (id, first_name, second_name, web_name, team_id, position, price, total_points,
     points_per_game, status, ep_next, xg, xa, xgi, xgc,
     goals_scored, assists, minutes,
     defcon, defcon_per90, cbi, tackles, recoveries,
     chance, news)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    news            = excluded.news
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


class Storage:
    """A thin wrapper around the SQLite database."""

    def __init__(self, db_path: str = config.DB_PATH):
        # Make sure the parent folder exists (e.g. data/) before connecting.
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        # SQLite has foreign keys OFF by default, per connection — turn them on so
        # a player/fixture can't reference a team that doesn't exist.
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Return rows that can be indexed by column name, e.g. row["web_name"].
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute(CREATE_TEAMS)
            self.conn.execute(CREATE_PLAYERS)
            self.conn.execute(CREATE_FIXTURES)
            self._migrate()

    def _migrate(self) -> None:
        """Add any columns missing from an older database, table by table.

        CREATE TABLE IF NOT EXISTS won't alter a table that already exists, so we
        bring older caches up to the current schema by adding missing columns.
        Idempotent: only columns not already present are added.
        """
        for table, columns in _MIGRATIONS.items():
            existing = {row[1] for row in self.conn.execute(f"PRAGMA table_info({table})")}
            for column, col_type in columns.items():
                if column not in existing:
                    # table/column/type are fixed constants, never user input.
                    self.conn.execute(
                        f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                    )

    def save_teams(self, teams: list[Team]) -> None:
        rows = [
            (t.id, t.name, t.short_name,
             t.strength_overall_home, t.strength_overall_away)
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
             p.chance, p.news)
            for p in players
        ]
        with self.conn:
            self.conn.executemany(UPSERT_PLAYER, rows)

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
            clauses.append("p.web_name LIKE ?")  # LIKE is case-insensitive for names
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

    def get_upcoming_fixtures(self, team: str | None = None) -> list[sqlite3.Row]:
        """Unfinished fixtures with both team short-names, ordered by gameweek.

        Answers "which fixtures are upcoming?" (a stored-column filter). With a
        `team` short-name, only that team's fixtures are returned; without one,
        all upcoming fixtures. The per-team aggregation and the home/away
        perspective live in the analytics layer, not here.
        """
        clauses = ["f.finished = 0"]
        params: list = []
        if team:
            clauses.append("(th.short_name = ? OR ta.short_name = ?)")
            params.extend([team, team])

        sql = f"""
            SELECT f.event, f.team_h, f.team_a,
                   f.team_h_difficulty, f.team_a_difficulty,
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

    def count_players(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]

    def get_teams(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id, name, short_name, elo FROM teams ORDER BY short_name"
        ).fetchall()

    def count_teams(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]

    def count_fixtures(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM fixtures").fetchone()[0]

    def close(self) -> None:
        self.conn.close()
