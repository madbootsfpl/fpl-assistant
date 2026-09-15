"""Wrap long answer lines under their own content, so nothing scrolls sideways (ADR-191).

The chip and gameweek blocks are fixed-width console output: a label, then a sentence. Their *static* prose
has always been hand-wrapped at 100 columns; their *dynamic* lines never were, and they have grown. The
wildcard line now runs past 230 characters — *"worth +306.8 xP — a fresh build beats your squad … you keep
only 3 of 15 … your weakest stretch GW12–GW14 … Confidence 95/100"* — which a terminal breaks at column 0 and
a `st.code` block does not break at all, so the reader scrolls a monospace box horizontally to finish a
sentence. (Owner, 2026-09-15.)

⚠️ **The hanging indent is the whole point.** Wrapping at column 0 would put the continuation of the Wildcard
line under the *label* column, where it reads as a new chip. Continuations align under the text they continue,
so the label column stays a column:

    Wildcard:       worth +306.8 xP — a fresh build beats your squad over this window; you keep
                    only 3 of 15; £4.1m of your squad cannot play.

**110 rather than the 100 the static prose uses**, and the reason is worth a line: almost every dynamic line
carries a ` · Confidence 40/100 · Low` suffix, which pushes an otherwise-comfortable line just past 100 and
orphans the last word on a line of its own. Wrapping at 100 produced

    Triple Captain: GW5 — Haaland (MCI), xP 6.3 (the highest single-GW ceiling)  · Confidence 40/100 ·
                    Low

which is worse than not wrapping that line at all. A ragged right edge between the two widths is invisible;
an orphan is not.
"""

import re
import textwrap

WIDTH = 110

# A leading `Label:` plus its padding — the column dynamic lines are written in. Deliberately narrow: it must
# not match a colon *inside* a sentence, or the hang would land in the middle of the prose.
_LABEL = re.compile(r"^([A-Z][\w' ]{0,20}:\s+)")

# ⚠️ **The confidence suffix is one unit of meaning, so it may not be split.** Nearly every dynamic line ends
# `· Confidence 40/100 · Low`, and a plain wrap puts `Low` alone on the next line — a lone band word under a
# sentence reads as a fragment, and it happened at 100 columns *and* at 110. Widening the block to chase it is
# whack-a-mole: the next line is always a few characters longer.
#
# Instead the suffix is welded into a single token for the duration of the wrap, so it moves down whole:
#
#     Free Hit:       GW9 — your best XI projects only 47.9 xP (your weakest single week)
#                     · Confidence 40/100 · Low
_CONF = re.compile(r"·\s*Confidence\s+\d+/100\s*·\s*\w+")
_WELD = "\x00"        # not a space, never in the data, swapped back before returning


def wrap_block(text: str, width: int = WIDTH) -> str:
    """Wrap every over-long line of `text` to `width`, continuing under the line's own content.

    Short lines, blank lines and alignment are untouched — a block that already fits comes back
    **byte-identical**, which is what makes this safe to apply to every answer rather than to chosen ones.
    """
    out = []
    for line in text.split("\n"):
        if len(line) <= width:
            out.append(line)
            continue
        line = _CONF.sub(lambda m: m.group(0).replace(" ", _WELD), line)
        body = line.lstrip(" ")
        indent = len(line) - len(body)
        label = _LABEL.match(body)
        hang = indent + (len(label.group(1)) if label else 0)
        # `break_long_words`/`break_on_hyphens` off: a long token here is a name or a figure like "GW12–GW14",
        # and splitting either mid-word turns a readable line into a puzzle.
        out += textwrap.wrap(body, width=width, initial_indent=" " * indent, subsequent_indent=" " * hang,
                             break_long_words=False, break_on_hyphens=False) or [line]
    return "\n".join(out).replace(_WELD, " ")
