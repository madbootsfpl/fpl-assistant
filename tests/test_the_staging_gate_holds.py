"""Nothing reaches the testers until someone decides it should (ADR-340).

⭐⭐ **The iPhone is the staging environment**, because it already was one: `release_ios.sh` installs to
one phone, and every other route publishes to all nine testers at once.

⚠️⚠️ **This re-introduces the step ADR-290 removed**, which automated publishing because *"a publish step
a person has to remember is a publish step that measures how busy they are"* — the live build once sat
three releases behind. The step buys a test gate now, but the failure mode is unchanged, so these tests
pin the two things that make it survivable: the gate is honoured by **both** publishers, and the scripts
say loudly what is and is not live.
"""

import pathlib
import re

import pytest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
PUBLISHERS = ("release_android.sh", "release_web.sh")


def read(name: str) -> str:
    return (SCRIPTS / name).read_text()


@pytest.mark.parametrize("name", PUBLISHERS)
def test_every_publisher_honours_the_gate(name):
    """🔴 **Both, or neither.** Each script deploys the *whole* `$SITE` folder, so gating only the
    Android one would let a later web deploy publish the staged `version.json` — and the nine testers
    would be prompted by a release nobody decided to make. ⭐ *A gate on one of two doors is a doorway.*
    """
    body = read(name)
    assert "MADBOOTS_STAGE_ONLY" in body, f"{name} can publish past the staging gate"

    # ⚠️ The check must come BEFORE the token branch, or a set token wins and publishes anyway.
    gate = body.index("MADBOOTS_STAGE_ONLY")
    deploy = body.index("wrangler@4 pages deploy")
    assert gate < deploy, f"{name} reaches wrangler before it checks the gate"


@pytest.mark.parametrize("name", PUBLISHERS)
def test_a_staged_run_never_reaches_wrangler(name):
    """⭐ Structural, not textual: the deploy sits in a branch the gate does not fall through to."""
    body = read(name)
    staged_branch = re.search(
        r'if \[ -n "\$\{MADBOOTS_STAGE_ONLY:-\}" \]; then(.*?)\nelif ', body, re.S)
    assert staged_branch, f"{name} has no staged branch"
    assert "wrangler" not in staged_branch.group(1), f"{name} publishes while staging"


def test_staging_does_not_claim_the_testers_have_it():
    """⚠️⚠️ The closing line is the only thing most readers read. It said *"Testers already have it"*
    unconditionally — ⭐ *a closing instruction that is wrong about what just happened is worse than
    none*, because it is the sentence someone acts on."""
    body = read("release_android.sh")
    staged = re.search(r'if \[ -n "\$\{MADBOOTS_STAGE_ONLY:-\}" \]; then\n(.*?)\nelif ',
                       body[body.index("NEXT:") - 600:], re.S)
    assert staged, "no staged closing message"
    assert "already have it" not in staged.group(1)
    assert "Nothing is live" in staged.group(1)


def test_the_two_commands_exist_and_are_runnable():
    for name in ("release_stage.sh", "release_ship.sh"):
        path = SCRIPTS / name
        assert path.exists(), f"{name} is missing"
        assert path.stat().st_mode & 0o111, f"{name} is not executable"


def test_shipping_says_what_it_is_about_to_publish():
    """⭐ `release_stage.sh` can run several times before anyone ships, so the build on disk is not
    necessarily the one you remember testing — ⚠️ *a publish step that does not name what it publishes
    is a publish step you cannot check.*"""
    body = read("release_ship.sh")
    assert "about to publish build" in body
    assert "version.json" in body


def test_staging_sets_the_flag_for_every_publisher_it_calls():
    """⚠️ Exported once, at the top — ⭐ *a flag passed to some children and not others is the bug this
    whole file exists to prevent.*"""
    body = read("release_stage.sh")
    assert re.search(r"^export MADBOOTS_STAGE_ONLY=1$", body, re.M)
    for name in PUBLISHERS:
        assert f"scripts/{name}" in body, f"release_stage.sh does not run {name}"
    # ⭐ And the iPhone install is NOT gated — it is the whole point.
    assert "scripts/release_ios.sh" in body


def test_a_failed_phone_install_does_not_read_as_a_failed_stage():
    """⚠️⚠️ **The first real run proved this.** The phone was off the Wi-Fi, the script exited 1 after a
    bare *"no iPhone found"*, and everything above it had already worked.

    ⭐ *A script that reports its last step as its outcome invites you to redo the ones that succeeded* —
    and redoing this one burns a build number for nothing.
    """
    body = read("release_stage.sh")
    assert "if ! scripts/release_ios.sh; then" in body, (
        "a failed install aborts the script with no explanation"
    )
    assert "IS STAGED" in body
    assert "do NOT re-run" in body
