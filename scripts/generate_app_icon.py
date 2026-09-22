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


def _ink() -> tuple[int, int, int]:
    """The brand's ink as RGB — ⚠️ read from `brand.py`, never typed here (ADR-103/114)."""
    raw = brand.INK.lstrip("#")
    return tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4))


def render(size: int, badge: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (size, size), _ink())
    edge = max(1, int(size * INSET))
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

    # ⚠️ Transparent here, unlike the app icons: the header sits on the app's own background, and an inked
    # square would show as a box around the badge.
    FLUTTER_ASSET.parent.mkdir(parents=True, exist_ok=True)
    badge.resize((128, 128), Image.LANCZOS).save(FLUTTER_ASSET)
    print(f"  {FLUTTER_ASSET.relative_to(ROOT)}: the header badge")


if __name__ == "__main__":
    main()
