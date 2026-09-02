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

## B0. Pre-registered criteria — **written 2026-08-29, with 1 played gameweek and nothing to look at**

> Fixed **before** the data exists, which is the only time it can be fixed honestly. *"Only if it clearly
> helps"* is a standard you choose after seeing the curve; these are numbers you can fail against.
>
> If a rule below turns out to be wrong, **change it in a commit that says so and explains why** — amending a
> criterion is legitimate, amending it silently after seeing the result is not.

### The bar each weight must clear

A weight ships **only if all four hold**. Any one failing ⇒ leave it at **0**.

| # | Criterion | Why this number |
|---|---|---|
| 1 | **ρ improves by ≥ 1 standard error** of ρ at the eligible sample size (`SE ≈ 1/√(n−1)`; the harness prints `n`). At n≈400 that is **≈ +0.05**. | Below its own noise floor an improvement is indistinguishable from luck. Stated as a *formula*, not a fixed number, because `n` changes every gameweek. |
| 2 | **MAE worsens by ≤ 1%** against weight 0. | Rank is the objective (ADR-101), but a value that sharpens the order while making every projection worse is trading a metric we optimise for one we show. |
| 3 | **hit@20 does not fall at all.** | A count out of 20. There is no "small" drop in an integer that size — a fall means the top of the board got worse, which is the part anyone reads. |
| 4 | **The gain holds at ≥ 2 adjacent sweep values.** | One spike on a swept curve is the shape noise makes. A real effect is a *region*, not a point. |

**Choosing the value:** the **smallest** weight whose ρ is within 1 SE of the best. Ties go to the smaller
number — a weight is a claim about how much we trust a signal, and the smaller claim is the cheaper mistake.

### What we expect, recorded now so a surprise is legible

Writing the prediction down is what makes an odd result *informative* rather than just a number to accept. A
result far outside these is a reason to **check the harness before believing it**.

| weight | expectation | if it comes back very differently |
|---|---|---|
| `FORM_WEIGHT` | small positive, **≈ 0.05–0.20**. FPL's `form` is a 30-day mean — real signal, largely already inside `points_per_game`. | > 0.35 suggests the baseline rate is being under-used, not that form is magic. Inspect the tiers (ADR-028/124) first. |
| `SET_PIECE_WEIGHT` | small positive, driven almost entirely by **penalties**; corners/FKs near zero. | A large gain with pens excluded means the proxy is picking up "good attacker", not set-piece duty. |
| `DEFCON_MAGNIFIER_WEIGHT` | **genuinely unknown** — a new stat, one season of history. Coin-flip whether it clears the bar. | Any large effect deserves suspicion: check it is not just re-ranking defenders by minutes. |

### Stopping rule — so "re-run later" cannot become forever

- **GW4:** first honest attempt. Expect at least one weight to fail on sample size alone.
- **GW6:** the real sitting. Whatever clears the bar ships; whatever does not stays 0.
- **GW10:** last look. Anything still failing is **closed as not supported** and the config comment says so —
  not left as a permanent "revisit later", which is how a dormant weight becomes furniture.

Re-running a sweep after a fail is fine **once per checkpoint above**. Re-running until it passes is the same
mistake as choosing the criterion afterwards, spread over more weeks.

### Also in this sitting (same data, different check)

Not backtests — these are **constants measured once, on one gameweek**, and the question is whether the
population they were measured on was big enough to mean anything.

| constant | measured on | ships if |
|---|---|---|
| `EXODUS_PRESSURE` (p10) · `EXODUS_OWNERSHIP_FLOOR` | GW1, 199 players ≥1% owned (ADR-146/150) | re-measured on ≥4 GWs it moves **< 20%** → keep. **≥ 20%** → the original was noise; take the new value and say so. |
| captain-margin quartiles · concentration quartiles (ADR-143/145) | one gameweek | same 20% test. These gate *whether a message appears at all*, so a wrong quartile is a feature that fires on everyone or no one. |
| ADR-125 in-season xMins share | deliberately deferred to this sitting | `c ≈ GWs/(GWs+k)` reaches a share worth having only when it changes a projection by **> 0.5 xP for ≥ 20 players**. Below that it is churn. |
| Scout / Trending copy | — | ⚠️ **When any weight flips, `test_the_scout_shortlist_never_promises_points` fails by design** — the page says this value *is not in xP*, which stops being true. Rewrite the copy in the same commit as the flip. |

