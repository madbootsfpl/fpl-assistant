"""Render a grounded Edge / Risk / Confidence block (Sprint 104, ADR-089).

A plain-text block from an `analytics.Explanation` — the ✓ reasons, the ⚠ risks, and the heuristic confidence
(score + band). Shown above a decision's detail in `ask`/CLI/web, so a user sees *why* and can trust or
challenge it. The confidence is a transparent heuristic (from the signals listed), not a probability.
"""


# The honest attribution line closing an explained answer (ADR-089): the analytics decide, the LLM only
# phrases — and the confidence is a heuristic, not a probability (the caveat folded in here, US-277/278).
# ⚠️ **This said "AI explains the reasoning" until 2026-09-10 (ADR-184), on six surfaces, and it was false
# for every tester.** There is no Ollama on Streamlit Cloud and Ask is behind `FPL_ADMIN_KEY`, so nothing
# here is narrated by a model: the Edge / Risk / Confidence block this note annotates is rule-based Python
# (`explain.py`), which is exactly what the sentence now says.
#
# ADR-168 retired that claim from the mantra and ADR-182 rewrote its successor — **and this line survived
# both**, because each guard checked the two places its author remembered rather than sweeping for the claim.
MODEL_NOTE = (
    "Model note:\n"
    "Analytics decide the recommendation; logic explains it. "
    "Confidence is a heuristic from the signals, not a probability."
)


def render_explanation(explanation) -> str:
    """`explanation` is an `analytics.Explanation`. One block: a Confidence line + Edge (✓) / Risk (⚠) lists."""
    if explanation is None:
        return ""
    # A clean confidence line (US-277/278) — the "heuristic, not a probability" caveat now lives once in the
    # shared MODEL_NOTE that closes the answer.
    lines = [f"Confidence: {explanation.confidence}/100 ({explanation.band})"]
    if explanation.reasons:
        lines.append("")
        lines.append("Edge")                          # MADBOOTS vocab (ADR-107): the advantage / the "why"
        lines += [f"  ✓ {r}" for r in explanation.reasons]
    if explanation.risks:
        lines.append("")
        lines.append("Risk")
        lines += [f"  ⚠ {r}" for r in explanation.risks]
    return "\n".join(lines)
