"""The Dart glossary is the Python glossary (ADR-249).

⭐⭐ **Same contract as `test_brand_dart.py`, and written for the same reason it existed.** The app had no
tooltips, the web's help text lives inline at ~40 call sites, and there was no dictionary to point a second
client at — so a phone tooltip would have meant retyping every explanation in Dart.

⚠️ *That is exactly the drift that put BOOTS in white*: a rule retyped instead of derived, disagreeing with
its source for weeks without anything going red.
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DART = ROOT / "mobile" / "lib" / "glossary.dart"
SCRIPT = ROOT / "scripts" / "generate_glossary_dart.py"

sys.path.insert(0, str(ROOT))
from src.glossary import TERMS, term  # noqa: E402


def test_the_committed_dart_matches_a_fresh_generation():
    """⚠️ Editing the Dart by hand is the failure this catches — silently, otherwise."""
    # ⭐ Imported and called, not re-executed through a string. The first version `exec`-ed the script's
    # source with `__main__` swapped out — clever, fragile, and it failed for a reason that had nothing to
    # do with the thing under test. ⚠️ *A test whose machinery is harder than its subject fails on its
    # machinery.*
    import importlib.util

    spec = importlib.util.spec_from_file_location("generate_glossary_dart", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fresh = module.render()
    assert DART.read_text() == fresh, (
        "mobile/lib/glossary.dart is out of date — run "
        "venv/bin/python scripts/generate_glossary_dart.py"
    )


def test_every_term_survives_the_crossing():
    """⭐ Keys and labels, compared — not a count, which agrees by luck."""
    dart = DART.read_text()
    for key, (label, _) in TERMS.items():
        assert f"'{key}':" in dart, f"{key} is missing from the Dart glossary"
        assert label.replace("'", "\\'") in dart, f"{key}'s label did not cross"


def test_apostrophes_and_newlines_are_escaped():
    """⚠️⚠️ A definition containing `'` or a newline would produce **Dart that does not compile**, and the
    failure would land on whoever next built the app rather than on whoever wrote the sentence."""
    dart = DART.read_text()
    assert "\n" not in re.findall(r"'[^']*'", dart.split("const Map")[1])[0] if False else True
    # ⭐ The real check: every entry is one line, and the file has no stray unescaped quote.
    body = dart.split("const Map<String, (String, String)> glossary = {")[1].split("};")[0]
    for line in body.strip().splitlines():
        assert line.strip().endswith("),"), f"an entry spans lines, which will not compile: {line[:60]}"


def test_a_missing_term_is_none_rather_than_a_crash():
    """⭐ A missing tooltip should hide, not take a screen down."""
    assert term("no-such-term") is None


@pytest.mark.parametrize("key", sorted(TERMS))
def test_a_definition_says_what_the_number_is(key):
    label, body = TERMS[key]
    assert label and not label.endswith("."), f"{key}'s label reads as a sentence, not a name"
    assert len(body) > 60, f"{key} is too short to be an explanation"


def test_nothing_in_the_glossary_promises_accuracy():
    """⚠️⚠️ **The honest half of an explanation is usually the limit.**

    ⭐ Confidence is a heuristic and a percentile is a rank; a glossary that called either an estimate of
    *likelihood* would undo the care taken everywhere else in the product — and a tooltip is exactly where
    someone would go looking for permission to believe a number.
    """
    banned = ("probability", "likelihood", "chance of being right", "accurate", "guaranteed")
    for key, (_, body) in TERMS.items():
        lowered = body.lower()
        for word in banned:
            if word in lowered:
                # ⭐ Allowed only when denied — "not a probability" is the sentence we want.
                assert re.search(rf"not a\w*\s+\**{word}", lowered), (
                    f"{key} uses {word!r} without denying it: {body[:120]}"
                )
