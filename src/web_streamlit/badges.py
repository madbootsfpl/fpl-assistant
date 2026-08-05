"""Team badge image URLs (Sprint 055) — built from the stored team `code`.

The FPL badge CDN; the browser fetches the image at render, so a team with no `code` (an unrefreshed DB)
just yields an empty string (no image, no crash). Lives in the edge — the core imports nothing here.
"""

_BADGE = "https://resources.premierleague.com/premierleague/badges/70/t{code}.png"


def badge_url(code) -> str:
    return _BADGE.format(code=code) if code else ""


def badge_url_by_short_name(teams) -> dict:
    """`{team short_name -> badge URL}` from stored team rows (each with `short_name` + `code`)."""
    return {t["short_name"]: badge_url(t["code"]) for t in teams}
