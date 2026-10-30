# ADR-376 — Not on a number we know is biased

**Decision ID:** ADR-376
**Date:** 2026-10-30
**Status:** ✅ **Accepted and built.** The transfer engine no longer advises selling a DEF/GK when the
defence it fails to price fully explains the move. **xP is unchanged** — this is a flag, not a correction.
**Superseded By / Replaces:** The fast half of [ADR-375](./ADR-375-the-defence-he-played-behind.md), shipped
without waiting for it. Follows [ADR-138](./ADR-138-value-frontier.md)'s *flag, not a correction* pattern.
Narrows [ADR-218](./ADR-218-read-the-board-instead-of-rebuilding-it.md)'s read optimisation, deliberately.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 The complaint, and why it is not a modelling problem

Testers who own Konsa were being advised to sell him. The owner's framing is the decision:

> *"that's not a runner, it's one giant exposure to our credibility."*

He is **DEF #50 of 217** on xP while his Arsenal teammate **Gabriel is #3** — same back line, same clean
sheets — because Konsa's rate was earned at Aston Villa and `CLEAN_SHEET_WEIGHT` is **0**, so no clean-sheet
term is priced at all. The community disagrees loudly: **127,475 in against 4,869 out at GW9, a 26:1 ratio**.

ADR-375 proposes the model fix and it needs a gate, a backtest and a sprint. ⭐⭐ **THE DAMAGE IS NOT THE
WRONG NUMBER — IT IS ACTING ON A NUMBER WE ALREADY KNOW IS BIASED.** That part needs no gate, because the
honest response to a number you distrust is to stop giving advice on it.

⭐ The precedent is in the codebase. [ADR-138](./ADR-138-value-frontier.md)'s `yet_to_play`: *"This is a flag,
not a correction: it does not touch xP. It exists so a surface can say what the number is standing on."*

---

### 🎯 What it does

`unpriced_defence` returns the points per match a DEF/GK's xP understates him by, from the defence he plays
behind now versus the one his historical rate was earned behind — both measured **against their own era's
league average**, so a player whose old club was league-average gets **zero** and the guard is invisible to
him. `suggest_transfers(sell_doubt=…)` then withholds a move when the doubt covers the gain.

🔴 **`CLEAN_SHEET_WEIGHT` is 0, so the figure is the WHOLE era-relative delta, not the difference between
two baselines.** `decision_xp` prices no clean-sheet term whatsoever; all of it is missing.

