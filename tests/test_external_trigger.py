"""The external pipeline trigger (ADR-378) must keep naming things that exist.

⭐⭐ **A Cloudflare Worker cannot be unit-tested from pytest and does not need to be** — it is one `fetch`
call with no branching worth asserting. What *can* rot is the **contract between two files in different
languages**: the worker hard-codes a workflow filename, a branch and an input name, and nothing in a
rename would tell it. ⚠️ *A trigger that dispatches a workflow that no longer exists fails silently every
fifteen minutes, and the only symptom is data quietly going stale.*

So these tests read the worker's source and check it against the workflow it claims to drive. ⭐ The same
shape as `test_setup_docs.py`: a cross-file claim, verified against the repo rather than remembered.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "trigger" / "worker.js"
WRANGLER = ROOT / "trigger" / "wrangler.toml"


def _const(name: str) -> str:
    """A `const NAME = "value";` from the worker — it has no module system pytest can import."""
    m = re.search(rf'^const {name} = "([^"]+)"', WORKER.read_text(), re.M)
    assert m, f"the worker no longer declares {name}"
    return m.group(1)


def _workflow() -> dict:
    return yaml.safe_load((ROOT / ".github" / "workflows" / _const("WORKFLOW")).read_text())


def test_the_worker_names_a_workflow_that_exists():
    assert (ROOT / ".github" / "workflows" / _const("WORKFLOW")).is_file()


def test_the_workflow_it_dispatches_accepts_being_dispatched():
    """⚠️ `workflow_dispatch` is not implied by `schedule`. Without it GitHub answers 422 and the trigger
    is a no-op that reports success nowhere."""
    triggers = _workflow()[True]            # PyYAML reads the `on:` key as the boolean True
    assert "workflow_dispatch" in triggers


def test_the_force_input_the_worker_sends_is_one_the_workflow_declares():
    # ⚠️ GitHub rejects the whole request for an undeclared input, so a typo here stops every tick.
    declared = (_workflow()[True]["workflow_dispatch"] or {}).get("inputs") or {}
    assert "force" in declared, f"the workflow declares {sorted(declared)}"


def test_the_trigger_never_forces_the_cadence_gate():
    """⭐⭐ The policy lives in `src/pipeline.py` and the trigger only supplies opportunities.

    `force: true` would bypass `refresh_due` ninety-six times a day and hammer FPL — and it would move the
    schedule back out of Python, which is the thing `data.yml`'s comment exists to prevent.
    """
    assert re.search(r"inputs:\s*\{\s*force:\s*false\s*\}", WORKER.read_text()), \
        "the worker must dispatch with force: false"


def test_the_branch_it_dispatches_is_this_repos_default():
    # ⭐ Two sources, because a skipped test guards nothing: `origin/HEAD` is the real answer but is not
    # always set on a fresh clone, and the checked-out branch is what CI is testing anyway.
    for cmd in (["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                ["git", "rev-parse", "--abbrev-ref", "HEAD"]):
        got = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        branch = got.stdout.strip().removeprefix("origin/")
        if got.returncode == 0 and branch and branch != "HEAD":
            assert _const("REF") == branch
            return
    pytest.skip("detached HEAD and no origin/HEAD — nothing to compare against")


def test_the_cron_is_at_least_as_often_as_the_tightest_policy_interval():
    """⭐ The trigger exists to make `cadence()`'s tightest interval reachable. If the cron were slower than
    the policy's shortest ask, the policy would still be unreachable and this whole worker would be
    decoration — which is the bug it was written to fix, reintroduced one layer up.
    """
    from src.pipeline import INTERVAL_LIVE, INTERVAL_PRE_DEADLINE

    crons = re.findall(r'"(\*/(\d+) \* \* \* \*)"', WRANGLER.read_text())
    assert crons, "wrangler.toml declares no minute-interval cron"
    every = min(int(m[1]) for m in crons)
    tightest = min(INTERVAL_LIVE, INTERVAL_PRE_DEADLINE).total_seconds() / 60
    assert every <= tightest, f"cron every {every} min cannot serve a {tightest:.0f} min policy"


def test_the_backstop_schedule_is_still_there():
    """⭐ *A replacement for an unreliable mechanism should not also be a single point of failure.*

    If the worker is deleted or Cloudflare's cron proves no better, the pipeline must fall back to today's
    behaviour rather than stopping. Deleting the `schedule:` block would make the worker exactly that.
    """
    assert _workflow()[True].get("schedule"), "data.yml lost its backstop schedule"


def test_the_worker_is_inert_without_its_secret():
    # ⭐ Same shape as the workflows: an unconfigured deployment does nothing rather than failing loudly
    # every quarter hour (and a fork of this repo never sees it).
    assert "if (!env.GITHUB_TOKEN)" in WORKER.read_text()
