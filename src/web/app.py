"""The FastAPI app — a thin, read-only edge over the analytics (ADR-050).

Sync handlers only (no async — we don't need it). Each route calls the same engine the CLI does and
renders the existing text renderers inside a `<pre>` block (slice-1: zero new rendering logic). The
flagship is `/ask` — the grounded NL layer, in a browser, trust line and all.

Read-only, local-only; no auth, no writes. Run: `python -m src.web` (serves 127.0.0.1:8000).
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src import ask
from src.analytics import rank_players, team_fdr
from src.squads import SquadStore
from src.storage import Storage
from src.ui.ask import render_ask
from src.ui.fdr import render_fdr_table
from src.ui.table import render_player_table

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
_HOME_LIMIT = 30   # how many players the home view lists

app = FastAPI(title="FPL Assistant", docs_url=None, redoc_url=None)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """A players view — the same table the CLI's `table` command shows."""
    store = Storage()
    try:
        rows = store.get_players()
    finally:
        store.close()
    body = (render_player_table(rank_players(rows, sort_by="points"), limit=_HOME_LIMIT)
            if rows else "No data yet — run `python app.py refresh` first.")
    return _TEMPLATES.TemplateResponse(
        request, "page.html", {"title": "Players", "body": body},
    )


@app.get("/ask", response_class=HTMLResponse)
def ask_page(request: Request, q: str | None = None):
    """The flagship: a question box → `ask.answer(q)` → the decision + the ✓/⚠ trust line.

    Degrades exactly like the CLI — without Ollama, the answer is the decision + facts (no prose).
    """
    answer = render_ask(ask.answer(q)) if q else None
    return _TEMPLATES.TemplateResponse(
        request, "ask.html", {"title": "Ask", "q": q or "", "answer": answer},
    )


@app.get("/fixtures", response_class=HTMLResponse)
def fixtures_page(request: Request):
    """The league fixture-difficulty ranking (easiest over the next 5) — the same FDR table."""
    store = Storage()
    try:
        upcoming = store.get_upcoming_fixtures()
    finally:
        store.close()
    body = (render_fdr_table(team_fdr(upcoming, next_n=5, source="fpl"), next_n=5, source="fpl")
            if upcoming else "No fixtures yet — run `python app.py refresh` first.")
    return _TEMPLATES.TemplateResponse(
        request, "page.html", {"title": "Fixtures", "body": body},
    )


@app.get("/squads", response_class=HTMLResponse)
def squads_index(request: Request):
    """The saved squads — each links to its analysis."""
    return _TEMPLATES.TemplateResponse(
        request, "squads.html", {"title": "Squads", "squads": SquadStore().names()},
    )


@app.get("/squad/{name}", response_class=HTMLResponse)
def squad_page(request: Request, name: str):
    """A saved squad's health — the same `analyse` decision, via `ask` (so it reads identically)."""
    answer = render_ask(ask.answer(f"analyse {name}"))
    return _TEMPLATES.TemplateResponse(
        request, "page.html", {"title": f"Squad · {name}", "body": answer},
    )
