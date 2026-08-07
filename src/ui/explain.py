"""Render a grounded Why / Risk / Confidence block (Sprint 104, ADR-089).

A plain-text block from an `analytics.Explanation` — the ✓ reasons, the ⚠ risks, and the heuristic confidence
(score + band). Shown above a decision's detail in `ask`/CLI/web, so a user sees *why* and can trust or
challenge it. The confidence is a transparent heuristic (from the signals listed), not a probability.
"""


def render_explanation(explanation) -> str:
    """`explanation` is an `analytics.Explanation`. One block: a Confidence line + Why (✓) / Risk (⚠) lists."""
    if explanation is None:
        return ""
    lines = [
        f"Confidence: {explanation.confidence} / 100 · {explanation.band}   "
        "(a heuristic from the signals below — not a probability)",
    ]
    if explanation.reasons:
        lines.append("")
        lines.append("Why")
        lines += [f"  ✓ {r}" for r in explanation.reasons]
    if explanation.risks:
        lines.append("")
        lines.append("Risk")
        lines += [f"  ⚠ {r}" for r in explanation.risks]
    return "\n".join(lines)
