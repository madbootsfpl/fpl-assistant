"""Image URLs for the Streamlit edge — team badges (Sprint 055) + player photos (Sprint 059).

Built from the stored `code`s; the FPL CDN serves the images, fetched by the browser at render. A missing
`code` (an unrefreshed DB) yields an empty string — no image, no crash. The one source of image URLs for
every tab, so Players/Fixtures and the squad tabs stay visually consistent. Lives in the edge — the core
imports nothing here.

Photo fallback (Sprint 098, US-255): ~a quarter of players have a valid `code` but **no photo file** on the
CDN (it 403s — new/lower-profile players), so the card shows a blank. `photo_url_by_id` resolves each id to
the **photo when it exists, else the club shirt** (GK variant for keepers). Existence is a **cached** sweep
(`_missing_photo_codes`, ~daily TTL) that **degrades to "all present"** on any error — never worse than
before. The sweep is the only network here; it's patched out in tests (see the root `conftest.py`).
"""

from concurrent.futures import ThreadPoolExecutor

import requests
import streamlit as st

_BADGE = "https://resources.premierleague.com/premierleague/badges/70/t{code}.png"
_PHOTO = "https://resources.premierleague.com/premierleague/photos/players/110x140/p{code}.png"
# FPL club-shirt kit images — the outfield shirt, and the `_1` goalkeeper variant. Keyed by *team* code.
_SHIRT = "https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_{code}{gk}-66.png"

_SWEEP_TIMEOUT = 2.5        # seconds per photo HEAD — kept short so a slow CDN degrades fast
_SWEEP_WORKERS = 32


def badge_url(code) -> str:
    return _BADGE.format(code=code) if code else ""


def badge_url_by_short_name(teams) -> dict:
    """`{team short_name -> badge URL}` from stored team rows (each with `short_name` + `code`)."""
    return {t["short_name"]: badge_url(t["code"]) for t in teams}


def photo_url(code) -> str:
    return _PHOTO.format(code=code) if code else ""


def shirt_url(team_code, position=None) -> str:
    """The club-shirt kit image by *team* code — the goalkeeper (`_1`) variant when `position == 'GK'`.
    Empty when the team code is missing (no image, no crash)."""
    if not team_code:
        return ""
    return _SHIRT.format(code=team_code, gk="_1" if position == "GK" else "")


def _photo_exists(code) -> bool:
    """True if the CDN serves this player's photo (HEAD 200). Any error → True (assume present — never
    hide a photo we can't check)."""
    try:
        return requests.head(photo_url(code), timeout=_SWEEP_TIMEOUT).status_code == 200
    except requests.RequestException:
        return True


@st.cache_data(ttl=86_400, show_spinner=False)
def _missing_photo_codes(codes: tuple) -> frozenset:
    """The subset of `codes` whose photo the CDN doesn't serve — a cached daily sweep. Degrades to an
    **empty set** (every photo kept) on any failure, so the fallback is never worse than showing photos."""
    try:
        with ThreadPoolExecutor(max_workers=_SWEEP_WORKERS) as pool:
            present = pool.map(_photo_exists, codes)
            return frozenset(c for c, ok in zip(codes, present) if not ok)
    except Exception:
        return frozenset()


def _code(player):
    """A player row's `code` (sqlite Row or dict), or None if absent."""
    try:
        return player["code"]
    except (KeyError, IndexError):
        return None


def _get(player, key):
    try:
        return player[key]
    except (KeyError, IndexError):
        return None


def photo_url_by_id(players, teams=None) -> dict:
    """`{player id -> image URL}` — the player **photo** when the CDN has it, else the **club shirt**
    (US-255). `teams` (rows with `short_name` + `code`) enables the shirt fallback; without it, the photo
    URL is returned as before (no fallback). Empty-safe; the existence check is cached + degrades."""
    team_code = {t["short_name"]: t["code"] for t in teams} if teams else {}
    codes = tuple(sorted({c for p in players if (c := _code(p)) is not None}))
    missing = _missing_photo_codes(codes) if (codes and team_code) else frozenset()

    out = {}
    for p in players:
        code = _code(p)
        if code and code not in missing:
            out[p["id"]] = photo_url(code)
        else:                                          # no code, or the photo 403s → the club shirt
            out[p["id"]] = shirt_url(team_code.get(_get(p, "team")), _get(p, "position"))
    return out