| player | unpriced defence |
|---|---|
| **Konsa** (moved from a 0.235 defence to 0.625) | **+1.44 /match** |
| Gabriel (already behind it) | +0.47 |
| White (already behind it) | +0.39 |
| Milenković (Forest's defence is worse) | **0.00** — clamped |
| Haaland (outfield) | 0.00 |

96 of 669 players carry a positive figure.

### ⭐⭐ Three properties that make an ungated number safe to act on

1. **One-sided.** It clamps at zero, so it can only ever *remove* a sale, never argue anyone up and never
   penalise. ⭐ *An ungated correction is safe to act on only where being wrong about it costs nothing, and
   declining to give advice is that place.*
2. **Netted against the incoming player.** ⚠️⚠️ Crediting the outgoing defender and not his replacement
   would compare a corrected player against an uncorrected one and **freeze every defender sale** — ⭐ *a
   one-sided correction applied to one side of a comparison is a thumb on the scale, not a guard.*
3. **A test, not a blanket.** It withholds what the bias explains and nothing more. Verified end to end on
   the real board: at a 1-GW horizon the Konsa → Affengruber move **still stands** (gain 1.9 against doubt
   1.44 — even crediting him in full, Affengruber is better this week); at the app's default 5-GW horizon it
   is **withheld**.

It threads through `suggest_transfer_plan` for the reason `reported_out` does: ⭐ *a sale we decline to advise
on move 1 is one we decline to advise on move 3, or the guard is bypassed by asking for two.*

---

### ⚠️ Where it lives, and a cost decision taken on measurement

In the **shared layer** (`service/inputs.py`), for the reason `reported_leavers` gives there: *ADR-151→156 is
the record of one fact being re-taught to six surfaces one at a time, every gap found by the owner using the
product.* Wired into the service (the app) and the CLI; `ask`, Streamlit and the gameweek plan default to
`sell_doubt=None`, which is **exactly today's behaviour**.

🔴 **It cost an optimisation, and the boundary moved to where the cost actually is.** ADR-218 made the
transfer endpoint rank on the published board, with a test asserting the saving because *"a version that
reads the board and loads the history anyway passes every other test in this file."* The guard needs
historical rows, so:

| | size | grows? |
|---|---|---|
| past-season history | **186 KB** | no — flat all season |
| per-gameweek history | 359 KB at GW8 | **yes, ~45 KB/week → ~1.7 MB by May** |
| fixtures | 380 rows / 2 ms | no |

⭐⭐ **Clean-sheet rates come out of the SCORELINES, identically.** `team_cs_from_fixtures` agrees with
`gw_form.team_clean_sheet_rate`'s goalkeeper proxy club by club (ARS 0.625/0.625, CHE 0.125/0.125, …) — so
the per-gameweek read was dropped entirely. ⭐ *When two derivations of the same number agree, keep the one
whose cost is flat.* The test now forbids `get_gw_history_by_code` and permits the flat 186 KB, with the
numbers in its docstring. ⚠️ *ADR-218's quoted "1.9 MB" was end-of-season sizing, which is why it read as
8× today's actual cost.*

---

### 🧪 Definition of Done

**1 — Automated tests.** 20 new (14 in `test_cleansheet.py`, 6 in `test_transfer.py`). **9 deliberate
defects, every one caught:** league baseline not position-matched · unweighted instead of start-weighted ·
unknown edge reading 0.0 instead of None · doubt no longer one-sided · personal edge dropped · any played
match counting as a clean sheet · doubt not netted · doubt not scaled by the window · guard never withholds.

⚠️ **Two process notes, both mine.** My first six transfer tests **all failed**, including one I had read as
passing — a one-defender squad cannot form a legal XI, so the XI-aware path returns nothing and the tests
were asserting against the wrong mechanism; they now use `xi_aware=False` to isolate the guard. And the
mutation harness reported one mutant as "no summary", which was an `IndentationError` my own `perl` had
introduced — ⭐⭐ *an invalid mutant looks exactly like an uncaught one unless the harness prints what it
applied and what came back.* Same harness, same lesson as ADR-372.

**2 — Manual smoke test.** `python -m src.cli transfer --squad TS` renders; the guard verified against a
synthetic Konsa squad on the live GW8 board at both horizons.

**3 — Docs.** This ADR, ADR-375, ADR-218's test rationale, index, PROJECT_STATUS.

---

### 📊 Consequences

**Good:** the credibility exposure closes this week rather than after a gate. The guard is reversible by one
argument, touches no xP, and is off by default for every surface not opted in.

**Costs / limits:**
- ⚠️ **It acts on an ungated number.** The three properties above are what make that defensible; if ADR-375
  declines, this guard's premise weakens and it should be re-argued rather than quietly kept.
- ⚠️ **Silent.** A withheld move simply does not appear. The player's `defence_unpriced` is not yet surfaced,
  so nothing *tells* the reader why — ⭐ and ADR-138's pattern is a flag that **says** something. This is half
  of it.
- ⚠️ `ask`, Streamlit and the gameweek plan are **not** wired, so the chat and web can still advise a sale the
  app withholds. ⚠️ *Inconsistency between surfaces is its own credibility risk*, and ADR-151→156 is the
  record of exactly that being fixed six times.
- ⚠️ 64% of DEF/GK have a personal baseline; the rest behave as today.

---

### 🔗 Links

- [ADR-375](./ADR-375-the-defence-he-played-behind.md) — the model fix, gated
- [ADR-138](./ADR-138-value-frontier.md) — *a flag, not a correction*
- [ADR-218](./ADR-218-read-the-board-instead-of-rebuilding-it.md) — the optimisation narrowed here
- [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md) — where Konsa was first raised
