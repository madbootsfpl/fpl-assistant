"""The iPhone is part of a release (ADR-316).

⚠️⚠️⚠️ **It was left behind twice.** Android and web are one command each; the iPhone was a *document* —
`docs/03_Architecture/iPhone_Free_Provisioning.md` — and twice a build went out to two platforms while the
owner's own phone stayed on an older one. ⭐ *A step that must happen every release and lives only in prose
is a step that gets skipped.*

⭐ These pin the handful of things the script must not lose. Running it needs a phone; **reading it does
not**, which is the only reason this file can exist at all.
"""

from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release_ios.sh"


@pytest.fixture(scope="module")
def script() -> str:
    return SCRIPT.read_text()


def _code(script: str) -> str:
    """The script with its comments stripped.

    ⚠️⚠️ **Added because a comment broke a test that was looking for a command.** ADR-379's note explains
    the cached-profile bug and quotes `flutter build ios` in prose; `test_the_api_address_is_baked_in_at_
    build_time` took the *first* line containing that string and got the explanation. ⭐ *A test that greps
    a script cannot tell code from the paragraph describing it, and the paragraph is the part that keeps
    getting written.*
    """
    return "\n".join(ln for ln in script.splitlines() if not ln.lstrip().startswith("#"))


def test_the_script_exists_and_runs() -> None:
    assert SCRIPT.exists(), "the iPhone is a document again"
    import os

    assert os.access(SCRIPT, os.X_OK), "not executable — `bash scripts/…` is a workaround, not a command"


def test_the_api_address_is_baked_in_at_build_time(script: str) -> None:
    """⚠️⚠️ **`flutter install` has no `--dart-define`**, so the address must be set when the app is built.
    ⭐ A build without it points at `localhost` — *which on a phone is the phone* — and every screen fails
    with nothing to say why."""
    build = next(line for line in _code(script).splitlines() if "flutter build ios" in line)

    assert "--dart-define=MADBOOTS_API=" in build
    assert "--release" in build, "a debug build judges the wrong thing on a phone"


def test_the_developer_server_field_is_not_in_a_real_build(script: str) -> None:
    """⭐ `MADBOOTS_DEV` adds Settings ▸ Server for aiming at a laptop (ADR-270). ⚠️ *A build that can be
    pointed anywhere is a build that can be pointed at nothing*, and this one is the real app."""
    assert "MADBOOTS_DEV" not in script.replace("# ", "", 1) or "no `MADBOOTS_DEV`" in script
    build = next(line for line in _code(script).splitlines() if "flutter build ios" in line)
    assert "MADBOOTS_DEV" not in build


def test_it_installs_rather_than_runs(script: str) -> None:
    """⭐ `flutter run` stays attached, and quitting it **terminates the app on the phone** — ⚠️ *a release
    script whose last act can uninstall its own release is not a release script.*"""
    assert "flutter install" in script
    assert "flutter run" not in script


def test_the_device_is_discovered_not_typed(script: str) -> None:
    """⚠️ The provisioning doc names a device id in prose — ⭐ *and a device id in prose is one that goes
    stale the day the phone is replaced.*"""
    assert "flutter devices --machine" in script
    assert "00008150" not in script, "a hard-coded device id crept back in"


def test_it_asks_the_phone_whether_the_app_is_there(script: str) -> None:
    """⭐⭐ **A build that succeeded and an app that is on the device are different claims** — and this
    script exists because the second was assumed twice."""
    assert "devicectl" in script, "nothing verifies the install against the device"


def test_the_seven_day_expiry_is_said_out_loud(script: str) -> None:
    """⚠️ Free provisioning stops launching after a week. ⭐ *The cost people forget is the one nobody
    prints*, and it is the actual argument for the £79 — not distribution."""
    assert "SEVEN DAYS" in script or "seven days" in script.lower()


def test_the_android_release_points_at_the_other_two() -> None:
    """⭐ Where the omission actually happened: whoever cuts a build reads *that* script's last line."""
    android = (ROOT / "scripts" / "release_android.sh").read_text()

    assert "release_ios.sh" in android, "cutting a build still does not mention the iPhone"
    assert "release_web.sh" in android


# ---- ADR-379: the seven days, made real and then stated ---------------------

LIB = ROOT / "scripts" / "lib" / "ios_profile.sh"


def _call(func: str, *args: str) -> str:
    """Run one function from the helper. ⭐ The release script itself needs a phone; this does not, which
    is the whole reason the arithmetic was moved out of it."""
    import subprocess

    quoted = " ".join(f'"{a}"' for a in args)
    out = subprocess.run(["bash", "-c", f'source "{LIB}"; {func} {quoted}'],
                         capture_output=True, text=True)
    return out.stdout.strip()


NOW = "2026-10-30T19:49:21Z"


def _now_epoch() -> str:
    return _call("iso_epoch", NOW)


def test_the_helper_reads_an_apple_timestamp():
    # ⚠️ BSD date needs the format spelled out; GNU `date -d` does not exist on a stock Mac.
    assert _call("iso_epoch", "2026-11-06T19:48:46Z").isdigit()


