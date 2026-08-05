"""The web edge (ADR-050).

A thin, **read-only, local-only** web layer over the analytics. The web is a *new edge*: its
handlers call the SAME `decision_xp` / `ask.answer` / optimiser the CLI does, and render the existing
text renderers inside a page shell. The analytics/CLI import **nothing** from here — one-way data flow
is preserved (a test asserts the core stays web-free). Run it with `python -m src.web`.
"""
