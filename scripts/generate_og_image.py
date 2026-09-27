"""Render `site/og-image.png` — the card a link shows when the site is shared.

⭐⭐ **Rendered by the browser, not drawn by hand.** The wordmark is set in the page's own `--heavy` stack
(Arial Black) and **italicised by synthesis** — there is no Arial Black Italic file — so an image library
cannot reproduce it without faking the slant. ⚠️ *The asset a link shows is the worst place for an
approximation of the brand.*

⚠️⚠️ **It was hand-made, and it drifted** (ADR-312): the committed card set the wordmark **upright** while
every other typeset instance is italic, and it had no generator, so nothing would ever have said so. ⭐ Now
it reads `brand.py` like the palette and the Dart tokens do.

⚠️ The drawn logo keeps its own two-word lettering — that is `brand.LOGO_ART_EXEMPT`, decided in ADR-312 §4:
*the illustration letters the name in its own style; wherever the name is SET IN TYPE it is MADBOOTS.*

Run: `venv/bin/python scripts/generate_og_image.py`
"""

import base64
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.web_streamlit import brand  # noqa: E402

OUT = ROOT / "site" / "og-image.png"
ART = ROOT / "site" / "favicon.png"          # the drawn logo, boots + its own lettering
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH, HEIGHT = 1200, 630


def html() -> str:
    art = base64.b64encode(ART.read_bytes()).decode()
    slant = "italic" if brand.WORDMARK_ITALIC else "normal"
    return f"""<!doctype html><meta charset="utf-8"><style>
  html,body{{margin:0;width:{WIDTH}px;height:{HEIGHT}px;background:{brand.INK};overflow:hidden}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
        display:flex;flex-direction:column;justify-content:center;padding:0 86px;box-sizing:border-box}}
  /* ⚠️ In flow, not absolute: positioned, it sat on top of the "MAD" it was meant to introduce. */
  .art{{width:150px;height:auto;margin:0 0 22px}}
  /* ⭐ The same setting every other surface uses, from brand.py. */
  .mark{{font-family:"Arial Black","Helvetica Neue",Impact,sans-serif;font-style:{slant};
         font-weight:{brand.WORDMARK_WEIGHT};font-size:104px;letter-spacing:{brand.WORDMARK_TRACKING_EM}em;
         line-height:1;margin:0 0 16px}}
  .mad{{color:{brand.MAD_ON_DARK}}} .boots{{color:{brand.ORANGE}}}
  .tag{{font-family:"Arial Black","Helvetica Neue",Impact,sans-serif;font-style:{slant};
        font-weight:{brand.WORDMARK_WEIGHT};font-size:40px;color:{brand.DARK_TEXT};margin:0 0 16px;
        letter-spacing:{brand.WORDMARK_TRACKING_EM}em}}
  .lede{{font-size:26px;color:{brand.DARK_MUTED};font-weight:600;margin:0 0 22px}}
  .url{{font-size:24px;color:{brand.GREEN};font-weight:800;margin:0}}
</style>
<img class="art" src="data:image/png;base64,{art}" alt="">
<p class="mark"><span class="mad">MAD</span><span class="boots">BOOTS</span></p>
<p class="tag">{brand.TAGLINE}</p>
<p class="lede">The FPL tool that does the maths for you.</p>
<p class="url">madboots.com</p>
"""


def main() -> None:
    if not pathlib.Path(CHROME).exists():
        print(f"  ✗ Chrome not found at {CHROME} — cannot render")
        raise SystemExit(1)
    with tempfile.TemporaryDirectory() as tmp:
        page = pathlib.Path(tmp) / "og.html"
        page.write_text(html())
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             f"--window-size={WIDTH},{HEIGHT}", "--virtual-time-budget=5000",
             f"--screenshot={OUT}", f"file://{page}"],
            check=True, capture_output=True,
        )
    print(f"  wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
