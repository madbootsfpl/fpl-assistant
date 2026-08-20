# GW1 Data Hardening — the runbook

**GW1 = 2026-08-21.** The season-start modelling (form / set-piece / DefCon) is wired **dormant** (weights = 0), so
preseason xP is unchanged. This is the ordered checklist to turn it on **calibrated on real returns** (ADR-101) and
to verify the GW1-gated features. Nothing here changes a weight until the backtest says so — the harness
**recommends**, you **commit**.

> **🚨 T-1 (2026-08-20):** the **GW1 deadline is tomorrow, 2026-08-21**. Picks / manager-ID import unlock **at the
> deadline**; the backfill + returns in **§A need matches *played***, so §A runs **once the first results post**
> (not at the whistle). Nothing to flip today — this is the on-the-day checklist.
>
> Prep done (Sprint 138): the backfill (`history --backfill`), the form/set-piece/DefCon terms (dormant), the
> calibration harness (`analytics/backtest.py`), and the `calibrate` CLI all exist. GW1 is a **switch-flip**.
>
> **Dry-run verified 2026-08-13 (~8 days out):** ✅ `calibrate --weight form|set_piece|defcon` all run and gate
> correctly (*"Not enough gameweeks yet — have 0, need ≥4"*); ✅ `history --backfill [--limit N]` wired; ✅ `reseed`
> present; ✅ `config.FORM_WEIGHT`/`SET_PIECE_WEIGHT`/`DEFCON_MAGNIFIER_WEIGHT` all `0.0`; ✅ invariance + activation
> tests green (32). **What can only be checked once GW1 posts:** the gated features *lighting up* (a real manager-ID
> squad loads · momentum/price/community-signals show live movement) and a real `--backfill` fetch. **Timing:** the
> 21st is **§A** (backfill · reseed · verify features); the **weight flip is §B (~GW4–6)** once ≥4 GWs of returns
> exist — not the 21st.

---

## A. At GW1 (once the first gameweek's results have posted)

1. **Collect per-GW returns** — the form/backtest inputs:
   ```
   python app.py history --backfill        # throttled, resumable; --limit N to slice. Re-run each GW (idempotent).
   ```
2. **Refresh the snapshot** (so the app serves live data):
   - Local: `python app.py reseed` (refresh `fpl.db` → copy to `seed.db`), or the 🔄 button.
   - Cloud: `reseed` → `git push` → **Reboot app** (DEPLOY.md).
3. **Verify the GW1-gated features on live data** (they degrade gracefully preseason; confirm they light up):
   - **Manager import** — Squads sidebar → enter a real **FPL manager-ID** → your actual squad loads (picks are
     public from the GW1 deadline).
   - **Momentum / trending** — the Trending boards show real transfer/form movement (0 preseason).
   - **Price predictor** — the Players Pool shows 🔺/🔻 flags; My Squad shows the sell/hold nudge.
   - **Community signals** — the "Talked about" board works on the **live cloud IP** (may rate-limit → degrades to
     a note; that's expected).

## B. As returns accrue (~GW4–6) — calibrate, one weight at a time

Run the backtest, read the table, and **only if it clearly helps**, commit the value:

1. **Form first** (the main season signal):
   ```
   python app.py calibrate --weight form            # sweeps 0→0.5; prints ρ (rank) · MAE · hit@20 per value + a rec
   ```
   - Below ~4 GWs it says *"not enough gameweeks yet"* — wait and re-run.
   - If it recommends a value **and** the rank correlation (ρ) improves without worsening MAE / hit-rate:
     set `config.FORM_WEIGHT` to the recommended value, **update the one invariance test that relies on the config
     default being 0**, run the full suite + a real-DB smoke, and commit.
   - **The exact test to update at flip (verified 2026-08-13 dry-run)** — one per weight, all the same fix. It
     currently proves "config default ⇒ no change"; once the default *is* the new weight, add a
     `monkeypatch.setattr(config, "<WEIGHT>", 0.0)` so it still tests the **dormancy property**, not the default:
     - form → `tests/test_form.py::test_decision_xp_invariant_while_dormant`
     - set-piece → `tests/test_setpieces.py::test_decision_xp_invariant_while_set_piece_dormant`
     - defcon → `tests/test_defcon_xp.py::test_decision_xp_invariant_while_defcon_dormant`
     The `*_unchanged_when_*_weight_zero` tests (explicit weight 0) and the `*_activates_*` tests (they monkeypatch a
     weight > 0) **stay green as-is** — only the "default = dormant" test changes.
   - If the curve is flat / no clear signal → **leave it at 0** and re-run later.
2. **Then set-piece:** `python app.py calibrate --weight set_piece` → same decision → set `config.SET_PIECE_WEIGHT`.
3. **Then DefCon:** `python app.py calibrate --weight defcon` → set `config.DEFCON_MAGNIFIER_WEIGHT`.

**One weight at a time** (interpretable, not confounded, ADR-101). After each flip: `ruff check .` + `python -m
pytest -q` + a manual smoke that xP moved sensibly.

---

## Principles (ADR-101)

- **The harness recommends; you commit.** Weights stay 0 in the repo until a reviewed commit sets them.
- **Rank first.** It optimises **Spearman rank correlation** (predicted xP vs actual points) — the app *ranks*
  players. MAE + a top-N hit-rate are sanity checks; a value must not worsen them.
- **Walk-forward.** Each gameweek is predicted from data **before** it — never in-sample.
- **Don't chase noise.** Need ≥4 GWs; on a flat curve prefer the **smaller** weight; read the whole curve, not
  just the winner. It's a decision aid on a hobby-sized sample — **not** a significance claim.

## Also GW1+ (deferred, data-dependent)

Rolling 3-/6-GW form windows; DGW/BGW chip detection + momentum season features; elite-manager comparison. These
build on the same backfilled per-GW data once the season is underway.
