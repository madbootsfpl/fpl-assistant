"""The Flutter app's brand tokens still match `brand.py`.

⭐⭐ **`brand.py` is the single source of truth for the product's identity** (ADR-103/114), and says so in
its own comment: *"consume these, don't re-type hexes."* A Dart theme holding `Color(0xFF8B2FC9)` would be
that instruction ignored on a new surface — one rule with two implementations, which is what ADRs 123, 127
and 181 are each about, and what ADR-219 and ADR-220 both found in a *contract*.

⚠️ **A generator alone would not be enough, because nothing makes anyone run it.** The failure this guards
is small and silent: the purple moves on the web, nobody regenerates, and the phone quietly ships last
season's brand. ⭐ *A generated file with no guard is a copy with extra steps.*

This lives in the Python suite on purpose — that is the suite CI runs, so it is the one that can actually
stop a commit. The Dart side has no equivalent gate yet (ADR-221).
"""

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_brand_dart.py"
DART = ROOT / "mobile" / "lib" / "brand.dart"

sys.path.insert(0, str(ROOT / "scripts"))


def test_the_committed_dart_matches_a_fresh_generation():
    """⚠️ **Regenerate, do not hand-edit.** If this fails, run

        venv/bin/python scripts/generate_brand_dart.py

    and commit the result — the web and the phone had drifted apart.
    """
    from generate_brand_dart import render

    assert DART.exists(), f"{DART} is missing — run {GENERATOR.name}"
    assert DART.read_text() == render(), (
        "mobile/lib/brand.dart no longer matches brand.py. Regenerate it rather than editing it; a hand "
        "edit here is a second definition of the brand."
    )


def test_a_palette_change_would_fail_this():
    """⭐ **The guard proved against the thing it guards**, not merely asserted. A test that compares a file
    to itself passes whatever happens — ask *"if the purple moved, would this fail?"*"""
    from src.web_streamlit import brand

    original = brand.PURPLE
    try:
        brand.PURPLE = "#123456"
        from generate_brand_dart import render
        assert DART.read_text() != render(), "a changed palette must not still match the committed file"
        assert "0xFF123456" in render(), "…and the change must actually reach the generated Dart"
    finally:
        brand.PURPLE = original


@pytest.mark.parametrize("token", ["mantra", "tagline", "disclaimer"])
def test_the_words_travel_too_not_only_the_colours(token):
    """⭐ The mantra was rewritten twice (ADR-182) — once because it promised AI the deployed app could not
    deliver, once because spoken aloud it was indistinguishable from *"shows it's working"*. ⚠️ A phone
    carrying a retired mantra is exactly the drift ADR-184 found surviving fourteen days on six surfaces."""
    from src.web_streamlit import brand

    value = getattr(brand, token.upper())
    assert value in DART.read_text(), f"brand.{token.upper()} has not reached the Flutter app"


def test_the_generated_file_says_it_is_generated():
    """⚠️ Without this the first person to open it edits it, and the next regeneration silently reverts
    their work. ⭐ *A generated file has to say so in the place someone would type.*"""
    head = DART.read_text()[:600]
    assert "generated" in head.lower()
    assert "generate_brand_dart.py" in head, "…and it must name the script that writes it"


def test_the_generated_file_is_stable_under_dart_format():
    """⚠️⚠️ **Two tools fighting over one file is a loop with no stable state** (ADR-242).

    `dart format` rewrapped the long string constants, which failed the byte-for-byte comparison above;
    regenerating unwrapped them, which the formatter then rewrapped. ⭐ *The visible symptom was a test
    failing for a file nobody had edited*, which is the kind of failure people learn to re-run past.

    The fix is a `// dart format off` marker inside the generated output. ⚠️ **The formatter recognises it
    only verbatim** — a trailing comment on the same line disables it silently, which cost one round here —
    and `formatter: exclude:` in `analysis_options.yaml` does not help, because `dart format lib/` with an
    explicit path ignores the exclusion.
    """
    lines = DART.read_text().splitlines()
    marker = "// dart format off"
    assert marker in lines, (
        f"the generated file has no verbatim {marker!r} line, so `dart format` will rewrap it and "
        f"test_the_committed_dart_matches_a_fresh_generation will fail for a file nobody edited"
    )
    # ⚠️ Verbatim means *alone on its line*. This is the mistake that cost a round.
    assert lines[lines.index(marker)] == marker
    # ⭐ And it must come before any code, or it governs nothing.
    assert lines.index(marker) < next(i for i, ln in enumerate(lines) if ln.startswith("import ")), (
        "the marker sits after the imports, so the code above it is still formatted"
    )


def test_the_app_wordmark_is_the_brands_wordmark():
    """⚠️⚠️ **MAD purple · BOOTS orange** — `brand.py`'s `wordmark_html` is the rule, and the phone had
    been rendering BOOTS in **white** since the app was built.

    ⭐⭐ Nobody decided that. The palette is generated into `brand.dart`, but the *wordmark* — which colour
    goes on which half — was retyped in Dart, so it drifted. **A generated palette does not stop a
    hand-written rule from disagreeing with it**, and the owner spotted it on a phone screen before any
    test did.

    ⚠️ The purple is deliberately the **light** shade on the app's dark ground — `brand.py` itself says a
    caller should *"pick a shade legible on the surface (e.g. `PURPLE_LT` on a dark band)"*. So this
    asserts the *orange* exactly and the purple as one of the sanctioned two.
    """
    import re
    import sys

    sys.path.insert(0, str(ROOT))
    from src.web_streamlit import brand

    dart = (ROOT / "mobile" / "lib" / "main.dart").read_text()
    block = re.search(r"text: 'MAD'.*?text: 'BOOTS'.*?color: ([\w.]+)", dart, re.S)
    assert block, "the wordmark in main.dart no longer looks like MAD + BOOTS — update this guard with it"
    boots = block.group(1)
    assert boots == "Brand.orange", (
        f"BOOTS renders in {boots}; brand.py's wordmark_html puts it in {brand.ORANGE}. "
        f"The two-tone split is the brand, not a style choice."
    )

    mad = re.search(r"text: 'MAD'.*?color: ([\w.]+)", dart, re.S).group(1)
    assert mad in {"Brand.purple", "Brand.purpleLight"}, f"MAD renders in {mad}"
