# Architectural Decision Record: Transfer advice must name the dead slot

**Decision ID:** ADR-136
**Date:** 2026-08-25
**Status:** ✅ **Accepted — owner-gated ("build it as recommended"), built** (Sprint 190, 2026-08-25).
Owner-reported 2026-08-19, promoted from the Backlog 2026-08-25, reproduced on live data before the design was
written (below), built the same day. **1294 → 1329 tests, ruff clean.**
**Superseded By / Replaces:** Fixes a blind spot in ADR-046 (`xi_aware` ranking) without changing it. Pairs
with US-421 (the ⛔ flag) and ADR-130 (the Risk Monitor), which already *show* the player — this makes the
**action** explicit. **No `decision_xp` change** (ADR-041 untouched).
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner's report, 2026-08-19:

> Transfer advice says *"hold"* on a squad with a dead player. RoboTS contains Destan (departed, 0 xP,
> benched). The gameweek plan correctly **flags** him — but the transfer line still reads *"no positive-gain
> upgrade — hold your transfer"*.

**Reproduced on live data (2026-08-25), and the mechanism is exactly as reported.** A 15 holding Destan
(status `u`, *"Has joined Konyaspor permanently"*, 0.00 xP over 5 GWs) on the bench:

```
--- xi_aware=True  (the default, and what every surface shows):  0 suggestions
--- xi_aware=False (the --raw view):                             1 suggestion
      Destan (0.0) -> Thomas-Asante (7.4)   gain +7.4  (BENCH)
```

`suggest_transfers` ranks by the swap's effect on the best legal **starting XI** (ADR-046). A dead player on
the bench is not in the best XI, so replacing him moves that number by **exactly zero**, the move is filtered
out by `if gain > 0`, and the advice falls through to "hold". The ranking is doing precisely what ADR-046
asked of it. The gap is that **XI xP is not the only thing a squad slot is for.**

A dead slot is a permanent zero *with no bench cover*. When a starter is rotated or knocked, FPL auto-subs
from the bench — and a departed player cannot come on. So the slot costs you nothing on the sheet and
everything on the day it matters. That cost is invisible to an XI-gain ranking by construction.

**The size of it, measured on the live market** — best same-position replacement at the same price or cheaper:

| dead player | | best replacement | over 5 GWs |
|---|---|---|---|
| Spence £4.5 DEF (joined Inter) | → | Mitchell £4.5 | **16.9 xP** |
| Doku £7.5 MID (calf, back 5 Sep) | → | Rice £7.5 | **20.9 xP** |
| Burn £5.0 DEF (ankle, back 14 Sep) | → | Thiaw £5.0 | **17.2 xP** |
| Yates £4.5 MID (unknown return) | → | Slater £4.5 | **7.5 xP** |

The app currently calls every one of these "hold".

---

### 🔱 The fork this ADR exists to settle: what counts as *dead*?

This is the whole design, and it is not obvious. **94 of 610 players are currently unavailable**, and
`decision_xp` scores **all 94 at 0.00 xP** — it cannot separate them, because `chance_of_playing_next_round`
is 0 for all of them by definition. *Next round* is the only thing that field knows.

But they are not the same thing at all:

| what the news says | count | is it a dead slot? |
|---|---:|---|
| `Has joined … permanently` / `on loan` / `has returned to …` | **39** | **Yes — permanent.** Never plays again this season. |
| `… - Unknown return date` | **47** | **Yes, in effect.** There is no date to wait for. |
| `… - Expected back <D Mon>` | **7** | **It depends on the date.** |
| `Suspended until <D Mon>` | **1** | Depends on the date. |

Doku is the case that decides the design: **£7.5m, calf, expected back 5 Sep — about two gameweeks.** Selling
a premium to fill a two-week hole with a £7.5m body you then have to transfer back out is bad advice, and an
engine that cannot tell him from Destan will give it. Minteh, three rows down, is *"back 28 Nov"* — over three
months, and functionally identical to a permanent exit.

**So the distinguishing signal exists in exactly one place: the news string.** Nowhere else. `status`,
`chance`, `ep_next` and `decision_xp` all flatten these to the same value.

**Options considered:**

- **(a) Treat every unavailable player as a dead slot.** Simplest, no parsing. Rejected: it tells you to sell
  Doku for a two-week absence, which is worse advice than the "hold" we are fixing.
