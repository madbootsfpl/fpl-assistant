"""Club kit image URLs — the shirt the pitch draws.

⭐⭐ **Here rather than in `web_streamlit/badges.py`, because the API needs it and that module imports
Streamlit.** Pulling the web framework into the API process to build a URL string would be absurd; copying
the template into the service would be a second definition of where a shirt comes from — ADR-181's rule.
One home, both surfaces import it, and `badges` re-exports so every existing caller is untouched.

⚠️⚠️ **Moved verbatim, not retyped, and the difference was not academic.** The first attempt at this file
reproduced the template from memory as `shirt_{code}{gk}.png` and dropped the **`-66`** suffix — a URL that
is wrong and still looks entirely plausible. ⭐ *A constant copied is a constant that can differ; it was
caught only because the two were compared side by side.*

⚠️ **The kit, deliberately, and never the mugshot** (ADR-084 revision, 2026-08-22). FPL's photo CDN lags a
transfer by weeks while the kit graphic updates instantly, so a just-transferred player would otherwise sit
on the pitch in his old club's shirt — visibly wrong on the one surface a manager checks most.
"""

_SHIRT = "https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_{code}{gk}-66.png"
_BADGE = "https://resources.premierleague.com/premierleague/badges/70/t{code}.png"
_PHOTO = "https://resources.premierleague.com/premierleague/photos/players/110x140/p{code}.png"


def _get(player, key):
    """A field from a dict **or** a `sqlite3.Row` — the two shapes player rows arrive in."""
    try:
        return player[key]
    except (KeyError, IndexError):
        return None


def shirt_url(team_code, position=None) -> str:
    """The club-shirt kit image by *team* code — the goalkeeper (`_1`) variant when `position == 'GK'`.
    Empty when the team code is missing (no image, no crash)."""
    if not team_code:
        return ""
    return _SHIRT.format(code=team_code, gk="_1" if position == "GK" else "")


def shirt_url_by_id(players, teams=None) -> dict:
    """`{player id -> club-shirt kit URL}` by each player's **current** team.

    ⚠️ Empty-safe: an empty string when the team code is missing, so a surface gets a placeholder rather
    than a crash.
    """
    team_code = {t["short_name"]: t["code"] for t in teams} if teams else {}
    return {p["id"]: shirt_url(team_code.get(_get(p, "team")), _get(p, "position")) for p in players}


def badge_url(code) -> str:
    """A club badge by team code — ⭐ moved here with the rest (ADR-255) so the API can build one."""
    return _BADGE.format(code=code) if code else ""


def photo_url(code) -> str:
    """A player's mugshot by his **element code**, not his id.

    ⭐⭐ `code` is stable across seasons; `id` restarts every August (ADR-201). A photo URL built from the
    id would point at whoever inherited the number.

    ⚠️⚠️ **This is for a named card, never for the pitch.** ADR-084 chose the club kit there on purpose:
    FPL's photo CDN lags a transfer by weeks while the kit graphic updates instantly, so a just-transferred
    player would sit on the pitch wearing his old club's face. ⭐ *On a card his name is beside him and the
    staleness is a curiosity; on the pitch it is the app being visibly wrong about your team.*
    """
    return _PHOTO.format(code=code) if code else ""
