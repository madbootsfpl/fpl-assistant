"""The Android launcher icon is MADBOOTS, not Flutter's default (ADR-279).

⚠️⚠️ **This shipped wrong, and the check I ran could not have caught it.** The icons were "generated"
by a shell loop that silently did nothing, leaving Flutter's blue logo in place — and the verification
was *"is xxxhdpi 192 pixels?"*, which **Flutter's default already is**.

⭐⭐ *A check that the right answer and the wrong answer both satisfy is not a check.* The same shape as
the `greaterThan(0)` that accepted a fabricated 99 (ADR-267), one day apart.

⭐ So this compares **content**: each density must be a resize of the same 1024px master iOS uses — which
also means a new logo cannot land on one platform and not the other.
"""

import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MASTER = ROOT / "mobile/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png"
MIPMAP = ROOT / "mobile/android/app/src/main/res"

#: The Android launcher densities and their pixel sizes.
DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}


def test_the_master_icon_exists():
    """⭐ Both platforms are generated from one file, so its absence breaks both."""
    assert MASTER.exists(), f"the 1024px master is missing: {MASTER}"


@pytest.mark.parametrize("density,size", DENSITIES.items())
def test_each_density_is_a_resize_of_the_master(tmp_path, density, size):
    """⚠️ **Content, not dimensions.** Flutter's defaults are already exactly these sizes, so a size
    check passes whether the icon was replaced or not — which is how the blue logo reached a tablet."""
    icon = MIPMAP / f"mipmap-{density}/ic_launcher.png"
    assert icon.exists(), f"{density} launcher icon is missing"

    expected = tmp_path / "expected.png"
    subprocess.run(
        ["sips", "-z", str(size), str(size), str(MASTER), "--out", str(expected)],
        check=True, capture_output=True,
    )
    assert icon.read_bytes() == expected.read_bytes(), (
        f"mipmap-{density}/ic_launcher.png is not the MADBOOTS master resized to {size}px. "
        f"Regenerate it — see docs/03_Architecture/Android_Builds.md."
    )


def test_the_icon_is_not_flutters_default():
    """⭐ Named separately from the comparison above, because *this* is the failure that happened, and a
    test that says what went wrong is worth more than one that says what should be true."""
    from hashlib import sha256

    # Flutter's stock xxxhdpi launcher icon, as shipped by `flutter create` on 3.47.
    flutter_default = "3c34e1f298d0"
    digest = sha256((MIPMAP / "mipmap-xxxhdpi/ic_launcher.png").read_bytes()).hexdigest()[:12]
    assert digest != flutter_default, (
        "the Android launcher icon is still Flutter's blue logo — the icon generation did not run"
    )
