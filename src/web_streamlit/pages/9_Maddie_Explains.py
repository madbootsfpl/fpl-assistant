"""Maddie Explains — the video hub (ADR-112; renamed from "Ask Maddie" in Sprint 160/US-390 — the "Ask" verb
implied a chatbot, but this is a passive video list; the mascot name Maddie stays).

A grounded, scripted **FAQ-by-video** fronted by the mascot (Maddie) — *not* a live chatbot (the deployed app is
data-only; a chat persona would fight the "shows its working" brand). The clips live **unlisted on YouTube** and
their rows in a **Supabase `maddie_videos` table** the owner curates from the dashboard (add / hide / reorder /
swap — no redeploy). This page just **reads** them (cached, best-effort) and embeds each with `st.video`.
"""

import streamlit as st

from src.web_streamlit import analytics, brand, maddie
from src.web_streamlit.access import require_access


@st.cache_data(ttl=600, show_spinner=False)     # ~10 min — dashboard edits show within the window, or on Reboot
def _cached_videos():
    return maddie.videos()


st.set_page_config(**brand.page_config("Maddie Explains"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Maddie Explains")

st.title("🎥 Maddie Explains")
st.markdown(brand.mark_html(badge_px=18, font_px=15), unsafe_allow_html=True)
st.caption("Short explainers from **Maddie**, your MADBOOTS guide — the analytics decide, the AI explains, you "
           "make the call. New clips land here as they're made.")
st.divider()

videos = _cached_videos()
for i, v in enumerate(videos):
    st.subheader(v["topic"])
    if v.get("blurb"):
        st.caption(v["blurb"])
    if v.get("youtube_url"):
        st.video(v["youtube_url"])
    else:
        st.info("🎬 Coming soon — this explainer is on its way.")
    if i < len(videos) - 1:
        st.divider()

st.divider()
st.caption("Prefer to read? The **🧭 Help** tab has a step-by-step written guide + a glossary.")
