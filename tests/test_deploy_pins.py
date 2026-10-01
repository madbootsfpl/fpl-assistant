"""Every deployed dependency is pinned (ADR-322, completing ADR-310).

🔴 **This guard exists because the last one was written in the wrong file.** ADR-310 spent 24 days of red CI
on eight causes; the largest was unpinned `pulp` — PuLP 4.0.0 (2026-09-25) removes `PULP_CBC_CMD`, which was
**277 failures from one cause**. It pinned `pulp==3.3.2` in `requirements.txt`, whose comment reads *"Render
installs this same file."*

⚠️⚠️ Render does not. The `Dockerfile` reads `COPY requirements-api.txt .`, and `pulp` was still unpinned
there — so the break ADR-310 describes in the past tense was live in the image the phone talks to, held shut
only by the absence of a rebuild.

⭐⭐ *A fix applied to the file you were reading rather than the file that ships is worse than no fix, because
the comment explaining it reads as protection.* Hence a test that checks **every** deploy file, and checks
the `Dockerfile` still installs the one it is named against — the assumption that failed last time.
"""

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Each file, and what installs it — the second half matters as much as the first, because being wrong about
# it is the mistake this test exists to stop.
DEPLOY_FILES = {
    "requirements.txt": "Streamlit Community Cloud, CI and local dev",
    "requirements-api.txt": "the Dockerfile -> Render (the API the phone calls)",
    "requirements-pipeline.txt": "data.yml and backfill.yml, 24x a day unattended",
}


def _requirements(name: str) -> list[tuple[int, str]]:
    """Package lines only: no comments, no blanks, no `-e .`."""
    lines = (ROOT / name).read_text().splitlines()
    return [(n, line.split("#")[0].strip())
            for n, line in enumerate(lines, 1)
            if line.split("#")[0].strip() and not line.strip().startswith(("#", "-"))]


@pytest.mark.parametrize("name", sorted(DEPLOY_FILES))
def test_every_requirement_is_pinned_exactly(name):
    """⭐ **Pinned, not bounded.** `>=` on a deploy file is a floating version with extra characters: it still
    installs whatever is newest, which is precisely how PuLP 4 arrived. The maintenance cost is real and was
    accepted in ADR-322 — upgrades now happen when someone edits a file, never in front of nine testers.
    """
    floating = [f"{name}:{n}  {spec}" for n, spec in _requirements(name)
                if not re.search(r"==\s*\d", spec)]
    assert not floating, (
        f"unpinned requirements in a file installed by {DEPLOY_FILES[name]}:\n  "
        + "\n  ".join(floating)
        + "\n\nPin with `==`. A deploy that installs a version nothing tested is ADR-310's 24 days of red."
    )


# Which files are *expected* to install the solver, and why — ADR-323 moved the pipeline out of this set.
# ⭐ Stated as data rather than left implicit, so "should this file have pulp?" has one answer in one place.
SOLVER_FILES = {
    "requirements.txt": "the app runs squad builds in-process",
    "requirements-api.txt": "squad/build calls select_squad",
}


@pytest.mark.parametrize("name", sorted(DEPLOY_FILES))
def test_the_solver_is_pinned_where_it_is_used_and_absent_where_it_is_not(name):
    """⚠️ `pulp` by name, because it is the one that already broke (ADR-310) **and** the one that spent months
    installed somewhere nothing called it (ADR-323).

    ⭐⭐ Both halves are asserted, because the two failures are opposite and a test for one hides the other:
    a **missing pin** is a deploy that installs PuLP 4 and stops solving; a **reappearing pulp** in the
    pipeline's file is 16 MB downloaded and 36 MB unpacked, 24× a day, for an import that no longer
    happens. *A dependency nobody
    thinks they use is the one whose pin gets dropped in a tidy-up — and also the one that gets added back to
    make two files "match".*
    """
    specs = [spec for _, spec in _requirements(name) if spec.lower().startswith("pulp")]

    if name not in SOLVER_FILES:
        assert not specs, (
            f"{name} installs pulp again ({specs}). ADR-323 removed it: the solver left that import path when "
            "`import pulp` moved inside `optimizer.select_squad`, and nothing this file installs reaches it."
        )
        return

    assert specs, (
        f"{name} no longer installs pulp, but {SOLVER_FILES[name]} — so it needs the solver. If that has "
        "genuinely changed, move it out of SOLVER_FILES above rather than deleting this assertion."
    )
    assert any(spec.replace(" ", "").lower() == "pulp==3.3.2" for spec in specs), (
        f"{name} does not pin pulp==3.3.2. PuLP 4.0.0 removes `PULP_CBC_CMD`, which `select_squad` calls at "
        "solve time — squad builds, gameweek plans and My Squad all stop answering."
    )


