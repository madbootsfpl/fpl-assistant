# 200 — a squad population that is not random

`population.py` is **importable** — three measurements were blocked on the same missing thing
(ADR-191 §2, and both thresholds ADR-199 gated), so it is a module rather than a script.

    venv/bin/python spikes/200-realistic-squads/measure.py

* `optimal()`   — the optimiser's 15. The ceiling; nobody's real squad.
* `template()`  — the most-owned squad the money buys. The closest definable proxy to a median manager,
                  and the only population here that is *observed* rather than constructed.
* `perturbed()` — k legal swaps. The quality dial.
* `ladder()`    — the dial as a dict, one optimiser solve and cheap perturbation after.

⚠️ **Perturb the template, not the optimum, when you need real-squad behaviour.** Same XI xP, different
improvability — see `result-2026-09-16.txt`.
