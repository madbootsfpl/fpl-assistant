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

#: ⭐ **Every runbook, not the one that broke.** This file exists because the iPhone guide broke four
#: times on first use; applying its lessons only to that file would be fixing the instance and leaving the
#: class. ⚠️ *A guard that covers one document is a guard the next document does not get.*
RUNBOOKS = sorted((ROOT / "docs" / "03_Architecture").glob("*.md"))


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


def test_the_steps_are_numbered_in_order(runbook):
    """⚠️ Inserting a step renumbers everything after it, and a heading out of sequence reads as a
    missing step rather than an editing slip."""
    numbers = [int(n) for n in re.findall(r"(?m)^## Step (\d+) —", runbook)]
    assert numbers == list(range(1, len(numbers) + 1)), f"step headings run {numbers}"


def test_every_step_referred_to_actually_exists(runbook):
    """⭐⭐ **A cross-reference to a step number is a claim about the document**, and it is the first thing
    to rot when a step is inserted — *"re-run step 5"* kept pointing at the install after the install
    became step 4. ⚠️ Nothing about a stale number looks wrong; it just sends a reader to the wrong place.
    """
    headings = {int(n) for n in re.findall(r"(?m)^## Step (\d+) —", runbook)}
    # ⚠️ Case-insensitively, because prose says "step 4" and headings say "Step 4".
    referred = {int(n) for n in re.findall(r"(?i)\bstep (\d+)\b", runbook)}
    dangling = sorted(referred - headings)
    assert not dangling, (
        f"the runbook sends the reader to step(s) {dangling}, which do not exist. "
        f"It has steps {sorted(headings)}."
    )



# ── the same rules, applied to every runbook in the folder ───────────────────────────────────────

@pytest.mark.parametrize("path", RUNBOOKS, ids=lambda p: p.stem)
def test_no_runbook_changes_the_readers_directory(path):
    """⚠️ The iPhone guide's step 2 left the shell inside `mobile/` and step 3's path then resolved to
    `mobile/mobile/…`. ⭐ *Both lines were correct in isolation and the pair was wrong.*"""
    offenders = [
        line.strip()
        for block in _bash_blocks(path.read_text())
        for line in block.splitlines()
        if line.strip().startswith("cd ") or " && cd " in line.strip()
    ]
    assert not offenders, (
        f"{path.name}: these leave the reader's shell elsewhere, breaking the NEXT step: {offenders}"
    )


@pytest.mark.parametrize("path", RUNBOOKS, ids=lambda p: p.stem)
def test_every_runbook_names_real_scripts(path):
    import os

    for script in set(re.findall(r"\b(scripts/[\w./-]+\.sh)", path.read_text())):
        target = ROOT / script
        assert target.exists(), f"{path.name} names {script}, which does not exist"
        assert os.access(target, os.X_OK), f"{script} is not executable, so the command as written fails"


def test_the_hosting_runbook_marks_what_was_actually_run():
    """⭐⭐⭐ **The distinction that makes a runbook trustworthy.**

    ⚠️ The iPhone guide was written from knowledge and broke four times on first use — every fault a
    step-to-step interaction reading could not find. This one separates *executed* from *not executed*, so
    a reader knows which half has been through a machine and which half is still a plan.

    ⭐ *An unverified instruction is not a defect; an unverified instruction presented as a verified one
    is.*
    """
    text = (ROOT / "docs" / "03_Architecture" / "Hosting_The_API.md").read_text()
    assert "Executed on this machine" in text
    assert "Not executed" in text
    # Every step heading says which it is, so the marking cannot quietly stop partway down.
    headings = re.findall(r"(?m)^## Step \d+ — .*$", text)
    assert headings, "the hosting runbook has no steps"
    for heading in headings:
        assert "executed" in heading.lower(), f"unmarked step: {heading}"
