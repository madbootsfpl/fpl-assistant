"""The iPhone runbook's commands must work from where it says to run them (ADR-239).

⚠️ **This exists because the document broke itself.** Step 2 said `cd mobile && flutter devices`, which
leaves the shell inside `mobile/`; step 3 then said `open mobile/ios/Runner.xcworkspace`, which from there
resolves to `mobile/mobile/ios/…`. Both lines were correct in isolation and the pair was wrong.

⭐⭐ **A runbook is code that a person executes**, and the failure mode is the same as a script's: state
left behind by one step breaking the next. The difference is that nothing type-checks it, so ⭐ *the paths
in a runbook need a test for the same reason the paths in a script do not.*
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs" / "03_Architecture" / "iPhone_Free_Provisioning.md"


def _bash_blocks(text):
    return re.findall(r"```bash\n(.*?)```", text, re.S)


@pytest.fixture(scope="module")
def runbook():
    if not RUNBOOK.exists():  # pragma: no cover - the doc is committed
        pytest.skip(f"no {RUNBOOK}")
    return RUNBOOK.read_text()


def test_no_command_changes_the_readers_directory(runbook):
    """⭐ A `cd` inside brackets is a subshell and dies with the command; a bare one outlives it.

    ⚠️ The distinction is invisible when you read the line that has it and only matters to the line
    *after* — which is exactly the sort of thing that never gets noticed in review.
    """
    offenders = []
    for block in _bash_blocks(runbook):
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("cd ") or " && cd " in stripped:
                offenders.append(stripped)
    assert not offenders, (
        f"these lines leave the reader's shell somewhere else, so the NEXT step's paths break: "
        f"{offenders}. Wrap them in brackets — `(cd mobile && …)` — so the change dies with the command."
    )


def test_every_path_the_runbook_opens_exists(runbook):
    """⚠️ **The fault that started this**: a path that is right from one directory and wrong from another.

    Resolved from the repo root, because that is where the document now says every command runs.
    """
    missing = []
    for block in _bash_blocks(runbook):
        for path in re.findall(r"\bopen ([^\s#]+)", block):
            if not (ROOT / path).exists():
                missing.append(path)
    assert not missing, (
        f"the runbook opens paths that do not exist from the repo root: {missing}"
    )


def test_the_scripts_it_names_are_real_and_runnable(runbook):
    """⭐ A runbook naming a script that was renamed is worse than one naming none — it sends someone
    hunting for a typo in a command that was never going to work."""
    import os

    for script in set(re.findall(r"\b(scripts/[\w./-]+\.sh)", runbook)):
        path = ROOT / script
        assert path.exists(), f"the runbook names {script}, which does not exist"
        assert os.access(path, os.X_OK), f"{script} is not executable, so the command as written fails"


def test_the_wifi_address_is_not_presented_as_a_fact(runbook):
    """⭐⭐ `192.168.1.35` appears as an EXAMPLE, and it has to stay one.

    ⚠️ It is a DHCP lease on one particular Mac. A reader who types it because the document stated it
    plainly gets a refusal that looks like every other refusal — so wherever it appears, the document has
    to have said the address comes from the script.
    """
    if "192.168.1." not in runbook:
        pytest.skip("the runbook no longer shows an example address")
    assert "scripts/serve_api.sh" in runbook, (
        "the runbook shows a LAN address but never tells the reader where to get their own"
    )
    for phrase in ("prints the address", "can change"):
        assert phrase in runbook, (
            f"the runbook shows a LAN address without saying it {phrase!r} — "
            f"a reader will type this machine's lease and get an unexplained refusal"
        )
