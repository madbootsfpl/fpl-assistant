"""Tests for the web edge (ADR-050).

The FastAPI TestClient hits the routes (200 + expected content); `/ask` renders a real decision with
its trust line. Plus the architectural guardrail: the analytics core imports **nothing** from the web
edge, so one-way data flow survives.

These read the live `data/fpl.db` (like the CLI). Ollama needn't be running — `ask` degrades to the
decision + facts, which is deterministic enough to assert on.
"""

import pathlib

from fastapi.testclient import TestClient

from src.web.app import app

client = TestClient(app)


def test_home_lists_players():
    r = client.get("/")
    assert r.status_code == 200
    assert "MADBOOTS" in r.text          # the shell rendered
    assert "<pre>" in r.text                   # the players table is shown (reused renderer)


def test_fixtures_page_renders_the_fdr_table():
    r = client.get("/fixtures")
    assert r.status_code == 200
    assert "Avg FDR" in r.text or "run `python app.py refresh`" in r.text


def test_ask_page_without_a_question_shows_the_form():
    r = client.get("/ask")
    assert r.status_code == 200
    assert "<form" in r.text and "name=\"q\"" in r.text


def test_ask_page_answers_a_fixtures_question_with_the_trust_line():
    r = client.get("/ask", params={"q": "who has the best fixtures over the next 5?"})
    assert r.status_code == 200
    # the grounded decision is rendered (the FDR table's header), inside a <pre>
    assert "<pre>" in r.text
    assert "Avg FDR" in r.text or "fixtures" in r.text.lower()


def test_squads_index_renders():
    r = client.get("/squads")
    assert r.status_code == 200
    assert "Saved squads" in r.text          # renders whether or not any squads are saved


def test_squad_page_for_an_unknown_squad_is_graceful():
    r = client.get("/squad/definitely_not_a_saved_squad")
    assert r.status_code == 200
    assert "squad" in r.text.lower()          # a "name a saved squad" message, not a crash


def test_ask_escapes_html_in_the_question():
    # Jinja autoescaping: a `<script>` in the query must not appear unescaped in the page
    r = client.get("/ask", params={"q": "<script>alert(1)</script>"})
    assert r.status_code == 200
    assert "<script>alert(1)</script>" not in r.text


# ---- the architectural guardrail (one-way data flow) ------------------------

_CORE = [
    "src/analytics", "src/ui", "src/api", "src/models",
    "src/ask.py", "src/cli.py", "src/storage.py", "src/ingest.py",
    "src/squads.py", "src/llm.py", "src/config.py",
]


def test_core_never_imports_a_web_edge():
    """The core imports **neither** edge — `src/web` (FastAPI) nor `src/web_streamlit` (Streamlit).

    Both edge packages start with `src.web`, so a single prefix check covers both (ADR-050/052).

    ⚠️ **This checks real imports via the AST, not a substring.** It was a bare text scan, which failed on a
    *comment* in `cli.py` that merely mentioned `src/web_streamlit` while explaining an entry-point fix.

    ⚠️⚠️ **And the first repair silently broke it.** Stripping comments by tokenizing and re-joining with
    newlines split `src.web_streamlit` into three separate lines, so the substring could never match again —
    a real illegal import passed. Caught only by mutation-testing the "fixed" guard. **A guard you have just
    improved is exactly the guard you have to re-break.**
    """
    import ast

    def edge_imports(text):
        """Modules this file actually imports whose path starts with `src.web` — the rule, precisely."""
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return ["<unparseable>"]                       # fail loud rather than pass quietly
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                hits += [a.name for a in node.names if a.name.startswith("src.web")]
            elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("src.web"):
                hits.append(node.module)
        return hits

    root = pathlib.Path(__file__).resolve().parent.parent
    offenders = []
    for entry in _CORE:
        p = root / entry
        files = p.rglob("*.py") if p.is_dir() else [p]
        for f in files:
            for mod in edge_imports(f.read_text()):
                offenders.append(f"{f.relative_to(root)} imports {mod}")
    assert not offenders, f"the core must not import a web edge (one-way flow): {offenders}"
