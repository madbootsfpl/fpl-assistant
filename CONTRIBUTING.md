# Contributing to MADBOOTS

Thanks for looking. Before anything else, the honest framing:

> **This project is slow on purpose, and the most valuable thing you can send is not code.**

Its stated priorities, in order, are **understanding · documentation · maintainability · functionality**. That
ordering is not decoration — it is why there are 194 decision records for 48,000 lines, and why several of the
best decisions here were to **not build something**.

---

## The single most useful contribution

**Use it, disagree with it, and tell us exactly where.**

Almost every substantial improvement in this codebase came from someone running their own FPL team, reading a
recommendation, and saying *"I wouldn't make that transfer."* A recent month's worth:

| what the report was | what it turned out to be |
|---|---|
| *"You're showing his score above mine but he's above me in the league"* | the model projecting a bench-boosted squad on 15 players against a rival's 11 |
| *"I'm 40 points ahead of your picks after four gameweeks"* | three structural gaps — no banking-to-afford, no fixture-run planning, non-playing forwards in builds |
| *"I have a cheap Arsenal fullback, clean sheets are probably >50%"* | the club's defensive record was displayed on one page and used by nothing |
| *"Not sure on Konsa — more likely a higher performer than a Fulham back"* | a player with **one career appearance** outprojecting one with **seven seasons**, by 9.3 points |

None of those came from reading the code. If you play FPL and the app tells you something that feels wrong,
**that is the contribution** — open an issue, say what it recommended, what you'd have done, and why. You do
not need to know how it works, and you do not need to be right. *"That's not a transfer I'd make"* is a
complete bug report here.

---

## If you do want to write code

### 1. The gate is real: no feature before its ADR

Every non-trivial change is agreed **before** it is built, and recorded in `docs/06_Decisions/` as an
Architecture Decision Record. A PR that arrives as a finished feature with no prior discussion will usually be
declined — not because it is bad, but because the decision is the artefact and it is missing.

Open an issue first. If we agree it is worth doing, the ADR gets written, and *then* the code.

### 2. Measure before you build, and be willing to lose

A design is verified on **real data** before it is committed to. Several features have been killed by half an
hour of measurement:

- a win-probability simulator — one player's week has a standard deviation of 3.51 points, so it would have
  reported *"it's close"* every week
- multi-gameweek transfer path search — greedy captures **96%** of the available gain, and **54%** of squads
  gain nothing at all
- a set-piece xP term — correct, and permanently unmeasurable: it reaches **9 of 657** players

⭐ **A measurement that kills a feature is worth more than the feature.** If yours does, write it up and it
ships as a decision. That is a successful contribution, and the file will say so.

### 3. Every guard gets mutation-tested

A test that cannot fail is worse than no test, because it reads as cover. So: after writing a guard, **break
the thing it guards and watch it go red.** This is not a formality — in the last month it caught a guard whose
fixture only ever exercised the lucky case, a guard that tested a component nothing called, and a guard that
passed while the code it protected had been deleted.

If a mutant survives, the test is wrong, not the mutant.

### 4. The three-part Definition of Done

1. **Automated tests** — and the mutation sweep above
2. **A manual smoke test** on real data
3. **Docs** — the ADR, and whichever of `docs/01_Journal`, `03_Architecture`, `04_Roadmap`, `06_Decisions`
   the change touches

`python -m pytest -q` and `python -m ruff check .` both green.

### 5. Comment *why*, not *what*

The comments in this codebase are unusually long and that is deliberate. They explain why something is the way
it is, what was tried and rejected, and what broke last time. If you find yourself writing `# increment i`,
delete it; if you are about to write `# this looked wrong but the obvious fix breaks X`, that is exactly what
belongs there.

---

## Getting it running

```bash
python -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/python app.py refresh        # pull FPL data into a local SQLite file
venv/bin/python -m src.web_streamlit  # → http://localhost:8501
venv/bin/python -m pytest -q          # the suite
```

The CLI is the engine (`python app.py --help`); the web app is a read-only view over the same analytics. If a
number differs between them, that is a bug worth reporting.

---

## Where to start reading

- **`docs/06_Decisions/ADR-000-index.md`** — every decision, one line each. This is the map; skim it rather
  than reading the ADRs in order.
- **`CLAUDE.md`** — the working rhythm in a page.
- **`docs/00_Project/PROJECT_STATUS.md`** — what is happening right now.
- **`docs/GW1_RUNBOOK.md` §B0** — how a model weight earns its way in: criteria pre-registered *before* the
  data exists, so a surprise is legible instead of convenient.

You do not need to read 194 ADRs. You do need to check whether the thing you are proposing has already been
decided — the index is searchable and several ideas have been declined twice.

---

## Things that will be declined

- A feature with no ADR and no measurement behind it
- A number presented to a user that the app does not itself use to decide
- Anything that claims a prediction the model cannot support — confidence here is a **heuristic, not a
  probability**, and it says so on screen
- AI or LLM claims in user-facing copy: the deployed app has no model attached, and a promise it cannot keep
  was removed once already
- Dependencies added for convenience

---

## Conduct, and the boring bits

Be decent. Assume the other person has read more of the context than you have, and say what you actually
measured.

By contributing you agree your work is licensed under the **AGPL-3.0** (see `LICENSE`), and that the **MADBOOTS
brand is not covered by it** (see `NOTICE`) — fork freely, but run it under your own name.

MADBOOTS is not affiliated with the Premier League or the official Fantasy Premier League game.
