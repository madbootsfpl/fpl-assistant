"""Console rendering for captain suggestions (ADR-029, ADR-089).

Pure formatting: takes the annotated picks (from `analytics.captain_picks`) + their grounded `Explanation`
and shows the structured **Captain Pick** card — the medal pick, its Confidence · Edge · Risk, the runner-up
Alternatives, and the shared Model note (US-277/278) — so the manager sees *why*.
"""

from .explain import MODEL_NOTE

_MEDALS = ("🥇", "🥈", "🥉")


def render_captain_pick(ranked, explanation, *, scope: str = "", team_names=None,
                        heading: str = "Captain Pick", nudge: str = "") -> str:
    """The structured **Captain Pick** card (ADR-089, US-277) — the mockup a tester asked for.

    A medal pick (`Team · Pos` · `Projected: N pts`), a clean Confidence line, the grounded Edge (✓) / Risk
    (⚠) from the `Explanation`, the runner-up **Alternatives** (🥈/🥉 + their xP), and the shared Model note.
    `ranked` is the `captain_picks` list already sliced so `[0]` is the chosen pick (its runner-ups are the
    alternatives); `team_names` maps a team short code → a friendly name ("MUN" → "Man Utd"). `heading`
    distinguishes a squad-scoped pick ("Captain Pick") from the global one ("Best Captain Picks", US-280);
    `nudge` is an optional guidance line (e.g. how to scope). Pure/empty-safe.
    """
    if not ranked:
        return "No captain candidates — run `refresh` first."
    top = ranked[0]
    team = (team_names or {}).get(top.get("team"), top.get("team") or "")
    lines = [heading]
    if scope:
        lines.append(scope)
    lines += [
        "",
        f"🥇 {top['web_name']}",
        f"{team} · {top.get('position') or ''}",
        f"Projected: {top['xp']:.1f} pts",
    ]
    if explanation is not None:
        lines += ["", f"Confidence: {explanation.confidence}/100 ({explanation.band})"]
        if explanation.reasons:
            lines += ["", "Edge", *[f"✓ {r}" for r in explanation.reasons]]   # MADBOOTS vocab (ADR-107)
        if explanation.risks:
            lines += ["", "Risk", *[f"⚠ {r}" for r in explanation.risks]]
    # ADR-144 — the margin, always, not only when it is narrow. The alternatives below already carry their
    # xP, so a manager *could* subtract; what they could not do is tell whether the answer is a lot. Against
    # the measured spread (p25 0.20 · median 0.60 · p75 1.00) most captain calls are close, and a medal
    # implies a confidence the gap often does not support.
    from src.analytics.captain import captain_margin, margin_line
    _margin = margin_line(captain_margin(ranked))
    if _margin:
        lines += ["", _margin]
    alternatives = ranked[1:]
    if alternatives:
        lines += ["", "Alternatives"]
        for i, a in enumerate(alternatives):
            pos = i + 2                                         # 🥈 2nd · 🥉 3rd · plain "N." beyond (US-278)
            marker = _MEDALS[pos - 1] if pos <= len(_MEDALS) else f"{pos}."
            lines.append(f"{marker} {a['web_name']} {a['xp']:.1f} pts")
    if nudge:
        lines += ["", nudge]
    lines += ["", MODEL_NOTE]
    return "\n".join(lines)


def render_captain_picks(picks, squad_name: str | None = None, explanation=None, team_names=None) -> str:
    """The captain recommendation as the structured Captain Pick card (US-278) — used by the CLI `captain`
    command and the web Captain tab, so every surface reads the same as the Ask answer. `picks` is the ranked
    `captain_picks` list (its runner-ups become the Alternatives); `explanation` the grounded
    Edge/Risk/Confidence; `team_names` maps a team short code → a friendly name. Empty-safe, scope-aware."""
    if not picks:
        base = "No captain candidates"
        if squad_name:
            return f"{base} in squad '{squad_name}' — check the name, or `refresh` first."
        return f"{base} — run `refresh` first (and `history --backfill` for baseline rates)."
    scope = f"from squad '{squad_name}'" if squad_name else "all players"
    return render_captain_pick(picks, explanation, scope=scope, team_names=team_names)
