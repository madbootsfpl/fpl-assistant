"""The app's icons are MADBOOTS, not Flutter's default — on **every** surface (ADR-279).

⚠️⚠️ **This shipped wrong, and the check I ran could not have caught it.** The icons were "generated"
by a shell loop that silently did nothing, leaving Flutter's blue logo in place — and the verification
was *"is xxxhdpi 192 pixels?"*, which **Flutter's default already is**.

⭐⭐ *A check that the right answer and the wrong answer both satisfy is not a check.* The same shape as
the `greaterThan(0)` that accepted a fabricated 99 (ADR-267), one day apart.

⭐ So this compares **content**: each density must be a resize of the same 1024px master iOS uses — which
also means a new logo cannot land on one platform and not the other.

⚠️⚠️⚠️ **And it happened a third time, because this file only watched Android.** While the home-screen icon
(`scripts/generate_app_icon.py`'s own opening line) and the launcher icon (ADR-279) were each being fixed,
the **web build kept all five of its stock Flutter icons** — the browser-tab favicon, both PWA icons, and the
`apple-touch-icon` an iPhone uses when you add the site to a home screen. ⭐⭐ *A guard that names one surface
teaches everyone the other surfaces are covered*, and nobody looked at the tab for a month.
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


# ── the web build wears the same badge ────────────────────────────────────────

def generator():
    """The real `scripts/generate_app_icon.py`, imported from disk (`scripts/` is not a package)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("gen", ROOT / "scripts" / "generate_app_icon.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: ⭐ Tighter than `MAX_MEAN_DIFF`, because this compares each file against **what the generator would write
#: for it**, not against a resize of the master — so the only difference left is the resampler's.
MAX_REGENERATION_DIFF = 2.0


@pytest.mark.parametrize("relative", sorted(generator().WEB_ICONS))
def test_every_web_icon_is_the_badge_the_generator_renders(relative):
    """⚠️⚠️ **Including the maskable pair, which a naive check gets wrong.** They sit at a deliberately
    tighter inset (a platform crops a maskable icon to its own shape, and only the central ~80% survives), so
    measured against a plain resize of the master they score **22.6** — ⭐ *above the threshold, and correct.*

    So each file is compared against the generator's own `render()` at that icon's own inset. ⭐⭐ *Comparing a
    committed asset to the code that produces it is a stronger question than "does it look about right"* —
    and it is the question a reader actually has: **is this file stale?**
    """
    gen = generator()
    size, inset = gen.WEB_ICONS[relative]
    committed = gen.WEB / relative
    assert committed.exists(), f"{relative} is missing — run scripts/generate_app_icon.py"

    shipped = Image.open(committed)
    assert shipped.size == (size, size), f"{relative} is {shipped.size}, not {size}x{size}"

    expected = gen.render(size, Image.open(gen.BADGE).convert("RGBA"), inset)
    difference = mean_abs_diff(shipped, expected)

    assert difference <= MAX_REGENERATION_DIFF, (
        f"mobile/web/{relative} is not what the generator renders (differs by {difference:.1f}; "
        f"Flutter's stock icon scores ~145). Run: venv/bin/python scripts/generate_app_icon.py"
    )


def test_the_generator_covers_every_icon_the_web_build_ships():
    """⭐ The list-that-rots guard, in the place it already rotted once: a sixth PNG added to `mobile/web/`
    and not taught to the generator is the exact shape of how five Flutter icons survived two icon fixes."""
    gen = generator()

    on_disk = {str(p.relative_to(gen.WEB)) for p in gen.WEB.rglob("*.png")}
    generated = set(gen.WEB_ICONS)

    assert on_disk == generated, (
        f"mobile/web PNGs and WEB_ICONS disagree.\n"
        f"  shipped but never generated: {sorted(on_disk - generated) or 'none'}\n"
        f"  generated but not on disk:   {sorted(generated - on_disk) or 'none'}"
    )


def test_the_manifest_points_at_icons_that_exist():
    """⚠️ A PWA manifest naming a missing file degrades silently — the install prompt simply offers a
    generic square, which is the failure this whole file exists to stop, one indirection along."""
    import json

    gen = generator()
    manifest = json.loads((gen.WEB / "manifest.json").read_text())

    for entry in manifest["icons"]:
        assert (gen.WEB / entry["src"]).exists(), f"manifest names {entry['src']}, which is not there"


# ── the rest of the web shell ─────────────────────────────────────────────────

def test_the_web_shell_says_madboots_not_flutter():
    """⚠️⚠️⚠️ **The icon was only the visible half.** The web build also shipped Flutter's *words* — both
    the page and the manifest described the app as **"A new Flutter project."** — and, worse, Flutter's
    **colour**: `theme_color: #0175C2` is the blue a phone paints the PWA splash and the iOS status bar with
    when somebody adds the app to a home screen.

    ⭐⭐ *Replacing the icon and leaving that would have been the same bug wearing a different property*, and
    the one place nobody looks is the one a new user sees first.
    """
    import json

    from src.web_streamlit import brand

    page = (ROOT / "mobile/web/index.html").read_text()
    manifest = json.loads((ROOT / "mobile/web/manifest.json").read_text())

    assert "A new Flutter project" not in page
    assert "A new Flutter project" not in json.dumps(manifest)

    # ⭐ Read from `brand.py`, never typed here (ADR-103/114) — the same rule the icon generator follows.
    assert manifest["short_name"] == brand.NAME
    assert brand.NAME in manifest["name"] and brand.TAGLINE in manifest["name"]
    assert brand.NAME in page and brand.TAGLINE in page

    for key in ("theme_color", "background_color"):
        assert manifest[key].lower() == brand.INK.lower(), (
            f"manifest {key} is {manifest[key]}, not the brand ink — #0175C2 is Flutter blue"
        )
