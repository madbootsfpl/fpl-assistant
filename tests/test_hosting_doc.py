"""The hosting runbook must name every environment variable the API actually reads.

⭐⭐ **This test exists because a variable was documented for the wrong deployment.**
`FPL_FEEDBACK_WEBHOOK` was written up in `docs/BETA.md` as a *Streamlit* secret and never carried into the
Render instructions, so in-app feedback could not have worked on the first live build no matter what else
was right (ADR-261). ⚠️ *A variable documented for one deployment is not documented for the next one.*

⭐ Like `test_core_list_covers_every_non_edge_package`, this replaces a hand-maintained list with a
derived one: a new `os.environ.get` in the service layer fails this test on the day it is written.
"""

import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "03_Architecture" / "Hosting_The_API.md"

#: ⚠️ Where the *deployed* API can reach. Deliberately not all of `src/` — the CLI and the Streamlit edge
#: read variables that have nothing to do with this host.
_SERVED = ["src/service", "src/relay.py", "src/db.py"]


def _env_names_read_by(path: pathlib.Path) -> set[str]:
    """Every literal environment-variable name this file looks up — via the AST, not a text scan.

    ⚠️ A substring scan would match the names inside the very prose that documents them.
    """
    names: set[str] = set()
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        attr = getattr(func, "attr", None)
        if attr in {"get", "getenv"} and node.args and isinstance(node.args[0], ast.Constant):
            target = getattr(func, "value", None)
            source = getattr(target, "attr", None) or getattr(target, "id", None)
            if source in {"environ", "os"} and isinstance(node.args[0].value, str):
                names.add(node.args[0].value)
    return {n for n in names if n.startswith("FPL_")}


def test_the_hosting_doc_names_every_variable_the_api_reads():
    doc = DOC.read_text()
    read: set[str] = set()
    for entry in _SERVED:
        p = ROOT / entry
        for f in (p.rglob("*.py") if p.is_dir() else [p]):
            read |= _env_names_read_by(f)

    assert read, "found no environment variables at all — the scan is broken, not the docs"
    missing = sorted(name for name in read if name not in doc)
    assert not missing, (
        f"the API reads these but {DOC.name} never names them: {missing}. "
        "Anyone following the runbook deploys without them and the feature silently does nothing."
    )


def test_the_doc_says_what_happens_without_the_feedback_sink():
    """⚠️ Naming a variable is not the same as saying what its absence costs.

    The failure mode here is **silent**: feedback answers honestly and is still never delivered. A table row
    that only said *"optional"* would leave the runbook technically complete and practically wrong.
    """
    doc = DOC.read_text()
    assert "FPL_FEEDBACK_WEBHOOK" in doc
    row = next(line for line in doc.splitlines() if line.startswith("| `FPL_FEEDBACK_WEBHOOK`"))
    assert "does not reach you" in row, "the row must say what is lost, not just that it is optional"


def test_every_beta_runbook_section_it_cites_exists():
    """⚠️ **A citation to a section that does not exist sends a reader somewhere there is no help.**

    This file pointed at `BETA.md §1C` for Web3Forms, which lives under **§1B** — written from memory of a
    structure rather than from the structure. ⭐ *Cross-references rot silently: nothing fails, the reader
    just arrives nowhere*, and this repo has hit it before (the iPhone runbook, after a renumber).
    """
    beta = (ROOT / "docs" / "BETA.md").read_text()
    headings = set(re.findall(r"^#{2,4}\s*(\d+[A-Z]?)\.", beta, re.M))
    assert headings, "found no numbered sections in BETA.md — the scan is broken, not the citation"

    cited = set(re.findall(r"BETA\.md`?\s*§(\d+[A-Z]?)", DOC.read_text()))
    missing = sorted(c for c in cited if c not in headings)
    assert not missing, f"cites BETA.md sections that do not exist: {missing} (it has {sorted(headings)})"
