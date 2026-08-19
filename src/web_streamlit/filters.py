"""A shared player filter for the Streamlit edge (ADR-064).

`filter_controls` renders Team · Position · Player multiselects (+ an optional Max-price slider) and
returns a selection dict; `apply` keeps the rows that match **every non-empty** dimension (AND — an empty
dimension means "any"). Used by both **Players** and **Player Stats**; each caller passes a unique `key`
so the two pages' widgets don't collide. Field reads tolerate `sqlite3.Row` (Players) and `dict` (stat
analytics) rows alike. Display-only — it never mutates the input.
"""

import math

import streamlit as st

_POSITIONS = ["GK", "DEF", "MID", "FWD"]


def _get(row, field):
    """Read `field` from a sqlite Row or a dict, returning None if absent."""
    try:
        return row[field]
    except (KeyError, IndexError):
        return None


def filter_controls(players, *, key: str, with_price: bool = False, my_squad_ids=None) -> dict:
    """Render the filter multiselects and return the selection (ADR-064).

    Options come from `players` (distinct teams, `web_name`s); positions are the fixed four. `with_price`
    adds a Max-price slider (Players only — stat rows have no price). `my_squad_ids` (a set of the active
    squad's player ids, when one is loaded) adds a **My squad only** checkbox that scopes to your team
    (News/Trending, US-407b). Keys are namespaced by `key`.
    """
    teams = sorted({_get(p, "team") for p in players if _get(p, "team")})
    # The cap is the highest player price rounded up to £0.5 (never below £15) — so the priciest player (e.g.
    # Haaland £15.5m) is never filtered out by a stale fixed max (US-345).
    price_hi = max(15.0, math.ceil(max((_get(p, "price") or 0.0) for p in players) * 2) / 2) if players else 15.0

    # US-424: the filter collapses into a single **🔽 Filter** popover (was an always-visible widget row) to save
    # real estate — most on mobile — across every caller (Players/Player Stats/News/Trending). The button label
    # carries an active-filter count (read from last run's state) so you know it's on while collapsed. The return
    # dict + `apply` are unchanged.
    ss = st.session_state
    active = (len(ss.get(f"{key}_team", [])) + len(ss.get(f"{key}_pos", []))
              + len(ss.get(f"{key}_player", []))
              + (1 if (my_squad_ids and ss.get(f"{key}_mysquad")) else 0)
              + (1 if (with_price and ss.get(f"{key}_price", price_hi) < price_hi) else 0))
    with st.popover(f"🔽 Filter · {active} on" if active else "🔽 Filter", use_container_width=False):
        my_squad = (st.checkbox("My squad only", key=f"{key}_mysquad",
                                help="Show only players in your active squad.") if my_squad_ids else False)
        team_sel = st.multiselect("Team", teams, key=f"{key}_team",
                                  help="Show only players from these teams (leave empty for all).")
        pos_sel = st.multiselect("Position", _POSITIONS, key=f"{key}_pos",
                                 help="Show only these positions — GK / DEF / MID / FWD (empty = all).")
        # Scope the Player options by the current Team ∧ Position selection (ADR-064; empty dims = all), so
        # the dropdown is a short, relevant list rather than ~570 names.
        team_set, pos_set = set(team_sel), set(pos_sel)
        names = sorted({_get(p, "web_name") for p in players
                        if (not team_set or _get(p, "team") in team_set)
                        and (not pos_set or _get(p, "position") in pos_set)
                        and _get(p, "web_name")})
        pkey = f"{key}_player"
        if pkey in ss:   # prune a now-out-of-scope pick so it can't linger or resurrect
            ss[pkey] = [n for n in ss[pkey] if n in names]
        player_sel = st.multiselect("Player", names, key=pkey,
                                    help="Pick specific players (scoped to the team/position above; empty = all).")
        max_price = (st.slider("Max price (£m)", 0.0, price_hi, price_hi, step=0.5, key=f"{key}_price",
                               help="Hide players priced above this.") if with_price else None)
    return {"teams": set(team_sel), "positions": set(pos_sel),
            "players": set(player_sel), "max_price": max_price,
            "my_squad": set(my_squad_ids) if (my_squad and my_squad_ids) else None}


def apply(rows, sel: dict) -> list:
    """Keep rows matching every non-empty dimension in `sel` (AND). Max-price applies only when set
    and the row carries a price."""
    teams, positions, players = sel["teams"], sel["positions"], sel["players"]
    max_price = sel.get("max_price")
    my_squad = sel.get("my_squad")

    def ok(r):
        if my_squad is not None and _get(r, "id") not in my_squad:
            return False
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
