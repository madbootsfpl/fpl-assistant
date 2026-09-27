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


def test_the_script_exists_and_runs() -> None:
    assert SCRIPT.exists(), "the iPhone is a document again"
    import os

    assert os.access(SCRIPT, os.X_OK), "not executable — `bash scripts/…` is a workaround, not a command"


def test_the_api_address_is_baked_in_at_build_time(script: str) -> None:
    """⚠️⚠️ **`flutter install` has no `--dart-define`**, so the address must be set when the app is built.
    ⭐ A build without it points at `localhost` — *which on a phone is the phone* — and every screen fails
    with nothing to say why."""
    build = next(line for line in script.splitlines() if "flutter build ios" in line)

    assert "--dart-define=MADBOOTS_API=" in build
    assert "--release" in build, "a debug build judges the wrong thing on a phone"


def test_the_developer_server_field_is_not_in_a_real_build(script: str) -> None:
    """⭐ `MADBOOTS_DEV` adds Settings ▸ Server for aiming at a laptop (ADR-270). ⚠️ *A build that can be
    pointed anywhere is a build that can be pointed at nothing*, and this one is the real app."""
    assert "MADBOOTS_DEV" not in script.replace("# ", "", 1) or "no `MADBOOTS_DEV`" in script
    build = next(line for line in script.splitlines() if "flutter build ios" in line)
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
