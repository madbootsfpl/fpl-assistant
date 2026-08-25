# Architectural Decision Record: Squad Lab has two build modes, not three — and they were named backwards

**Decision ID:** ADR-137
**Date:** 2026-08-25
**Status:** ✅ **Accepted — built** (Sprint 191, 2026-08-25). **1329 → 1331 tests, ruff clean.** Owner-reported 2026-08-19, promoted from the Backlog
2026-08-25 with the intended shape written into the Roadmap entry. Measured on live data before building.
**Superseded By / Replaces:** A labelling correction to ADR-045 (the bench-aware objective) and ADR-062 (the
build-mode radio). **No optimiser change, no `decision_xp` change, no change to what any build produces.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, 2026-08-19:

> **Balanced** and **Bench Boost** both pass `bench_weight=None` and produce the **same squad**. And "Balanced"
> maps to the max-15 build — a *strong* bench — so the labels imply the opposite of what they do. This is a
> **correctness-of-labelling** issue, not a polish one.

Squad Lab offers three build modes. Measured on live data (£100m, 5-GW horizon, xP objective):

| radio option | `bench_weight` | 15-man xP | **XI xP** | bench spend | worst bench player |
|---|---|---:|---:|---:|---|
| **Balanced** | `None` | 303.7 | 231.7 | £23.5m | Thiaw, 17.2 xP |
| **Bench Boost** | `None` | 303.7 | 231.7 | £23.5m | Thiaw, 17.2 xP |
| **Strong XI (weaker bench)** | `0.1` | 289.2 | **238.9** | £19.0m | Walle Egeli, 4.9 xP |

**The first two rows are the same squad — the same fifteen player ids.** And it is worse than a wiring slip:
`select_squad` was also run with `bench_weight=1.0` (what "maximise all 15" would mean literally) and returned
**the same fifteen again**. Maximising `Σ score·start + 1.0·score·bench` *is* maximising `Σ score` over the 15.
**Bench Boost cannot be a distinct build**, however it is wired. There are two builds, and there only ever
could have been.

**And the two that exist are labelled backwards.** "Balanced" is the max-15 build — it spends £23.5m on a
bench where the *worst* player is worth 17.2 xP. That is the **strong-bench** build. The option labelled
"Strong XI (weaker bench)" is the one that behaves like a normal week's compromise. A user reading the radio
gets the opposite of the truth in both directions.

---

### ✅ Decision

**1. Two modes, named for what they build.**

| was | now | `bench_weight` |
|---|---|---|
| Balanced · Bench Boost | **All-round (strong bench)** | `None` |
| Strong XI (weaker bench) | **Strong XI (cheap bench)** | `0.1` |

"weaker bench" became "cheap bench" because *weak* was the misleading word: the £19.0m bench is not a worse
bench by accident, it is a deliberately cheaper one, bought so the money can go into the XI. Naming the
mechanism instead of the outcome is what makes the trade visible.

**2. Bench Boost is answered as copy, not offered as a build.** A caption under the radio says so plainly —
under the chip all 15 score, so *"maximise the XI"* and *"maximise all 15"* become the same question, and the
all-round build is already the answer. This is the **merge** branch of the two the Roadmap left open
(*"either merge Bench Boost or keep it as the chip-framing of the same build with a note"*), chosen because
the measurement above shows it is not a matter of wiring: a third option would be a lie the code cannot be
changed to tell the truth about.

**3. The default does not change.** Worth stating, because it was checked rather than assumed: max-15 is still
the default. The XI-first build is **+7.2 XI xP** over 5 gameweeks, which looks like a free win until you read
the bench it buys — one player on 4.9 xP, a near-dead slot of exactly the kind ADR-136 just taught the app to
warn about. That is a genuine trade, not an error, so it stays the user's call and the labels now describe it
honestly enough for them to make it.

**4. The CLI's `--bench-boost` keeps working and stops overclaiming.** Its help said *"Bench-aware build:
maximise all 15"*, which implies it changes the build; it never did — it adds the "all 15 score this week"
note to the output. The flag stays (removing it would break anyone's scripts, and the note is genuinely
useful); the help text now says what it does.

**Not in scope:** the optimiser, `WEEKLY_BENCH_WEIGHT`'s value (0.1 — a calibration question, not a naming
one), and `render_squad`'s `bench_boost` parameter, which the CLI still uses.

### ⚠️ Risks

- **A user with the old label in their head.** Small: the build behind "All-round" is byte-identical to what
  "Balanced" and "Bench Boost" both produced, so nobody's saved squad or workflow changes — only the words.
- **Losing the Bench Boost affordance.** A manager looking for it will not find a radio option. Mitigated by
  the caption naming the chip exactly where the question is asked, and by the Chips tab, which is where
  *when to play it* already lives.

### 🧪 Definition of Done

1. **Tests** — the radio offers exactly two options; both drive `select_squad` to a valid 15; the caption names
   Bench Boost; and a regression test asserting the two old modes really did produce one squad, so nobody
   re-adds the third.
2. **Manual smoke** — build both modes in Squad Lab; run the CLI with and without `--bench-boost`.
3. **Docs** — this ADR, the Roadmap entry, PROJECT_STATUS, the Feedback_Log row, a sprint retro.

---

### 🔨 Built — and one more contradiction it turned up

Both modes verified end to end on live data through the real page:

```
Build mode options: ['All-round (strong bench)', 'Strong XI (cheap bench)']
  All-round (strong bench)  -> Total: £100.0m · projected 303.7 xP
  Strong XI (cheap bench)   -> Total: £100.0m · projected 289.2 xP
```

**The smoke found a bug the design hadn't:** running `squad --full --bench-boost` printed

```
Bench Boost: all 15 score this week — your total is the whole squad's xP.
Note: Starters (11) is your XI — the bench won't score.
```

Both cannot be true, and a manager reading it has no way to know which to believe. **This is the same species
as the bug ADR-136 found the day before** — a new line added correctly while an older line that assumed it
didn't exist kept printing beside it. `render_squad` now suppresses the bench-won't-score notes under
`bench_boost`, with a test that the two can never both appear.

That is twice in two sprints. The pattern worth naming: **when you add a line that changes what an existing
line means, the existing line is part of the change.** Adding is never only adding.

### 🧪 Definition of Done — met

1. **Tests: +2 (1329 → 1331).** `test_a_full_weight_bench_cannot_build_a_different_squad_than_no_bench_weight`
   pins the algebra at the **optimiser** level on purpose — a UI test asserting "two options" can be edited
   away without anyone noticing why. It asserts on the objective **value**, not the id list, because tied
   optima make the solver's choice between them arbitrary. `test_the_bench_boost_note_does_not_argue_with_the
   _bench_wont_score_note` pins the contradiction fix, and the web test pins both the two options and that the
   chip question is still answered in the caption.
2. **Manual smoke:** both modes through the real Squad Lab page; CLI with, without, and `--weekly`.
3. **Docs:** this ADR, the Roadmap, PROJECT_STATUS, the Feedback_Log row, `docs/05_Sprints/Sprint191.md`.
