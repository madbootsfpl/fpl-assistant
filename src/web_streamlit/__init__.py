"""The Streamlit web edge (ADR-051/052) — the UI the project grows.

A thin, **read-only, local** Streamlit app over the analytics. Like the (frozen) FastAPI edge, its
pages call the SAME engine the CLI does (`ask.answer` / analytics) and render the existing renderers or
native widgets — the analytics/CLI import **nothing** from here (one-way flow; a test asserts it).

Multipage: `Home.py` + `pages/` — 7 tabs (ADR-069): Players (pool + stat views) · Fixtures · Squads
(Build · My Squad · Health · Transfer · Captain) · Ask · News · Trending · Help. The two consolidated
pages (Players, Squads) switch views with a lazy `st.segmented_control`; the view bodies live in
`web_streamlit/views/`.
Run:  python -m src.web_streamlit   (→ http://localhost:8501)
"""
