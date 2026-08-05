"""Image URLs for the Streamlit edge — team badges (Sprint 055) + player photos (Sprint 059).

Built from the stored `code`s; the FPL CDN serves the images, fetched by the browser at render. A missing
`code` (an unrefreshed DB) yields an empty string — no image, no crash. The one source of image URLs for
every tab, so Players/Fixtures and the squad tabs stay visually consistent. Lives in the edge — the core
imports nothing here.
"""

_BADGE = "https://resources.premierleague.com/premierleague/badges/70/t{code}.png"
_PHOTO = "https://resources.premierleague.com/premierleague/photos/players/110x140/p{code}.png"


def badge_url(code) -> str:
    return _BADGE.format(code=code) if code else ""


def badge_url_by_short_name(teams) -> dict:
    """`{team short_name -> badge URL}` from stored team rows (each with `short_name` + `code`)."""
    return {t["short_name"]: badge_url(t["code"]) for t in teams}


def photo_url(code) -> str:
    return _PHOTO.format(code=code) if code else ""


def _code(player):
    """A player row's `code` (sqlite Row or dict), or None if absent."""
    try:
        return player["code"]
    except (KeyError, IndexError):
        return None


def photo_url_by_id(players) -> dict:
    """`{player id -> photo URL}` from stored player rows — so any tab can show a player's photo by id."""
    return {p["id"]: photo_url(_code(p)) for p in players}
