"""Data models for FPL entities.

These are plain data holders (dataclasses) plus a `from_api` mapper that turns
one raw entry from the FPL bootstrap-static payload into an object. Keeping the
mapping next to the model means the API's quirks are handled in one obvious place.
"""

from src.models.fixture import Fixture
from src.models.player import Player
from src.models.player_season import PlayerSeason
from src.models.team import Team

__all__ = ["Fixture", "Player", "PlayerSeason", "Team"]