def test_hours_left_is_positive_for_a_live_profile_and_negative_for_a_dead_one():
    assert _call("hours_left", "2026-11-06T19:48:46Z", _now_epoch()) == "167"
    # 🔴 The actual failure: installed 14:35, profile expired 14:52, dead by the evening.
    assert _call("hours_left", "2026-10-30T14:52:03Z", _now_epoch()) == "-4"


def test_a_profile_about_to_expire_is_purged_and_a_healthy_one_is_kept():
    """⭐⭐ The decision that was never made at all.

    `flutter build ios` re-signs with whatever profile is cached, so a build on day seven inherits
    seventeen minutes. Purging the stale file is what makes *"re-running this fixes it"* true.
    """
    import subprocess

    def purge(expiry: str) -> bool:
        r = subprocess.run(["bash", "-c",
                            f'source "{LIB}"; should_purge "{expiry}" 48 "{_now_epoch()}"'])
        return r.returncode == 0

    assert purge("2026-10-30T14:52:03Z"), "an expired profile must be set aside"
    assert purge("2026-10-31T19:00:00Z"), "under 48h left is not worth keeping"
    assert not purge("2026-11-06T19:48:46Z"), "a fresh profile must be left alone"


def test_an_unreadable_date_is_never_treated_as_expired():
    """⚠️ The direction of the risk. Purging only helps if Apple then issues a replacement, so a profile
    whose date cannot be parsed must be left where it is — ⭐ *destroying the working thing on the strength
    of a failed measurement is the worst available outcome.*"""
    import subprocess

    r = subprocess.run(["bash", "-c", f'source "{LIB}"; should_purge "not-a-date" 48'])
    assert r.returncode != 0


def test_the_default_threshold_actually_purges_a_profile_with_a_day_left():
    """⚠️⚠️ **Asserting the DEFAULT, not a number passed in.** The first version of these tests handed
    `should_purge` a literal 48, so a mutant that set `IOS_PROFILE_MIN_HOURS=0` — disabling the purge
    entirely, which is the whole bug — passed every one of them. ⭐ *A constant exercised only through a
    value the test supplies is a constant the test does not cover.*
    """
    import subprocess

    def purge_at_default(expiry: str) -> bool:
        r = subprocess.run(["bash", "-c",
                            f'source "{LIB}"; '
                            f'should_purge "{expiry}" "$IOS_PROFILE_MIN_HOURS" "{_now_epoch()}"'])
        return r.returncode == 0

    assert purge_at_default("2026-10-31T19:00:00Z"), "~23h left must be purged at the default threshold"
    assert not purge_at_default("2026-11-06T19:48:46Z"), "a fresh week must survive the default threshold"


def test_the_threshold_is_not_always_reissue(script: str) -> None:
    """⭐ 48 hours, because purging a *useful* profile trades a working build for a network round trip that
    can fail — an offline laptop would go from an inconvenience to a failed release."""
    assert "IOS_PROFILE_MIN_HOURS" in script


def test_the_script_purges_before_it_builds(script: str) -> None:
    # ⚠️ Order is the whole point: a purge after the build re-signs with the stale profile anyway.
    code = _code(script)
    assert code.index("should_purge") < code.index("flutter build ios")


def test_the_script_sets_the_stale_profile_aside_rather_than_deleting_it(script: str) -> None:
    assert "mv " in script and "madboots-stale-profiles" in script
    assert "rm " not in script.split("1c. make the seven days real")[1].split("flutter build ios")[0]


def test_the_verdict_is_critical_for_the_bug_that_happened_and_ok_for_a_real_week():
    """🔴 The branch that decides the wording, tested — because the wording is what was wrong.

    The build installed at 14:35 on 2026-10-30 expired at 14:52. "Expires after SEVEN DAYS" was a true
    statement about free provisioning and a false one about that build. ⭐⭐ *The last place to leave
    untested is the branch that chooses which claim to make.*
    """
    now = _now_epoch()
    assert _call("expiry_verdict", "2026-11-06T19:48:46Z", now).startswith("ok 167")
    assert _call("expiry_verdict", "2026-10-30T20:00:00Z", now).startswith("critical 0")
    assert _call("expiry_verdict", "2026-10-30T14:52:03Z", now).startswith("critical -4")


def test_an_unreadable_or_missing_expiry_claims_nothing():
    # ⭐ "unknown" rather than a guess in either direction: the script then quotes the policy and says it
    # could not verify it, which is the one honest thing left to print.
    now = _now_epoch()
    assert _call("expiry_verdict", "wat", now) == "unknown"
    assert _call("expiry_verdict", "", now) == "unknown"


def test_the_closing_warning_reads_the_build_rather_than_quoting_the_policy(script: str) -> None:
    """🔴 The old line said "expires after SEVEN DAYS" — a true fact about free provisioning and a false
    one about the build it had just installed, which had seventeen minutes left. ⭐⭐ *A warning that states
    the policy instead of the measurement cannot tell you the policy was not applied.*
    """
    tail = script.split("5. say WHEN it dies")[1]
    assert "profile_expiry mobile/build/ios/iphoneos/Runner.app/embedded.mobileprovision" in tail
    assert "THIS BUILD EXPIRES IN" in tail, "a build with under a day left must say so loudly"
