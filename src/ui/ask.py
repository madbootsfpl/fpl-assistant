"""Console rendering for the `ask` command (ADR-034, ADR-036).

Shows the analytics decision (always) — a one-line headline, or a structured `detail` table
for the multi-transfer plan — then the LLM's explanation, or, when the model is unavailable, a
fallback. The point: `ask` is useful with or without the LLM, and the table is the exact truth.
"""


def render_ask(result, *, ollama_hint: bool = True, markdown: bool = False) -> str:
    """`ollama_hint` (US-375): the CLI (local) offers "Start Ollama for a written summary"; the **web** passes
    False — a deployed user can't start Ollama (it's local-only), so the hint would only confuse. The full
    plan/table/facts + ✓/⚠ always render regardless.

    `markdown` (US-399): the **web** passes True → the aligned plan/facts table is wrapped in a ``` fence so it
    keeps its monospace alignment, while the prose (question · explanation · ✓/⚠) renders as normal chat text
    instead of one raw terminal block. The CLI/FastAPI leave it False → **byte-identical** plain text."""
    def _mono(text: str) -> str:                    # keep aligned content monospace when rendering markdown
        return f"```\n{text}\n```" if markdown else text

    if result.headline is None and result.detail is None:
        # A free-form answer (ADR-085): prose but no grounded decision → show it with the ℹ label.
        if result.explanation:
            return "\n".join([f"Q: {result.question}", "", result.explanation,
                              _trust_line(result.trust)]).rstrip()
        # Otherwise an unrecognised question / empty result — just the message.
        head = f"Q: {result.question}\n\n" if result.intent else ""
        return f"{head}{result.message or ''}".rstrip()

    # The decision: a structured detail table (a plan → monospace), else a one-line headline (prose).
    lines = [f"Q: {result.question}", ""]
    lines.append(_mono(result.detail) if result.detail else result.headline)

    if result.explanation:
        lines += ["", result.explanation, _trust_line(result.trust)]
    elif result.detail is None:
        # Degraded and no table → show the grounded facts (+ how to enable prose, CLI only).
        facts = "\n".join(["Facts:"] + [f"  {k.replace('_', ' ')}: {v}" for k, v in (result.facts or {}).items()])
        lines += ["", _mono(facts)]
        if ollama_hint:
            lines += ["", "(Start Ollama — `ollama serve` with the model pulled — for a written "
                      "explanation.)"]
    elif ollama_hint:
        # A table is present (it's the exact data) but no prose — the CLI can enable it.
        lines += ["", "(Start Ollama for a written summary.)"]
    return "\n".join(lines)


def _trust_line(trust) -> str:
    """A visible ✓/⚠ line (ADR-037): the explanation checked against the data, or the gaps."""
    if trust is None:
        return ""
    if trust.get("free_form"):   # ADR-085: an ungrounded general answer — the honest third state
        return ("\nℹ General FPL advice — not checked against your data. For your squad, ask a specific "
                "question (captain / transfer / health …) and the answer is verified (✓).")
    numbers, names = trust.get("numbers", []), trust.get("names", [])
    if not numbers and not names:
        return "\n✓ Checked: every figure and name in the explanation traces to the data above."
    bits = []
    if numbers:
        bits.append("figures " + ", ".join(numbers))
    if names:
        bits.append("names " + ", ".join(names))
    return (f"\n⚠ Unverified in the explanation ({'; '.join(bits)}) — the data above is the "
            "source of truth.")
