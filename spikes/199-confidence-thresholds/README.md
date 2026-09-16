# 199 — what is actually behind each confidence threshold

    venv/bin/python spikes/199-confidence-thresholds/measure.py

Provenance audit + measured distributions for the four *chosen* confidence constants. See
`result-2026-09-16.txt`.

⚠️ **Two of the four cannot be set from this run** — random squads have more headroom than real ones, so
transfer and rebuild gains are inflated (the same finding as spike 191). The file says which and why.
