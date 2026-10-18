"""The pre-push net exists and says how to turn it on (ADR-359).

⭐⭐ `.git/hooks/` is not version-controlled, so a committed hook only runs for someone who has pointed
`core.hooksPath` at it. ⚠️ *A hook nobody installs is a file*, and the install line is one `git config` —
which makes the README line the part most likely to rot, not the script.
"""

import os
import pathlib

HOOK = pathlib.Path(__file__).resolve().parents[1] / ".githooks" / "pre-push"
README = pathlib.Path(__file__).resolve().parents[1] / "README.md"


def test_the_hook_is_there_and_runnable():
    assert HOOK.exists(), "the committed pre-push hook has gone"
    assert os.access(HOOK, os.X_OK), f"{HOOK} is not executable — git will skip it silently"


def test_the_readme_says_how_to_install_it():
    """⚠️ Silently skipped is the failure mode: an uninstalled hook looks exactly like a passing one."""
    assert "core.hooksPath .githooks" in README.read_text(), (
        "the one line that activates the hook is not in the README"
    )


def test_it_says_out_loud_that_it_is_not_the_full_suite():
    """🔴 ⭐ *Green here is not green on CI* — the hook runs ten seconds of a five-minute suite and nothing
    Postgres-only. A net that lets itself be mistaken for a gate is worse than no net."""
    body = HOOK.read_text()
    assert "not a gate" in body
    assert "--no-verify" in body, "a hook with no documented escape is a hook that gets deleted"