def test_the_dockerfile_still_installs_the_file_this_test_guards():
    """🔴🔴 **The assumption that failed in ADR-310, now asserted.** Its pin went into `requirements.txt`
    because a comment said Render installed it. Nothing checked that sentence, and it was wrong.

    ⭐ *A test that pins the right versions in the wrong file is green and useless* — so this checks the
    wiring rather than the contents.
    """
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "requirements-api.txt" in dockerfile, (
        "the Dockerfile no longer installs requirements-api.txt, so the pins this suite checks are not the "
        "pins the deployed image gets — re-point DEPLOY_FILES above at whatever it installs now"
    )


# ── the tree, not just its roots (ADR-341) ───────────────────────────────────────────────────────

#: A direct dependency → packages pip will install underneath it. ⭐ Not exhaustive: these are the
#: *anchors*, chosen because each is a well-known sub-tree that cannot be absent if the parent is present.
TREE_ANCHORS: dict[str, set[str]] = {
    "requests": {"urllib3", "certifi", "idna", "charset-normalizer"},
    "fastapi": {"starlette", "pydantic", "pydantic-core", "anyio", "typing-extensions"},
    "uvicorn": {"click", "h11"},
    "streamlit": {"altair", "numpy", "pandas", "pyarrow", "packaging"},
}


def _pinned_names(name: str) -> dict[str, str]:
    """`{normalised package name: version}` for one deploy file."""
    out = {}
    for _, line in _requirements(name):
        pkg, _, version = line.partition("==")
        out[pkg.split("[")[0].strip().lower().replace("_", "-")] = version.strip()
    return out


@pytest.mark.parametrize("name", sorted(DEPLOY_FILES))
def test_the_transitive_tree_is_named_not_just_the_direct_dependencies(name):
    """⭐⭐ **A file of pinned direct dependencies is not a reproducible install.**

    Pinning only what you import leaves pip to choose everything underneath, so two installs from the
    identical file resolve differently on different days — which is how **urllib3 2.7.0** arrived here
    with three CVEs that nobody evaluated, because nobody chose the version.

    ⚠️ The anchors below are a *sample*, not the tree. This test cannot prove completeness offline; what
    it stops is the regression — someone bumping a direct pin and dropping the generated block with it.
    """
    pinned = _pinned_names(name)
    for parent, children in TREE_ANCHORS.items():
        if parent not in pinned:
            continue
        missing = sorted(children - pinned.keys())
        assert not missing, (
            f"{name} pins {parent} but not what it installs underneath: {missing} "
            f"— regenerate the transitive block ({DEPLOY_FILES[name]})"
        )


@pytest.mark.parametrize("name", sorted(DEPLOY_FILES))
def test_urllib3_is_past_the_streaming_cves(name):
    """🔴 CVE-2026-97687 / 97688 / 97689, all fixed in **2.8.0**.

    ⭐ None are reachable in this codebase — two need response streaming and one needs an HTTPS proxy, and
    there is neither (`git grep -E "stream=True|iter_content|read_chunked|proxies="` finds nothing). ⚠️ The
    pin is held anyway because *"not reachable today"* is a statement about today's code, and the next
    person to add a streaming download will not read this file first.
    """
    version = _pinned_names(name).get("urllib3")
    if version is None:
        return                                   # not every file pulls requests
    parts = tuple(int(p) for p in version.split(".")[:2])
    assert parts >= (2, 8), f"{name} pins urllib3=={version}; 2.8.0 is the first without the three CVEs"
