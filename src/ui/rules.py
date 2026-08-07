"""Console rendering for an FPL-rules answer (Sprint 100, ADR-085).

A plain-text block of the curated rules facts the question matched — the *truth* the LLM narrates over (and
is verified against, ✓). Shows with or without the model; the same "the block is the truth" shape the other
`ask` details use.
"""


def render_rules(matched) -> str:
    """`matched` is a list of `(topic, fact)` pairs from `fpl_rules.match_rules`. One bullet per fact."""
    lines = ["FPL rules", ""]
    lines += [f"  • {fact}" for _topic, fact in matched]
    return "\n".join(lines)
