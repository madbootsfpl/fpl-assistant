"""User-state store for saved squads (ADR-024).

This is *not* the reference cache. `Storage` (fpl.db) holds FPL data that `refresh`
overwrites; this holds **the user's own picks** — player ids + which are bench — in a small
JSON file that must survive a refresh (and is gitignored). We store the picks only; prices
and availability are derived fresh from current data on load.
"""

import datetime
import json
from pathlib import Path

from src import config


class SquadStore:
    """A thin JSON-backed store of named squads. The path is injectable for tests."""

    def __init__(self, path: str = config.SQUADS_PATH):
        self.path = Path(path)

    def _read(self) -> dict:
        """All saved squads, or {} if the file is missing or unreadable."""
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write(self, data: dict) -> None:
        """Persist atomically: write a temp file, then replace — a crash can't corrupt it."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self.path)

    def save(self, name: str, player_ids, player_names=(), bench_ids=(), cost=None) -> None:
        """Save (or overwrite) a squad by name.

        Stores the picks (ids + names) + bench + cost + date. Names are kept so a player
        who later *leaves the game* can still be shown by name on load (they won't be in the
        current data to look up). Prices/availability are NOT stored — derived fresh on load.
        """
        data = self._read()
        data[name] = {
            "player_ids": list(player_ids),
            "player_names": list(player_names),
            "bench_ids": list(bench_ids),
            "cost": cost,
            "saved_at": datetime.date.today().isoformat(),
        }
        self._write(data)

    def load(self, name: str) -> dict | None:
        """The saved record for `name`, or None if there isn't one."""
        return self._read().get(name)

    def names(self) -> list:
        """The names of all saved squads, sorted."""
        return sorted(self._read())