### ⚠️ Verified while writing this, not assumed

Two claims above are only worth making if the tripwires actually fire, so they were tested by flipping each
weight and watching:

* **`test_the_scout_shortlist_never_promises_points` fails at 0.1** — confirmed. Good: the Scout page says
  this value is not in xP, and that stops being true at the flip.
* **The set-piece dormancy test was blind below 0.2** — `weight × PENALTY_BONUS (0.3)` rounded away at 1dp, so
  at **0.05 / 0.10 / 0.15**, the exact range pre-registered above as *expected*, it stayed green while
  guarding nothing. **Fixed** (2026-08-29): it now asserts `config.SET_PIECE_WEIGHT == 0.0` directly, so it
  fails at any non-zero value. Form and DefCon were checked the same way and already fail at every value.

The general point, since it has now caught three things this month: **a tripwire you have not fired is a
tripwire you are assuming.**

### 🔬 Pre-flight — the harness was dry-run before its first real use (2026-09-02)

The owner asked to calibrate at **GW3, with 2 played gameweeks**. The answer was no — §B0's stopping rule
puts the first honest attempt at GW4, and *"only if it clearly helps"* is exactly the standard you choose
after seeing a curve. But the harness had **never produced output**: it has been guarded since ADR-101 built
it, so GW4 would have been its first run. Dry-running it found two faults, both fixed before there was a
result to be tempted by.

**1. ⚠️ Criterion 1 could not be applied — the harness did not print `n`.** The bar above says *"SE ≈
1/√(n−1); the harness prints `n`"*. It did not: `pairs` produced the triples and every consumer discarded the
count. The criterion depended on a number the tool never reported, so at the sitting it would have been
estimated or skipped. **Fixed** — each sweep row now carries `n` and `±1 SE`, and the CLI prints the bar
underneath the table so it is read off the output rather than from memory:

```
   weight   ρ (rank)     MAE  hit@20      n   ±1 SE
    0.000      0.657    1.25    0.20    626   0.040
  §B0 criterion 1: ρ must beat weight-0's 0.657 by ≥ 0.040 (1 SE at n=626)
```

`n` is the **per-gameweek** eligible count, not the pooled total — ρ is computed per gameweek and averaged,
so pooling would report ~G× too many and shrink the SE by √G, making a noise-level gain look like signal
against the one criterion written to prevent that. On an even number of gameweeks it takes the **lower**
middle, because understating `n` raises the bar, and erring toward rejecting a dormant weight is the cheaper
mistake.

**2. ⚠️ "Could not test" was printed as "tested and found nothing".** `sweep` returns an `insufficient` flag
and **nothing read it**. A run that evaluated zero folds printed an empty table under *"No clear signal yet —
leave the weight at 0"*. Today the CLI's own guard fires first so it never surfaced, but that is two guards
reading one constant, and they agree only until someone edits one. **Fixed** — the CLI reports *"Not enough
gameweeks… Nothing was evaluated"* and returns.

**The numbers from the dry run are discarded and are not recorded here**, deliberately: two gameweeks
calibrate nothing, and writing them down would be the first step toward remembering them at GW4.

> **The general point, and it is the same one this file already makes about tripwires:** an instrument you
> have never run is an instrument you are assuming. The cheapest time to find it broken is before you need
> its answer — because afterwards, every fix looks like it might be aimed at the result.

---

### The one rule that outranks the rest

**The harness recommends; a human commits.** Nothing here auto-applies. If every criterion passes and the
result still looks wrong, that is a valid reason not to ship it — and a reason to write down what looked
wrong, because it is usually the harness.

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
