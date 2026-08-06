"""Players — live filters (position, max price) over a native sortable/searchable table (ADR-052).

Shows each player's official FPL photo (from the stored `code`); the browser fetches the image, so a
missing one just shows a broken-thumbnail icon (Sprint 055).
"""

import streamlit as st

from src.analytics import crowd_flags, rank_players
from src.storage import Storage
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.paginate import paginate
from src.web_streamlit.status import render_data_status

_POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}


def _sorted(players, sort_by):
    """Order players by the chosen key. Always go through `rank_players` first (it returns dicts with a
    computed `value`); then for team/position re-sort those dicts (points desc within each group)."""
    ranked = rank_players(players, sort_by="points" if sort_by in ("team", "position") else sort_by)
    if sort_by in ("points", "value"):
        return ranked
    key = (lambda p: (str(p["team"] or ""), -(p["total_points"] or 0))) if sort_by == "team" else \
          (lambda p: (_POS_ORDER.get(p["position"], 9), -(p["total_points"] or 0)))
    return sorted(ranked, key=key)


st.set_page_config(page_title="Players · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
st.title("Players")

store = Storage()
try:
    rows = store.get_players()
    badges = badge_url_by_short_name(store.get_teams())     # {short_name: badge URL}
    photos = photo_url_by_id(rows)                          # {player id: photo URL}
finally:
    store.close()

if not rows:
    st.info("No data yet — run `python app.py refresh` first.")
else:
    col1, col2, col3 = st.columns(3)
    positions = col1.multiselect("Position", ["GK", "DEF", "MID", "FWD"],
                                 default=["GK", "DEF", "MID", "FWD"])
    max_price = col2.slider("Max price (£m)", 3.5, 15.0, 15.0, step=0.5)
    sort = col3.selectbox("Sort by", ["points", "value", "team", "position"])

    filtered = [p for p in rows if p["position"] in positions and p["price"] <= max_price]
    if not filtered:
        st.info("No players match those filters — widen the position or price.")
    else:
        ranked = _sorted(filtered, sort)
        # The value landscape: price vs points across all matching players (top-left = cheap + high).
        st.scatter_chart(
            [{"£m": p["price"], "Pts": p["total_points"], "Pos": p["position"]} for p in filtered],
            x="£m", y="Pts", color="Pos",
        )
        # Page through ALL matches (ADR-063) — no 50-cap; the table headers also click-sort.
        page = paginate(ranked, key="players", per_page=50)
        # The crowd lens (ADR-057): Own% · Form · ICT + short trend flags (template / differential /
        # 🔥 in / ❄️ out / 💰 price / 📈 form). Display-only — xP is untouched. Momentum flags are 0
        # preseason and light up at GW1.
        st.dataframe(
            [{"photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
              "Player": p["web_name"], "Team": p["team"], "Pos": p["position"],
              "£m": p["price"], "Pts": p["total_points"], "Val/£m": p.get("value"),
              "Own%": p["selected_by"], "Form": p.get("form"), "ICT": p.get("ict_index"),
              "Trends": " ".join(crowd_flags(p))} for p in page],
            width="stretch", hide_index=True,
            column_config={"photo": st.column_config.ImageColumn("", width="small"),
                           "badge": st.column_config.ImageColumn("", width="small")},
        )
