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

import pytest
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
MASTER = ROOT / "mobile/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png"
MIPMAP = ROOT / "mobile/android/app/src/main/res"

#: The Android launcher densities and their pixel sizes.
DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}


def test_the_master_icon_exists():
    """⭐ Both platforms are generated from one file, so its absence breaks both."""
    assert MASTER.exists(), f"the 1024px master is missing: {MASTER}"


#: How far a real resize sits from a reference resize, and how far the wrong icon sits. ⭐⭐ **Measured, not
#: chosen**, against Flutter's actual default launcher icon — the image that caused ADR-279:
#:
#:     density     ours vs master    FLUTTER'S DEFAULT vs master
#:     mdpi             5.78                   93.40
#:     hdpi             5.69                   93.46
#:     xhdpi            4.84                   92.80
#:     xxhdpi           3.41                   92.50
#:     xxxhdpi          2.57                   92.63
#:
#: ⭐ A **16× gap**, so the threshold is not a fine judgement. Ours differ from the reference at all only
#: because the committed icons were resized by a different resampler than the one here.
MAX_MEAN_DIFF = 20.0


def mean_abs_diff(a: Image.Image, b: Image.Image) -> float:
    """Mean per-channel difference between two same-size images, 0-255."""
    pa, pb = a.convert("RGBA").tobytes(), b.convert("RGBA").tobytes()
    assert len(pa) == len(pb)
    return sum(abs(x - y) for x, y in zip(pa, pb)) / len(pa)


@pytest.mark.parametrize("density,size", DENSITIES.items())
def test_each_density_is_a_resize_of_the_master(density, size):
    """⚠️ **Content, not dimensions.** Flutter's defaults are already exactly these sizes, so a size
    check passes whether the icon was replaced or not — which is how the blue logo reached a tablet.

    ⚠️⚠️⚠️ **This used to shell out to `sips`, which exists only on macOS** — so on every Linux runner it
    raised `FileNotFoundError` and the five densities failed. ⭐⭐ *A check that can only run on the author's
    machine is a check CI does not have*, and CI is the only place it would have caught a regression nobody
    was looking for.

    ⭐ Compared by **pixels rather than bytes**, and deliberately: byte-exactness was a property of one
    resampler on one OS version, so it would have broken on the next macOS update as surely as it broke on
    Linux. The tolerance is measured against the real failure — see `MAX_MEAN_DIFF`.
    """
    icon = MIPMAP / f"mipmap-{density}/ic_launcher.png"
    assert icon.exists(), f"{density} launcher icon is missing"

    shipped = Image.open(icon)
    assert shipped.size == (size, size), f"mipmap-{density} is {shipped.size}, not {size}x{size}"

    reference = Image.open(MASTER).resize((size, size), Image.LANCZOS)
    difference = mean_abs_diff(shipped, reference)

    assert difference <= MAX_MEAN_DIFF, (
        f"mipmap-{density}/ic_launcher.png differs from the MADBOOTS master by {difference:.1f} "
        f"(a real resize scores under {MAX_MEAN_DIFF}; Flutter's default scores ~93). "
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
