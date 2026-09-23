"""The hosted image carries what it needs and nothing that would mislead it (ADR-256).

⭐⭐ **Written after running the image, not before.** Two bugs came out of `docker run` that reading the
Dockerfile would never have shown: the container reported `"version": "unknown"`, and `/health` answered
`200 {"ok": true}` while **every real request 500-ed**. A platform polling health would have kept that
instance in rotation and a tester would have met it.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
IGNORE = ROOT / ".dockerignore"
API_REQS = ROOT / "requirements-api.txt"


def _directives(text: str) -> str:
    """The Dockerfile with its comments stripped.

    ⚠️⚠️ **Because a comment explaining why something is absent contains the thing.** The first version of
    the test below searched the whole file for `--reload` and failed on the sentence *"No `--reload`"* —
    ⭐ *a grep for a string finds the paragraph that says it is not there.*
    """
    return "\n".join(ln for ln in text.splitlines() if not ln.strip().startswith("#"))



def _packages(path: Path) -> set[str]:
    out = set()
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line and not line.startswith("-"):
            out.add(re.split(r"[\[><=;]", line)[0].strip().lower())
    return out


def test_the_api_image_does_not_install_the_web_stack():
    """⭐ Measured: the app's full requirements are **481 MB** and the API loads **193 MB** of them. The
    difference is Streamlit's stack — ⚠️ *installing a rendering library into an image that renders
    nothing is the waste `requirements-pipeline.txt` was written to stop.*"""
    api = _packages(API_REQS)
    for web_only in ("streamlit", "pandas", "pyarrow", "altair", "authlib"):
        assert web_only not in api, f"{web_only} is in the API image and the API never imports it"


def test_it_keeps_the_dependencies_the_api_actually_imports():
    """⚠️⚠️ **`pulp` is not optional.** `src.analytics.__init__` imports the optimiser, so dropping it
    fails at **import**, not at use — the same trap `requirements-pipeline.txt` records."""
    api = _packages(API_REQS)
    for needed in ("fastapi", "uvicorn", "requests", "psycopg", "pulp"):
        assert needed in api, f"{needed} is missing — the image will fail at import, not at use"


def test_the_image_excludes_the_committed_database():
    """⚠️⚠️ **The one exclusion that is about correctness, not size.**

    `config.DB_PATH` falls back to `data/seed.db` when no DSN is set. An image carrying that file would
    **silently serve a month-old board** instead of failing — ⭐ *and a stale board that renders perfectly
    is exactly the failure ADR-248 exists to make visible.*
    """
    # ⚠️ Comments stripped first — the paragraph above these lines *names* `data/` while explaining why
    # it is excluded, so a naive search finds the explanation instead of the rule.
    ignored = {ln.strip() for ln in _directives(IGNORE.read_text()).splitlines() if ln.strip()}
    assert "data/" in ignored or "data" in ignored
    assert "src/web_streamlit/" in ignored or "src/web_streamlit" in ignored


def test_the_container_listens_on_the_platforms_port():
    """⚠️ Every host injects `$PORT`, and a hard-coded port is the commonest first-deploy failure: the
    container starts, listens on the wrong number, and the platform reports it unhealthy with no clue."""
    # ⚠️⚠️ Comments stripped, for the third time in this file. Two mutations survived the first draft —
    # a hard-coded port and a shipped database — because the **comments explaining those very rules**
    # contained the strings being searched for. ⭐ *A test that reads a file must read the part that runs.*
    text = _directives(DOCKERFILE.read_text())
    assert "${PORT}" in text or "$PORT" in text
    assert "0.0.0.0" in text, "binding to localhost would refuse everything the platform sends"


def test_it_does_not_run_as_root_and_does_not_reload():
    text = DOCKERFILE.read_text()
    assert re.search(r"^USER\s+(?!root)", text, re.M), "an image running as root is one CVE from mattering"
    assert "--reload" not in _directives(text), (
        "--reload watches the filesystem and serves stale code from a read-only layer"
    )


def test_health_can_report_that_it_cannot_serve():
    """⭐⭐⭐ **The bug that `docker run` found and reading never would.**

    With no `FPL_DATABASE_URL`, the container answered `/health` with `200 {"ok": true}` and 500-ed every
    real request. ⚠️ *A platform polling health would have kept it in rotation*, and the failure would have
    reached a tester as "the app is broken".

    ⭐ Health answers *can this instance serve?* — a different question from *is the process alive?*, and
    only the first is worth reporting.
    """
    source = (ROOT / "src" / "service" / "http" / "app.py").read_text()
    assert '"ok": reachable' in source, "health is reporting a constant again"
    assert "_can_serve" in source


def test_the_version_survives_not_being_pip_installed():
    """⚠️ `requirements-api.txt` deliberately omits `-e .`, so `importlib.metadata` has nothing to read in
    the container — it reported `"unknown"`. ⭐ *A deployment that cannot say which build it is cannot be
    diagnosed*, and the phone's own connection check asserts the field is non-empty."""
    source = (ROOT / "src" / "service" / "http" / "app.py").read_text()
    assert "pyproject.toml" in source, "there is no fallback for an uninstalled package"

    from src.service.http.app import _VERSION

    assert _VERSION and _VERSION != "unknown"
