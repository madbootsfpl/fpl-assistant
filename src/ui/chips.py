"""Console rendering for the chip-strategy advice (ADR-082).

A plain-text block — Triple Captain / Bench Boost / Free Hit / Wildcard — that is the exact advice the
analytics assembled (`chip_advisor`). It shows with or without the LLM (the prose is a bonus); the same
"the block is the truth" shape the other `ask` details use. Rendered in the CLI and, via `render_ask`, in the
web's Squads → Chips view.
"""


def _tc_line(tc) -> str:
    p = tc["player"]
    who = f"{p['web_name']} ({p['team']})" if p else "—"
    return f"GW{tc['gameweek']} — {who}, xP {tc['player_xp']} (the highest single-GW ceiling)"


def _bb_line(bb) -> str:
    return (f"GW{bb['gameweek']} — all 15 project {bb['squad_total']} xP "
            f"(the bench adds {bb['bench_points']})")


def _fh_line(fh) -> str:
    return f"GW{fh['gameweek']} — your best XI projects only {fh['xi_total']} xP (your weakest single week)"


def _wc_line(wc) -> str:
    a, b = wc["window"]
    span = f"GW{a}" if a == b else f"GW{a}–GW{b}"
    return f"{span} — your weakest stretch (avg XI {wc['avg_xi']} xP); reset before it"


def render_chip_advice(advice, squad_name, horizon: int = 8) -> str:
    """The chip advice as a readable block (ADR-082). `horizon` labels the window the advice looked over.

    Fixture-run + xP based — the closing note is honest about what sharpens in-season."""
    if not advice:
        return f"Chip strategy — squad '{squad_name}': no data yet (refresh, or add players)."
    window = f"next {horizon} GW" if horizon != 1 else "next GW"
    return "\n".join([
        f"Chip strategy — squad '{squad_name}' ({window})",
        "",
        f"  Triple Captain: {_tc_line(advice['triple_captain'])}",
        f"  Bench Boost:    {_bb_line(advice['bench_boost'])}",
        f"  Free Hit:       {_fh_line(advice['free_hit'])}",
        f"  Wildcard:       {_wc_line(advice['wildcard'])}",
        "",
        "  Note: based on your fixture run + projected points. Double/blank gameweeks and mini-league",
        "  position sharpen this in-season (live from GW1).",
    ])
