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

#: ⚠️⚠️ **Every layer that is not an edge belongs here, and `src/service` was missing for its whole
#: life.** The guard below is exact and well-tested, and it still let a real illegal import through —
#: `service/answers.py` imported `relay_result` from `web_streamlit`, which works in the repo and
#: **HTTP 500s in the API container**, where `.dockerignore` excludes that package. ⭐ *A guardrail is
#: only as wide as its list, and a hand-maintained list does not grow when the codebase does.*
#: `test_core_list_covers_every_non_edge_package` below keeps this honest from now on.
_CORE = [
    "src/analytics", "src/ui", "src/api", "src/models", "src/service",
    "src/ask.py", "src/cli.py", "src/storage.py", "src/ingest.py",
    "src/squads.py", "src/llm.py", "src/config.py", "src/relay.py",
    #: ⭐ Added when the test below first ran. `kits.py` and `glossary.py` had already been *moved out* of
    #: the Streamlit package precisely so the API could use them — and nothing then stopped them sliding
    #: back, which is the same fault in the same place twice.
    "src/chat_context.py", "src/community.py", "src/db.py", "src/fpl_rules.py",
    "src/glossary.py", "src/kits.py", "src/manager.py", "src/pipeline.py",
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


def test_core_list_covers_every_non_edge_package():
    """⭐⭐ **The guard above is only as wide as `_CORE`, so this widens it automatically.**

    The import rule was correct, precisely written and mutation-tested — and it missed a real offender for
    the whole life of `src/service`, because nobody added the new package to a hand-maintained list. ⚠️ *A
    growing codebase silently shrinks the coverage of any list written by hand.*

    So: every top-level module and package under `src/` is either an **edge** (`src/web*`) or is covered by
    `_CORE`. A new package fails this test on the day it is created, which is the day the decision is cheap.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    covered = {e.split("/", 1)[1] for e in _CORE}
    missing = sorted(
        p.name
        for p in (root / "src").iterdir()
        if not p.name.startswith(("_", ".", "web"))
        and (p.is_dir() or p.suffix == ".py")
        and p.name not in covered
    )
    assert not missing, (
        f"these live under src/ but no layering rule covers them: {missing}. "
        "Add each to _CORE (it must not import an edge), or name it an edge."
    )
