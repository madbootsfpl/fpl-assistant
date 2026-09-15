# 192 — score a scoped term on the population it scopes to

ADR-190 found that a whole-board rank metric cannot evaluate a term applied to a sub-population, and closed
`SET_PIECE_WEIGHT` on it. This is that reasoning applied to ADR-188's clean-sheet term, which touches DEF/GK
only and was scored across all 626 players.

    venv/bin/python spikes/192-defender-only-calibration/measure.py

Deterministic — `decision_xp` is arithmetic, no solver and no sampling. See `result-2026-09-15.txt`.

**The hypothesis was refuted:** restricted to DEF/GK the term declines *more* steeply, not less. The value is
in having asked — a whole-board decline and a sub-population decline are different facts, and only one of them
was on the record before.
