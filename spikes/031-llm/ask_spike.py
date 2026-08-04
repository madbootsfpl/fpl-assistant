#!/usr/bin/env python3
"""Spike (Sprint 031, ADR-033): grounded captain narration via local Ollama.

The point being tested: **analytics DECIDE, the LLM only NARRATES.** A planning probe
showed that asking the model to *recommend* makes it re-rank and fabricate a justification
(it picked Saka over B.Fernandes claiming a "higher xP" that the data contradicts). Here the
analytics (`captain_picks`) make the decision; the LLM is handed the *pre-made pick + only
its supporting facts* and told to explain it, never to rank/compare/compute/invent.

This is a SPIKE — throwaway, boxed here, not wired into `app.py`, not in `src/`. It reuses
the production analytics read-only.

    python spikes/031-llm/ask_spike.py "who should I captain from TS?"
"""

import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, ".")  # run from the repo root so `from src...` resolves

from src.analytics import baseline_rate, captain_picks, player_xp  # noqa: E402,F401
from src.squads import SquadStore  # noqa: E402
from src.storage import Storage  # noqa: E402

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


def _squad_from_question(q: str):
    """Crude intent parse for the spike: '... from <name>' → the squad name, else None."""
    words = q.replace("?", "").split()
    if "from" in words:
        i = words.index("from")
        return words[i + 1] if i + 1 < len(words) else None
    return None


def _analytics_decision(question: str):
    """Analytics make the decision: the top captain pick + its facts (never the LLM)."""
    store = Storage()
    try:
        players = store.get_players()
        upcoming = store.get_upcoming_fixtures()
        baselines = {c: baseline_rate(r) for c, r in store.get_history_by_code().items()}
        scope = "all players"
        name = _squad_from_question(question)
        if name:
            squad = SquadStore().load(name)
            if squad:
                ids = set(squad["player_ids"])
                players = [p for p in players if p["id"] in ids]
                scope = f"squad '{name}'"
        picks = captain_picks(players, upcoming, baseline_by_code=baselines, limit=3)
        return scope, picks
    finally:
        store.close()


def _facts(pick: dict) -> dict:
    """Only the chosen pick's facts, **pre-humanised** — the model must never decode
    abbreviations. (Spike finding: it read venue "A" as "home" and expanded "HUL" to the
    wrong club; passing "away against HUL" and forbidding expansion fixed both.)
    """
    venue = "home" if pick["venue"] == "H" else "away"
    return {
        "player": f"{pick['web_name']} ({pick['team']})",
        "expected_points_next_gameweek": pick["xp"],
        "fixture": f"{venue} against {pick['opponent']}",
        "is_penalty_taker": pick["penalty_taker"],
    }


def _prompt(facts: dict) -> str:
    return (
        "You are an FPL assistant. The captain has ALREADY been chosen by the analytics: "
        f"{facts['player']}. Using ONLY the facts below, explain in 2-3 short sentences why "
        "this is a good captain pick this gameweek.\n"
        "Rules: do NOT rank or compare players, do NOT compute or invent any number, do NOT expand "
        "or rename teams (use the codes exactly as written), state home/away exactly as given, and "
        "do NOT mention anything not in the facts.\n\n"
        f"FACTS:\n{json.dumps(facts, indent=2)}"
    )


def _narrate(prompt: str) -> str:
    body = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.2},
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))["response"].strip()
    except (urllib.error.URLError, TimeoutError) as exc:
        return f"[Ollama unavailable: {exc}. Is `ollama serve` running with '{MODEL}' pulled?]"


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "who should I captain from TS?"
    scope, picks = _analytics_decision(question)
    if not picks:
        print("No captain candidates (run `refresh`; check the squad name).")
        return
    pick = picks[0]  # the ANALYTICS decision — #1 by xP
    print(f"Q: {question}")
    print(f"Analytics pick ({scope}): {pick['web_name']}  "
          f"[xP {pick['xp']} vs {pick['opponent']} {pick['venue']}"
          f"{', penalty taker' if pick['penalty_taker'] else ''}]")
    print("\nExplanation (llama3.2, grounded — narrates the decision, does not make it):")
    print(_narrate(_prompt(_facts(pick))))


if __name__ == "__main__":
    main()
