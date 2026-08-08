"""Console rendering for an FPL-rules answer (Sprint 100, ADR-085).

A plain-text block of the curated rules facts the question matched — the *truth* the LLM narrates over (and
is verified against, ✓). Shows with or without the model; the same "the block is the truth" shape the other
`ask` details use.
"""


def render_rules(matched) -> str:
    """`matched` is a list of `(topic, fact)` pairs from `fpl_rules.match_rules`.

    A single-concept fact shows as one `•` bullet; a multi-item fact is authored with its own bullet lines
    (a lead + `• item` lines) and is printed **verbatim**, so a list like the chips reads item-per-line
    (US-283, tester feedback). Facts are separated by a blank line for readability."""
    blocks = [fact if "\n" in fact else f"  • {fact}" for _topic, fact in matched]
    return "\n".join(["FPL rules", "", "\n\n".join(blocks)])
