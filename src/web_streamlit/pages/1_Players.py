"""Players — live filters (position, max price) over a native sortable/searchable table (ADR-052).

Shows each player's official FPL photo (from the stored `code`); the browser fetches the image, so a
missing one just shows a broken-thumbnail icon (Sprint 055).
"""

import streamlit as st

from src.analytics import rank_players
from src.storage import Storage
from src.web_streamlit.badges import badge_url_by_short_name

_PHOTO = "https://resources.premierleague.com/premierleague/photos/players/110x140/p{code}.png"

st.set_page_config(page_title="Players · FPL Assistant", page_icon="⚽", layout="wide")
st.title("Players")


def _photo_url(player) -> str:
    code = player["code"] if "code" in player.keys() else None
    return _PHOTO.format(code=code) if code else ""

store = Storage()
try:
    rows = store.get_players()
    badges = badge_url_by_short_name(store.get_teams())     # {short_name: badge URL}
finally:
    store.close()

if not rows:
    st.info("No data yet — run `python app.py refresh` first.")
else:
    col1, col2, col3, col4 = st.columns(4)
    positions = col1.multiselect("Position", ["GK", "DEF", "MID", "FWD"],
                                 default=["GK", "DEF", "MID", "FWD"])
    max_price = col2.slider("Max price (£m)", 3.5, 15.0, 15.0, step=0.5)
    sort = col3.selectbox("Sort by", ["points", "value"])
    limit = col4.slider("How many", 5, 50, 20)

    filtered = [p for p in rows if p["position"] in positions and p["price"] <= max_price]
    if not filtered:
        st.info("No players match those filters — widen the position or price.")
    else:
        ranked = rank_players(filtered, sort_by=sort)[:limit]
        st.caption(f"{len(filtered)} players match · showing {len(ranked)}")
        # The value landscape: price vs points across all matching players (top-left = cheap + high).
        st.scatter_chart(
            [{"£m": p["price"], "Pts": p["total_points"], "Pos": p["position"]} for p in filtered],
            x="£m", y="Pts", color="Pos",
        )
        st.dataframe(
            [{"photo": _photo_url(p), "badge": badges.get(p["team"], ""),
              "Player": p["web_name"], "Team": p["team"], "Pos": p["position"],
              "£m": p["price"], "Pts": p["total_points"], "Val/£m": p.get("value"),
              "Own%": p["selected_by"]} for p in ranked],
            width="stretch", hide_index=True,
            column_config={"photo": st.column_config.ImageColumn("", width="small"),
                           "badge": st.column_config.ImageColumn("", width="small")},
        )
