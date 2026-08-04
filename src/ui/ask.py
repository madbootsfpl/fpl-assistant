"""Console rendering for the `ask` command (ADR-034).

Shows the analytics decision (always), then the LLM's explanation — or, when the model is
unavailable, the facts themselves + a note. The point: `ask` is useful with or without the LLM.
"""


def render_ask(result) -> str:
    # Unrecognised question, or an empty result — just the message.
    if result.message and result.headline is None:
        head = f"Q: {result.question}\n\n" if result.intent else ""
        return f"{head}{result.message}"

    lines = [f"Q: {result.question}", "", result.headline]
    if result.explanation:
        lines += ["", result.explanation]
    else:
        # Degraded: the LLM is unavailable — show the grounded facts + how to enable prose.
        lines += ["", "Facts:"]
        lines += [f"  {k.replace('_', ' ')}: {v}" for k, v in (result.facts or {}).items()]
        lines += ["", "(Start Ollama — `ollama serve` with the model pulled — for a written "
                  "explanation.)"]
    return "\n".join(lines)
