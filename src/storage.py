"""Local SQLite storage for FPL data.

This is the project's storage layer. It knows about the database but nothing
about HTTP or how data is displayed (Architecture §3, §6). Rows are upserted on
the stable FPL id, so re-running the fetch refreshes existing rows instead of
creating duplicates.
"""

import sqlite3
from pathlib import Path

from src import config
from src.models import Player, Team

CREATE_TEAMS = """
CREATE TABLE IF NOT EXISTS teams (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    short_name TEXT NOT NULL
)
"""

CREATE_PLAYERS = """
CREATE TABLE IF NOT EXISTS players (
    id           INTEGER PRIMARY KEY,
    first_name   TEXT,
    second_name  TEXT,
    web_name     TEXT,
    team_id      INTEGER REFERENCES teams(id),
    position     TEXT,
    price        REAL,
    total_points INTEGER
)
"""

# Upsert: insert a new row, or refresh the existing one if the id already exists.
UPSERT_TEAM = """
INSERT INTO teams (id, name, short_name)
VALUES (?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name       = excluded.name,
    short_name = excluded.short_name
"""

UPSERT_PLAYER = """
INSERT INTO players
    (id, first_name, second_name, web_name, team_id, position, price, total_points)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    first_name   = excluded.first_name,
    second_name  = excluded.second_name,
    web_name     = excluded.web_name,
    team_id      = excluded.team_id,
    position     = excluded.position,
    price        = excluded.price,
    total_points = excluded.total_points
"""


class Storage:
    """A thin wrapper around the SQLite database."""

    def __init__(self, db_path: str = config.DB_PATH):
        # Make sure the parent folder exists (e.g. data/) before connecting.
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        # Return rows that can be indexed by column name, e.g. row["web_name"].
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute(CREATE_TEAMS)
            self.conn.execute(CREATE_PLAYERS)

    def save_teams(self, teams: list[Team]) -> None:
        rows = [(t.id, t.name, t.short_name) for t in teams]
        # `with self.conn` is a transaction: commit on success, roll back on error.
        with self.conn:
            self.conn.executemany(UPSERT_TEAM, rows)

    def save_players(self, players: list[Player]) -> None:
        rows = [
            (p.id, p.first_name, p.second_name, p.web_name,
             p.team_id, p.position, p.price, p.total_points)
            for p in players
        ]
        with self.conn:
            self.conn.executemany(UPSERT_PLAYER, rows)

    def get_players(self) -> list[sqlite3.Row]:
        # LEFT JOIN so each row carries the team's short_name; LEFT (not inner)
        # means a player with an unknown team still appears rather than vanishing.
        return self.conn.execute(
            """
            SELECT p.*, t.short_name AS team
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.id
            ORDER BY p.total_points DESC
            """
        ).fetchall()

    def count_players(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]

    def count_teams(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]

    def close(self) -> None:
        self.conn.close()
