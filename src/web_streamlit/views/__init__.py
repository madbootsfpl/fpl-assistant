"""Reusable page-view renderers for the consolidated Streamlit pages (ADR-069).

Each `render_*` draws one view's body given already-loaded data + shared helpers, so a consolidated page
(Players, Squads) can load once and render only the view its segmented control selects.
"""
