# Sprint 190: Transfer advice must name the dead slot (ADR-136)

**Dates:** 2026-08-25
**Status:** ✅ Complete — ADR-136. 1294 → 1329 tests, ruff clean.

> **Owner:** reported it on 2026-08-19, promoted it off the Backlog, gated the design (*"build it as
> recommended"*). Also confirmed the ADR-120 Admin smoke is done and good, closing the last owner action.

---

### 🔍 Why this sprint exists

> *"Transfer advice says 'hold' on a squad with a dead player. RoboTS contains Destan (departed, 0 xP,
> benched). The gameweek plan correctly **flags** him — but the transfer line still reads 'no positive-gain
> upgrade — hold your transfer'."*

Reproduced on live data before a line was designed:

```
xi_aware=True   (the default, what every surface shows):  0 suggestions -> "hold"
xi_aware=False  (the --raw view):                         Destan (0.0) -> Thomas-Asante (7.4)  +7.4
```

`suggest_transfers` ranks by the swap's effect on the best legal **starting XI** (ADR-046). A dead player on
the bench is not in the best XI, so replacing him moves that number by exactly zero, `if gain > 0` drops the
move, and the advice falls through to "hold". **The ranking was right about what it measures.** The gap was
that XI xP is not the only thing a squad slot is for: a dead slot is a permanent zero *with no auto-sub
cover*, which costs nothing on paper and everything the week a starter is knocked.

---

### 🔱 The fork, and why the sprint stopped to ask

**94 of 610 players are unavailable, and `decision_xp` scores every one of them at 0.00.** It cannot do better
— `chance_of_playing_next_round` is 0 for all of them by definition, because *next round* is the only thing
that field knows. But they are not the same thing:

| what the news says | count | dead slot? |
|---|---:|---|
| `Has joined … permanently` / `on loan` / `has returned to …` | 39 | yes — permanent |
| `… - Unknown return date` | 47 | yes, in effect |
| `… - Expected back <D Mon>` | 7 | depends on the date |
| `Suspended until <D Mon>` | 1 | depends on the date |

Doku decided the design: £7.5m, calf, **back 5 Sep — about two gameweeks.** Selling a premium to fill a
two-week hole is worse advice than the "hold" being fixed. Minteh, three rows down, is back **28 Nov** —
functionally identical to a departure.

So the distinguishing signal exists in exactly one place: **FPL's free-text `news`.** `status`, `chance`,
`ep_next` and `decision_xp` all flatten these to the same value. Three options went to the owner (treat all 94
as dead / only count departures / parse the date and compare it to our fixtures); the gate picked the third.

---

### 🔧 What shipped

`src/analytics/dead_slot.py` turns a sentence into the number the advice actually wants: **how many of your
next N gameweeks he misses**, using the kickoff times already in `get_upcoming_fixtures`. `replace_dead` (in
`transfer.py`, beside the legality helpers it reuses) names the **highest-xP** legal affordable replacement.
`gameweek_plan` gained a separate `replacements` key — deliberately not folded into `transfer`, because its
`gain` answers a different question and a differently-meaning number in an existing field is how consumers
start lying. Four surfaces: CLI, `ask`, web ▸ Transfer (with a one-click Replace), and the Risk Monitor left
alone because it already lists the player.

**The control is the result worth quoting**, because the design is only worth having if it can tell these two
apart:

```
Destan (gone, misses 5/5) -> Thomas-Asante £5.0  +7.4 xP over 5 GWs
the same squad holding Doku (back 5 Sep) instead: no dead slot ✅ (held)
```

---

### 🐛 Two things the build found that the design had not

1. **The "hold" sentence lived in three places.** *"No positive-gain transfers — the squad may already be
   strong"*, printed **directly beneath** a dead-slot banner, is the reported bug wearing different words.
   Adding the new advice without silencing the old one would have shipped a page that argues with itself. A
   test now pins that the two lines cannot contradict each other.
2. **The `ask` verifier flagged our own recommendation.** `verify_grounding` (ADR-037) checks every name in
   the narration against a `subjects` list — owned players plus the transfer buy, but *not* a dead-slot
   replacement, who is by definition not owned. The first end-to-end run printed *"⚠ Unverified (names Walle
   Egeli)"* against a player the analytics had just chosen. **A false unverified is worse than none:** it
   teaches you to ignore the one warning that should be trusted.

Both are the same species this project keeps meeting — *a new path added correctly, while an old path that
assumed it didn't exist kept running beside it.*

---

### 💡 The lesson

`decision_xp` cannot be fixed to know this. The field it would need only knows about next round, so the
difference between a permanent exit and a two-week calf strain does not exist anywhere in the numeric model,
and no amount of modelling adds it. It exists only in a sentence a human wrote.

> **When the model genuinely cannot know something, the answer is sometimes to read the text and state your
> evidence — not to build a cleverer number.**

The reason string (*"gone"*, *"out until 28 Nov"*, *"no return date"*) is doing more work here than the xP
figure beside it. It is also what makes the advice **arguable**: a manager who wants to keep Minteh can see
exactly what we stood on and disagree. That is worth more than a confident number they cannot interrogate.

A smaller one worth keeping: **the failure direction was a design decision, not an implementation detail.** An
unparseable date resolves to *not dead*, so the advice stays as it is today. Missing a dead slot leaves the
manager where they already are; inventing one costs them a transfer. Every uncertainty here resolves toward
silence, and that is written into the module docstring so it survives the next edit.

### 🧪 Tests

**+35 (1294 → 1329.)** `tests/test_dead_slot.py` (23) covers the parse across all four *live* news shapes (not
invented ones), the December→January year boundary, blank gameweeks, a double-gameweek return between two
fixtures, and every verdict including "a doubtful player is never dead". `test_transfer.py` adds `replace_dead`
legality, best-not-cheapest, disjoint replacements for two dead slots, and the reported case as an explicit
before/after. `test_gameweek.py` pins the separate key and that *"hold your transfer"* is gone. An AppTest
drives the web block through a real squad built from live data.