- **(b) Only `u` (departed) counts.** Unambiguous and permanent — 39 players, zero parsing, zero risk of a
  wrong call. Rejected as *too* narrow: it misses the 47 unknown-return injuries, which are the larger group
  and are genuinely dead. It would fix the reported case and leave most of the problem.
- **(c) ✅ RECOMMENDED — parse the return date, and compare it to the fixtures we already hold.** The format
  is stable and covers **8/8** of the dated cases today (`Expected back 5 Sep`, `Suspended until 19 Sep` —
  both `<D Mon>`). Then convert it into the number the advice actually wants: **how many of your next N
  gameweeks he misses**, using the kickoff times already in `get_upcoming_fixtures` (ADR-123's work). He is a
  dead slot when he misses **the whole horizon**. Doku misses ~2 of 5 → hold, and we can say why. Minteh
  misses 5 of 5 → sell. Destan has no date at all → sell.

**Failure direction is chosen deliberately.** If the news has a date we cannot parse, the player is treated as
**not dead** (advice reverts to today's "hold"). A parse failure must never manufacture a sell recommendation.
Missing a dead slot leaves the manager where they are now; inventing one costs them a transfer.

---

### ✅ Decision

**1. A new pure module `src/analytics/dead_slot.py`.** Small, no I/O, Row/dict safe, in the house style.

```
return_date(player, *, today)          -> date | None      # parsed from news; None when there is no date
gameweeks_missed(player, upcoming, *, today) -> int | None # how many of the upcoming GWs he misses; None = all
dead_slots(owned, upcoming, *, today)  -> list[dict]       # {player, reason, until, gws_missed}
```

`reason` is the honest word for *why*, so the surfaces can say it: `"gone"` (left the club/league),
`"no return date"`, `"out until <date>"`. Naming the reason is most of the value — *"Spence has joined Inter"*
is a different sentence from *"Spence is a low-xP defender"*, and only one of them makes a manager act.

**2. `replace_dead(owned, players, xp_by_id, upcoming, *, bench_ids, bank, max_per_club, today)`** in the same
module. One suggestion per dead slot: the **highest-xP** legal, affordable, available, same-position
replacement. Not "the cheapest playing body" — the owner's *"any ~£4.5m body is pure upside"* describes the
floor, not the target; if the best affordable replacement is Mitchell at 16.9 xP, that is the one to name.
Same legality rules as `suggest_transfers` (`_club_ok`, budget, not-owned, available) — reused, not restated.

**3. `gameweek_plan` gains a separate `replacements` key. It does NOT overload `transfer`.** The `gain` on a
dead-slot move means something different — *"this fills a slot that cannot score"*, not *"this lifts your XI
by X"* — and quietly putting a differently-meaning number into an existing field is how consumers start lying.
A new key makes every surface opt in deliberately.

**4. Where a dead slot exists, it leads.** The surfaces put the replacement **above** any xP upgrade and label
it as the different thing it is. The xP upgrade still shows as the alternative: you have one free transfer and
the manager makes the call, but they should make it knowing the slot is dead.

**Surfaces to update:** `ask.py` (the `transfer:` line that currently says *"none — no positive-gain
upgrade"*), `src/ui/transfer.py` (CLI), and My Squad ▸ Transfer in the web app. The Risk Monitor (ADR-130)
already lists the player and needs no change.

**Explicitly not in scope:** any change to `decision_xp` or to `suggest_transfers`' ranking. ADR-046 is right
about what it measures; this adds a second question rather than corrupting the first.

---

### ⚠️ Risks

- **The news format is FPL's free text and could change.** Mitigated by the failure direction (unparsed → not
  dead → today's behaviour) and by a test on the four real shapes seen in the live data.
- **Year inference.** *"5 Sep"* carries no year, and the season spans Aug→May. A month earlier than today's
  rolls to next year. Needs a test at the December/January boundary, which is where it breaks if anywhere.
- **Advising a sell on a player who returns just after the horizon.** A 5-GW horizon calls "back in GW6" dead.
  Real, and accepted: the reason string carries the date, so the manager sees *"out until 28 Nov"* and can
  disagree. The advice states its evidence rather than hiding it.

### 🧪 Definition of Done

1. **Tests** — unit tests for the parse (all four live news shapes + the year boundary + garbage), for
   `gameweeks_missed` against real fixture kickoffs, for `dead_slots` (Destan yes, Doku no, Minteh yes), for
   `replace_dead` legality, and the reported case end-to-end through `gameweek_plan`.
2. **Manual smoke** — the squad from the reproduction above: the advice must name Destan and stop saying hold.
3. **Docs** — this ADR, the Roadmap entry, PROJECT_STATUS, the Feedback_Log row closed, and a sprint retro.

---

### 🔨 What was built, and the one place it deviates from the design above

**`src/analytics/dead_slot.py`** — `return_date` · `gameweeks_missed` · `dead_slots`, exactly as specced.

**`replace_dead` went into `transfer.py`, not `dead_slot.py`.** The only deviation, and it is a better split:
`dead_slot.py` owns *what is dead* (the parse, the horizon arithmetic) and `transfer.py` owns *which
replacement* — where the legality helpers (`_club_ok`, `_summary`, `is_unavailable`) already live and are
reused rather than exported. A module-private helper crossing a module boundary is a smell; this avoids it.

**Verified on live data at every step.** The reproduction, the population split, and the outcome:

```
BEFORE — suggest_transfers (xi_aware, the default): 0 suggestions -> "hold"
AFTER  — replace_dead:
   Destan (gone, misses 5/5) -> Thomas-Asante £5.0  +7.4 xP over 5 GWs
CONTROL — the same squad holding Doku (back 5 Sep) instead: no dead slot (held) ✅
```

The control is the one that matters: the design is only worth having if it can tell those two apart, and it
can. Against the six most-owned unavailable players, `dead_slots` holds Doku (1/5), Burn (2/5) and a
suspension (3/5), and flags Destan (gone), Minteh (out until 28 Nov) and Saliba (no return date).

**Surfaces, all four:**
- **CLI `transfer`** — a banner above the table (`render_dead_slots`), silent when the 15 are whole.
- **`ask` / "this week"** — a `Replace:` line above `Transfer:`, and `dead_slots_to_replace` in the facts.
- **Web ▸ My Squad ▸ Transfer** — an `st.error` naming the reason, with a one-click **Replace** button.
- **The Risk Monitor (ADR-130)** already lists the player and was left alone.

### 🐛 Two things the build found that the design had not

1. **The "hold" sentence had to be fixed in three places, not one.** *"No positive-gain transfers — the squad
   may already be strong"* printed **directly beneath** a dead-slot warning is the reported bug wearing
   different words. `render_transfers`, `render_transfer_plan` and `_transfer_line` all take a `has_dead` flag
   now, and a test pins that the two lines cannot contradict each other. Adding the new advice without
   silencing the old one would have shipped a page that argues with itself.
2. **The `ask` verifier flagged our own recommendation.** `verify_grounding` (ADR-037) checks that every name
   in the narration traces to the facts, via a `subjects` list — which included owned players and the transfer
   buy, but not a dead-slot replacement, who is by definition **not** owned. The first end-to-end run printed
   *"⚠ Unverified in the explanation (names Walle Egeli)"* against a player the analytics had just chosen. A
   false unverified is worse than none: it teaches you to ignore the one warning that should be trusted.

### 💡 What this ADR is really about

`decision_xp` scores all 94 unavailable players at 0.00 and **cannot** be fixed to do better — the field it
would need (`chance_of_playing_next_round`) only knows about next round. So the distinction between a
permanent exit and a two-week calf strain does not exist anywhere in the numeric model, and no amount of
modelling adds it. It exists only in a sentence a human wrote.

That is the lesson worth keeping: **when the model genuinely cannot know something, the answer is sometimes to
read the text and state your evidence, not to build a cleverer number.** The reason string (*"gone"*, *"out
until 28 Nov"*, *"no return date"*) is doing more work here than the xP figure beside it — and it is what makes
the advice arguable, which is what a manager needs from it.

### 🧪 Definition of Done — met

1. **Tests: +35 (1294 → 1329).** `tests/test_dead_slot.py` (23) covers the parse on all four live news shapes,
   the December→January year boundary, blank gameweeks, a DGW return between two fixtures, and each verdict.
   `test_transfer.py` covers `replace_dead` legality, best-not-cheapest, disjoint replacements for two dead
   slots, and the reported case as an explicit before/after. `test_gameweek.py` pins the separate key and that
   "hold your transfer" is gone. An AppTest drives the web block through a real squad.
2. **Manual smoke: done** on the CLI, on `ask`, and on a real saved squad holding Destan.
3. **Docs:** this ADR, the Roadmap, PROJECT_STATUS, the Feedback_Log row closed, `docs/05_Sprints/Sprint190.md`.
