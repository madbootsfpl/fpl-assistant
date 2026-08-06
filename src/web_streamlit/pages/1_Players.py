"""Players — a shared team/position/player filter (ADR-064) over a native sortable table (ADR-052),
paged through in full (ADR-063), with a filter-responsive top-15 bar.

Shows each player's official FPL photo (from the stored `code`); the browser fetches the image, so a
missing one just shows a broken-thumbnail icon (Sprint 055).
"""

import altair as alt
import streamlit as st

from src.analytics import crowd_flags, rank_players
from src.storage import Storage
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.filters import apply as apply_filter
from src.web_streamlit.filters import filter_controls
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
    # A shared filter (ADR-064): Team · Position · Player (AND) + max-price; then a separate sort.
    sel = filter_controls(rows, key="players", with_price=True)
    sort = st.selectbox("Sort by", ["points", "value", "team", "position"],
                        help="Order the table: total points · value (points per £m) · team · position.")

    filtered = apply_filter(rows, sel)
    if not filtered:
        st.info("No players match those filters — clear a filter or raise the price.")
    else:
        ranked = _sorted(filtered, sort)
        # A filter-responsive top-15 bar (ADR-064): the strongest of the filtered set by the sort metric
        # (points → Pts, else value → Val/£m), rank-ordered. Replaces the old price-vs-points scatter.
        by_value = sort == "value"
        field, bar_label = ("value", "Val/£m") if by_value else ("total_points", "Pts")
        top = sorted(ranked, key=lambda p: -((p.get(field) or 0)))[:15]
        bar_data = [{"Player": p["web_name"], "metric": round(p.get(field) or 0, 1)} for p in top]
        st.caption(f"Top {len(top)} of {len(filtered)} filtered players — by {bar_label}")
        st.altair_chart(
            alt.Chart(alt.Data(values=bar_data)).mark_bar().encode(
                x=alt.X("metric:Q", title=bar_label),
                y=alt.Y("Player:N", sort="-x", title=None),
                tooltip=[alt.Tooltip("Player:N"), alt.Tooltip("metric:Q", title=bar_label)],
            ).properties(height=28 * len(bar_data) or 28),
            width="stretch",
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
