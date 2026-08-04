"""Console rendering for the `ask` command (ADR-034, ADR-036).

Shows the analytics decision (always) — a one-line headline, or a structured `detail` table
for the multi-transfer plan — then the LLM's explanation, or, when the model is unavailable, a
fallback. The point: `ask` is useful with or without the LLM, and the table is the exact truth.
"""


def render_ask(result) -> str:
    # Unrecognised question, or an empty result — just the message.
    if result.headline is None and result.detail is None:
        head = f"Q: {result.question}\n\n" if result.intent else ""
        return f"{head}{result.message or ''}".rstrip()

    # The decision: a structured detail table (a plan), else a one-line headline.
    lines = [f"Q: {result.question}", "", result.detail or result.headline]

    if result.explanation:
        lines += ["", result.explanation]
    elif result.detail is None:
        # Degraded and no table → show the grounded facts + how to enable prose.
        lines += ["", "Facts:"]
        lines += [f"  {k.replace('_', ' ')}: {v}" for k, v in (result.facts or {}).items()]
        lines += ["", "(Start Ollama — `ollama serve` with the model pulled — for a written "
                  "explanation.)"]
    else:
        # A table is present (it's the exact data) but no prose.
        lines += ["", "(Start Ollama for a written summary.)"]
    return "\n".join(lines)
