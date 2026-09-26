"""Generate the iOS/macOS app icons from the MADBOOTS badge.

⭐⭐ **The app shipped to a real home screen wearing Flutter's blue logo.** Nobody noticed until it was on
a phone among other apps — on a simulator you know which one you launched.

⚠️⚠️ **iOS icons must be fully opaque.** The badge is RGBA with a transparent surround; an icon with an
alpha channel is rejected at submission and renders with a black box in some places before that. So it is
composited onto the brand's ink, which is also what the badge's own dark preview uses.

⭐ **Resolution, honestly.** The badge master is 298×298. The largest icon iOS actually *renders on a
device* is 180×180 (60pt @3x), so every on-device size is a **downscale** and loses nothing. The 1024
asset is upscaled and will be soft — it is used only by the App Store, which is not a thing we do yet.
📌 A proper 1024 render from `~/Downloads/madboots1.svg` (real vector, 5 paths) is owed before submission;
this machine has no SVG rasteriser installed.

Run: `venv/bin/python scripts/generate_app_icon.py`
"""

import json
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.web_streamlit import brand  # noqa: E402

BADGE = ROOT / "src" / "web_streamlit" / "assets" / "madboots-badge.png"
IOS = ROOT / "mobile" / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
MACOS = ROOT / "mobile" / "macos" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
# ⭐ The header's badge comes from here too, so the icon and the wordmark can never be different marks.
FLUTTER_ASSET = ROOT / "mobile" / "assets" / "madboots-badge.png"

# ⭐ The badge is a hexagon with its own outline, so it wants air around it rather than bleeding to the
# corners the way a flat glyph would.
INSET = 0.82

#: ⭐ **A maskable icon is cropped by the platform**, to a circle or a squircle of its choosing, and only the
#: central ~80% is guaranteed to survive. ⚠️ At the ordinary inset the hexagon's points sit exactly where the
#: crop lands, so the badge needs to pull further in for these two — *the same art, framed for a mask.*
MASKABLE_INSET = 0.62

#: Web/PWA icons — path under `mobile/web/` → (pixel size, inset).
#:
#: ⚠️⚠️⚠️ **Flutter's blue logo shipped a third time.** This file's own opening line records the first
#: (a home screen) and ADR-279 the second (the Android launcher) — and while both were being fixed, the
#: **web build kept all five of its stock icons**: the favicon in the browser tab, both PWA icons, and the
#: `apple-touch-icon` an iPhone uses when you add it to the home screen. ⭐⭐ *The icon was regenerated twice
#: and the generator was never taught the third surface*, so the tab kept saying Flutter.
WEB = ROOT / "mobile" / "web"
WEB_ICONS = {
    # ⭐⭐ 32, not Flutter's 16, and **full bleed**: at tab size the badge is ~30 pixels across, and the
    # ordinary 18% margin spends six of them on ink. ⚠️ *A favicon is the one icon with no room for
    # composition* — at 0.82 it reads as a dark blob, at 1.0 the MB and the grin survive.
    "favicon.png": (32, 1.0),
    "icons/Icon-192.png": (192, INSET),              # also the apple-touch-icon in index.html
    "icons/Icon-512.png": (512, INSET),
    "icons/Icon-maskable-192.png": (192, MASKABLE_INSET),
    "icons/Icon-maskable-512.png": (512, MASKABLE_INSET),
}


def _ink() -> tuple[int, int, int]:
    """The brand's ink as RGB — ⚠️ read from `brand.py`, never typed here (ADR-103/114)."""
    raw = brand.INK.lstrip("#")
    return tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4))


def render(size: int, badge: Image.Image, inset: float = INSET) -> Image.Image:
    canvas = Image.new("RGB", (size, size), _ink())
    edge = max(1, int(size * inset))
    scaled = badge.resize((edge, edge), Image.LANCZOS)
    offset = (size - edge) // 2
    # ⭐ Pasted *through its own alpha*, which is what turns a transparent PNG into an opaque icon rather
    # than a badge on a black square.
    canvas.paste(scaled, (offset, offset), scaled)
    return canvas


def sizes_from(manifest: pathlib.Path) -> dict[str, int]:
    """Filename → pixel size, read from Xcode's own `Contents.json`.

    ⭐⭐ **Derived, not listed.** A hard-coded table of Apple's icon sizes is a table that goes stale the
    next time Xcode adds an idiom — and the symptom is a missing icon in one place only.
    """
    spec = json.loads(manifest.read_text())
    out = {}
    for entry in spec["images"]:
        if "filename" not in entry:
            continue
        points = float(entry["size"].split("x")[0])
        scale = int(entry["scale"].rstrip("x"))
        out[entry["filename"]] = round(points * scale)
    return out


def main() -> None:
    badge = Image.open(BADGE).convert("RGBA")
    for folder in (IOS, MACOS):
        manifest = folder / "Contents.json"
        if not manifest.exists():
            print(f"  skipped {folder.relative_to(ROOT)} — no Contents.json")
            continue
        wrote = 0
        for filename, size in sorted(sizes_from(manifest).items(), key=lambda kv: kv[1]):
            render(size, badge).save(folder / filename)
            wrote += 1
        print(f"  {folder.relative_to(ROOT)}: {wrote} icons")

    # ⭐ The web build is the same app in a browser, so it wears the same icon — see `WEB_ICONS`.
    wrote = 0
    for relative, (size, inset) in sorted(WEB_ICONS.items(), key=lambda kv: kv[1][0]):
        target = WEB / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        render(size, badge, inset).save(target)
        wrote += 1
    print(f"  {WEB.relative_to(ROOT)}: {wrote} icons (favicon, PWA, apple-touch)")

    # ⚠️ Transparent here, unlike the app icons: the header sits on the app's own background, and an inked
    # square would show as a box around the badge.
    FLUTTER_ASSET.parent.mkdir(parents=True, exist_ok=True)
    badge.resize((128, 128), Image.LANCZOS).save(FLUTTER_ASSET)
    print(f"  {FLUTTER_ASSET.relative_to(ROOT)}: the header badge")


if __name__ == "__main__":
    main()
