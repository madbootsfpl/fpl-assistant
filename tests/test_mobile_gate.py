"""The Dart suite can actually stop something (ADR-322, closing ADR-221).

⭐⭐ **ADR-221 wrote the sentence and deferred the wiring**: *"the Dart half runs locally and not in CI — a
test nobody runs is not a guard, so wiring `flutter test` into the workflow belongs with creating the real
app."* The app exists, is on nine phones and publishes itself (ADR-290), so the condition has arrived.

⚠️ **This file lives in the Python suite on purpose**, for exactly the reason `tests/test_brand_dart.py`
gives about itself: that is the suite CI already runs, so it is the one that can stop a commit. A Dart test
asserting the Dart gate exists would be inside the thing it is checking.

⭐ What it pins is not behaviour but *wiring* — the four ways this could quietly return to where it started:
the workflow being deleted, one of its two commands being dropped, the release scripts building without
checking first, or the `analyze` step going back to exiting 1 on a dead config key.
"""

import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/mobile.yml"
RELEASE_SCRIPTS = ("release_android.sh", "release_ios.sh")


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


def test_a_mobile_workflow_exists_at_all():
    """⚠️ The whole of ADR-221's open cost was that this file did not exist."""
    assert WORKFLOW.exists(), (
        "`.github/workflows/mobile.yml` is gone — 481 Dart tests are back to running only when somebody "
        "remembers, which is ADR-221's 'a test nobody runs is not a guard'"
    )


def test_the_workflow_runs_both_analyze_and_test():
    """⚠️ **Both, because they catch different things.** `flutter analyze` never executes a widget, and
    `flutter test` never sees an unused import or a dead lint — dropping either halves the gate while
    leaving a green tick that looks identical."""
    steps = _workflow()["jobs"]["mobile"]["steps"]
    commands = " ; ".join(s.get("run", "") for s in steps)
    assert "flutter analyze" in commands, "the workflow no longer analyzes"
    assert "flutter test" in commands, "the workflow no longer runs the Dart tests"


def test_the_flutter_version_is_pinned():
    """⭐ Pinned for the reason PuLP is (ADR-310/322): a floating toolchain makes *"the tests broke"* and
    *"Flutter changed"* the same red tick, and telling them apart costs a morning."""
    steps = _workflow()["jobs"]["mobile"]["steps"]
    setup = next((s for s in steps if "flutter-action" in str(s.get("uses", ""))), None)
    assert setup is not None, "no flutter-action step — nothing installs Flutter"
    version = str(setup.get("with", {}).get("flutter-version", ""))
    assert version and version[0].isdigit(), (
        f"flutter-version is {version!r}; an unpinned or floating toolchain was explicitly rejected "
        "in ADR-322"
    )


def test_the_workflow_is_path_filtered_to_the_app():
    """⭐ The Dart suite has nothing to say about a Python commit, and a job that runs on everything is a job
    people learn to scroll past. (`on:` parses as `True` — YAML 1.1 reads the bare word as a boolean.)"""
    workflow = _workflow()
    triggers = workflow.get("on", workflow.get(True))
    assert any("mobile/**" in (triggers[event] or {}).get("paths", [])
               for event in ("push", "pull_request")), \
        "mobile.yml no longer filters on mobile/** — it now runs on commits it cannot say anything about"


@pytest.mark.parametrize("script", RELEASE_SCRIPTS)
def test_the_release_scripts_check_before_they_build(script):
    """⭐⭐ **The ordering is the assertion, not the presence.** ADR-290 made cutting a release the same act
    as shipping it, so there is no later review in which a failure could be caught — a check that runs after
    `flutter build` is a check that reports on an app already on its way to nine phones.

    ⚠️ And for Android specifically, the gate sits ahead of the **version bump** too: aborting after step 1
    would leave `pubspec.yaml` incremented with nothing shipped, so the next run would bump twice.
    """
    text = (ROOT / "scripts" / script).read_text()
    assert "flutter test" in text, f"{script} builds a release without running the Dart tests"
    assert "flutter analyze" in text, f"{script} builds a release without analyzing"
    assert text.index("flutter test") < text.index("flutter build"), (
        f"{script} runs its tests after `flutter build` — by then the build exists, and on Android "
        "ADR-290 has already begun publishing it"
    )


def test_analysis_options_has_no_unsupported_formatter_key():
    """🔴 **The one thing that made the gate impossible, and it was dead config.**

    `flutter analyze` exited 1 on a single warning — *"The option 'exclude' isn't supported by
    'formatter'"* — from a `formatter: exclude:` block in `mobile/analysis_options.yaml`. ⭐⭐ The block was
    already superseded: `tests/test_brand_dart.py` says in its own docstring that `formatter: exclude:`
    *"does not help"*, and the mechanism that works is the verbatim `// dart format off` marker the
    generators emit (and which that test pins). So removing it took away a warning, not a protection.

    ⚠️ Pinned because re-adding it is the natural thing to try when someone next wonders how the generated
    file is protected — and it would silently turn the gate red again.
    """
    options = yaml.safe_load((ROOT / "mobile/analysis_options.yaml").read_text())
    assert "exclude" not in (options.get("formatter") or {}), (
        "`formatter: exclude:` is back in analysis_options.yaml. The analyzer rejects that key, so "
        "`flutter analyze` exits 1 and every release and CI run fails on it. The generated files are "
        "protected by the `// dart format off` marker instead — see tests/test_brand_dart.py."
    )
