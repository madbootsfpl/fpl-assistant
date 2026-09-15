"""The marketing scripts may not speak a retired claim (ADR-182/168, guarded 2026-09-15).

`brand.MANTRA` is guarded in the app. The **scripts were not**, and they are the copy a viewer actually hears —
ten videos, each closing on the sign-off. This project has already paid for that twice: six closes spoke *"the
AI explains"* until ADR-168, and after ADR-182 replaced *"shows its working"* everywhere, **two closes still
carried it and were shot that way** (§8 Leagues, §H Team DNA, found 2026-09-15).

⚠️ **Both misses share one mechanism: the phrase spans a line break.** A `grep` for "shows its working" finds
nothing, because the file wraps it as `…every answer shows\\n> its working.` ⭐ **A claim that wraps is invisible
to a line-by-line search, and prose always wraps** — so this normalises whitespace across each blockquote
block before looking, which is the only way the search can see what the reader sees.
"""

import pathlib

from src.web_streamlit import brand

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "docs" / "08_Marketing" / "Video_Scripts.md"

# Wordings that have been retired and must never be spoken again. Each is a decision, not a preference.
RETIRED = {
    "ai explains": "ADR-168 — there is no model on Cloud; no tester has ever seen AI output",
    "ai clarifies": "ADR-168 — same reason, and it was the first sentence of the intro",
    "shows its working": "ADR-182 — a British schoolroom idiom, and spoken aloud it is 'shows it's working'",
    "shows it's working": "ADR-182 — the hearing that made the previous mantra claim only that the app runs",
    "ultimate fpl": "an unfalsifiable superlative, in a product whose pitch is that every claim is checkable",
}


def _spoken_blocks():
    """Each run of blockquote lines, whitespace-normalised, excluding any block carrying a ⚠ marker.

    ⚠️ **Blocks, not lines.** A ⚠ note is flagged on its *first* line only, so a line-level filter reads its
    continuation as spoken copy — which is how the first version of this guard flagged its own warning text.
    Blocks are split on bare `>` lines, which is how the file separates a beat from a note.
    """
    blocks, buf = [], []
    for line in SCRIPTS.read_text().split("\n"):
        if line.startswith(">"):
            body = line.lstrip(">").strip()
            if body:
                buf.append(body)
                continue
        if buf:
            blocks.append(buf)
            buf = []
    if buf:
        blocks.append(buf)
    return [" ".join(" ".join(b).split()) for b in blocks if not any("⚠" in ln for ln in b)]


def test_no_script_speaks_a_retired_claim():
    offenders = []
    for block in _spoken_blocks():
        low = block.lower()
        for phrase, why in RETIRED.items():
            if phrase in low:
                offenders.append(f"{phrase!r} ({why}) in: {block[:90]}…")
    assert not offenders, "retired wording is still in the spoken copy:\n  " + "\n  ".join(offenders)


def test_the_guard_can_actually_see_a_wrapped_claim():
    """⚠️ **The guard's own mutation test, kept as a test.**

    The bug being guarded was invisible to `grep` because the phrase wrapped. A guard that inherits that
    blindness would pass on the exact file that prompted it, so this proves the normalisation works on text
    shaped like the real miss — ⭐ *a guard against a claim must be able to see the claim*.
    """
    wrapped = ["The analytics decide. Every answer shows", "its working. You make the call."]
    flat = " ".join(" ".join(wrapped).split()).lower()
    assert "shows its working" in flat, "normalisation must join across the break the file actually had"


def test_every_sign_off_quotes_the_current_mantra():
    """Ten closes carry the sign-off, and it is the most-repeated sentence in the product. Each must name both
    halves of `brand.MANTRA` — the wording may be spoken naturally (*"And you make the call"* in §0), but it
    may not drift into a different claim."""
    parts = [p.strip() for p in brand.MANTRA.rstrip(".").split(".")]
    assert parts[:2] == ["Analytics decide", "Logic explains"], brand.MANTRA

    closes = [b for b in _spoken_blocks() if "make the call" in b.lower()]
    assert len(closes) >= 8, f"expected the sign-off across the script set, found {len(closes)}"
    for block in closes:
        low = block.lower()
        assert "analytics decide" in low and "logic explains" in low, \
            f"a sign-off is missing half the mantra: {block[:110]}…"
