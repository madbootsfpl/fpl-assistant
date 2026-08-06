"""A shared player filter for the Streamlit edge (ADR-064).

`filter_controls` renders Team · Position · Player multiselects (+ an optional Max-price slider) and
returns a selection dict; `apply` keeps the rows that match **every non-empty** dimension (AND — an empty
dimension means "any"). Used by both **Players** and **Player Stats**; each caller passes a unique `key`
so the two pages' widgets don't collide. Field reads tolerate `sqlite3.Row` (Players) and `dict` (stat
analytics) rows alike. Display-only — it never mutates the input.
"""

import streamlit as st

_POSITIONS = ["GK", "DEF", "MID", "FWD"]


def _get(row, field):
    """Read `field` from a sqlite Row or a dict, returning None if absent."""
    try:
        return row[field]
    except (KeyError, IndexError):
        return None


def filter_controls(players, *, key: str, with_price: bool = False) -> dict:
    """Render the filter multiselects and return the selection (ADR-064).

    Options come from `players` (distinct teams, `web_name`s); positions are the fixed four. `with_price`
    adds a Max-price slider (Players only — stat rows have no price). Keys are namespaced by `key`.
    """
    teams = sorted({_get(p, "team") for p in players if _get(p, "team")})
    names = sorted({_get(p, "web_name") for p in players if _get(p, "web_name")})
    cols = st.columns(4 if with_price else 3)
    team_sel = cols[0].multiselect("Team", teams, key=f"{key}_team")
    pos_sel = cols[1].multiselect("Position", _POSITIONS, key=f"{key}_pos")
    player_sel = cols[2].multiselect("Player", names, key=f"{key}_player")
    max_price = (cols[3].slider("Max price (£m)", 3.5, 15.0, 15.0, step=0.5, key=f"{key}_price")
                 if with_price else None)
    return {"teams": set(team_sel), "positions": set(pos_sel),
            "players": set(player_sel), "max_price": max_price}


def apply(rows, sel: dict) -> list:
    """Keep rows matching every non-empty dimension in `sel` (AND). Max-price applies only when set
    and the row carries a price."""
    teams, positions, players = sel["teams"], sel["positions"], sel["players"]
    max_price = sel.get("max_price")

    def ok(r):
        if teams and _get(r, "team") not in teams:
            return False
        if positions and _get(r, "position") not in positions:
            return False
        if players and _get(r, "web_name") not in players:
            return False
        if max_price is not None:
            price = _get(r, "price")
            if price is not None and price > max_price:
                return False
        return True

    return [r for r in rows if ok(r)]
