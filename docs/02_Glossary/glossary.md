# Glossary

Plain-English meanings of the terms used across the project. Keep definitions short and jargon-free.
For where an idea is *explained in depth*, see [Handbook Ch 19 — Glossary Index](../08_Handbook/19_Glossary_Index.md).

## General & tooling

| Term                | Plain English                                                 |
| ------------------- | ------------------------------------------------------------- |
| Sprint              | A short, fixed block of work with a clear goal.               |
| User Story          | A small feature described from the user's point of view.      |
| ADR                 | Architecture Decision Record — a note of a decision and why.  |
| Gate                | The step where we agree an approach (and write its ADR) *before* building it. |
| 3-part DoD          | Definition of Done: automated tests + a manual smoke test + updated docs. |
| CLI                 | Command-Line Interface — driving the app by typed commands.   |
| CI                  | Continuous Integration — GitHub Actions runs lint + tests on every push. |
| ruff / pytest       | The linter / the offline test runner.                         |
| Git                 | A system that records the history of your project.            |
| Repository          | The folder that contains your project and its history.        |
| Virtual Environment | A private Python installation for one project.                |

## Data & sources

| Term                | Plain English                                                 |
| ------------------- | ------------------------------------------------------------- |
| API                 | A way for one program to ask another program for information. |
| Endpoint            | A specific web address the FPL API answers requests on.       |
| bootstrap-static    | The main FPL API endpoint listing all players, teams, prices. |
| element-summary     | The FPL endpoint with a player's per-gameweek + past-season history. |
| JSON                | A structured text format for exchanging data.                 |
| SQLite              | A tiny database stored in a single local file.                |
| Upsert              | Insert a record, or update it if it already exists.           |
| Migration           | A small, safe change to the database's shape (a new column).  |
| ClubElo             | An external source of team strength (an Elo rating); best-effort, degrades gracefully. |
| selected_by         | A player's ownership — the % of managers who own them.        |

## Analytics

| Term                | Plain English                                                 |
| ------------------- | ------------------------------------------------------------- |
| FDR                 | Fixture Difficulty Rating — how hard a team's upcoming matches are (1–5). |
| xP (Expected Points)| A prediction of how many points a player scores over a horizon. |
| decision xP         | The **one** xP recipe shared by the optimiser and every recommendation (so they agree). |
| Baseline / fallback rate | A player's scoring rate from history; a shrunk "fallback" for players with little evidence. |
| xMins (expected minutes) | Expected playing time (chance% × a historical minutes share) — used to **weight** xP. |
| Points per £m       | Value — points earned per million of price.                   |
| xG / xA / xGI       | Expected goals / assists / goal involvement (xG + xA).        |
| xGC                 | Expected goals conceded — the clean-sheet / defensive-solidity signal. |
| Over/under-performance | Actual attacking points vs expected (xGI-based) — is a player running hot or cold? |
| DefCon              | Defensive Contribution — a defensive points source (tackles/interceptions etc.). |

## Optimisation

| Term                | Plain English                                                 |
| ------------------- | ------------------------------------------------------------- |
| ILP                 | Integer Linear Programming — the maths that picks the best legal squad (via PuLP). |
| Best legal XI       | The highest-scoring starting eleven that obeys the formation rules. |
| XI-gain             | How much a transfer lifts your **best legal XI** (the way `transfer` ranks swaps). |
| Archetype           | A squad-shape constraint — cheap / premium / differential.    |
| Differential        | A low-owned (≤5%) player — an off-template pick.               |
| Bench-aware         | Building to maximise the **starting XI**, weighting the bench low (`--weekly`). |
| Chip                | A one-off FPL boost — Wildcard, Free Hit, Bench Boost, Triple Captain. |

## Natural language

| Term                | Plain English                                                 |
| ------------------- | ------------------------------------------------------------- |
| `ask` / `chat`      | Asking a question in plain English (one-shot / a conversation). |
| Intent              | The *kind* of question — captain, transfer, fixtures, … — routed by keyword. |
| Grounding           | The rule that the model may only use the facts it's given — never compute or invent. |
| Grounding verification | An automatic check that every figure/name in the answer traces to the data (the ✓/⚠ trust line). |
| Follow-up           | A `chat` question that builds on the last turn ("why?", "and the second best?"). |
| LLM / Ollama        | The (optional, local) language model that **narrates** a decision the analytics made. |
