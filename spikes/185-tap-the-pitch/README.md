# Spike 185 — tap the pitch

Answers the questions ADR-108 deferred: can a tap on the pitch return a player id without dragging a
front-end build toolchain into a pure-Python project?

- `findings.md` — the verdict and what remains unverified
- `spike_app.py` — a runnable pitch you can actually tap

```
./venv/bin/python -m streamlit run spikes/185-tap-the-pitch/spike_app.py
```

Not production code. `st-click-detector` is installed in the venv for the spike but is **not** in
`requirements.txt` — adopting it is the ADR's decision, not the spike's.
