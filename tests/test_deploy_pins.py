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


@pytest.mark.parametrize("name", sorted(DEPLOY_FILES))
def test_the_solver_is_pinned_wherever_it_is_installed(name):
    """⚠️ `pulp` by name, because it is the one that already broke and the one that is *least* obviously
    needed — both other files carry a comment apologising for it (`src.analytics.__init__` imports the
    optimiser, so it is on the import path even where nothing solves). ⭐ *A dependency nobody thinks they
    use is the one whose pin gets dropped in a tidy-up.*"""
    specs = [spec for _, spec in _requirements(name) if spec.lower().startswith("pulp")]
    assert specs, f"{name} no longer installs pulp — if that is deliberate, ADR-310's note needs revisiting"
    assert any(spec.replace(" ", "").lower() == "pulp==3.3.2" for spec in specs), (
        f"{name} does not pin pulp==3.3.2. PuLP 4.0.0 removes `PULP_CBC_CMD`, which `optimizer.py:276` "
        "calls at solve time — squad builds, gameweek plans and My Squad all stop answering."
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
