# FPL Assistant

[![CI](https://github.com/tesheridan/fpl-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/tesheridan/fpl-assistant/actions/workflows/ci.yml)

A personal Fantasy Premier League analytics assistant — a command-line tool you can also **talk to**.

**Status:** Phases 1 (*CLI Analytics MVP*), 3 (*decision support* — captain · transfer · squad analysis)
and 4 (*natural language* — a grounded `ask` + a conversational `chat`) **complete**. A **read-only web UI**
(Streamlit, deployable to Streamlit Community Cloud) is live, and **Phase 6 — Crowd & Community Signals**
(ownership / transfer trends · an FPL news lens · import-your-team-by-manager-ID · Reddit buzz) is
delivering — plus a grounded **"this week" gameweek recommendation** (captain · lineup · a transfer · flags).
**89 ADRs · 707 tests · CI green.** New here? See the **[Product overview](docs/00_Project/PRODUCT.md)**
(features · what's gated until GW1 · backlog · roadmap) and **[Direction & options](docs/00_Project/DIRECTION.md)**
(hobby vs multi-user/paid · mobile · wider testing). Running a beta? **[BETA.md](docs/BETA.md)**. Also the
[Roadmap](docs/04_Roadmap/Roadmap.md).

## What it does today

**Analytics**
- Rank players by points / value (Points per £m) and **Expected Points (xP)** over a fixture
  horizon — now with a **per-gameweek breakdown** (`--by-gameweek`)
- Expected goals (xG / xA / xGI / xGC), over/under-performance, Defensive Contribution, clean sheets
- Custom fixture difficulty (overall + ClubElo Elo)
- **Past-season history** (a throttled backfill) feeding a multi-season xP baseline

**Optimisation**
- Pick an optimal XI or full 15-man squad (ILP), with formations, bench, and availability handling
- Save and reload your own squad (re-priced, with current injuries + departures)

**Decision support (Phase 3)** — recommend *and explain*, composed on the above:
- **`captain`** — a structured **Captain Pick** card for the next GW (by xP): the 🥇 pick (Team · Pos ·
  Projected pts) · a Confidence · **Why**/**Risks** · 🥈🥉 **Alternatives** · a **Model note** (data-driven; AI
  explains)
- **`transfer`** — the best single legal transfers for your squad (≤3/club, budget), ranked by **XI
  improvement** (how much a swap lifts your best legal XI, so bench-fodder upgrades don't top the list);
  `--raw` for the old raw-xP-gain ranking
- **`analyse`** — a saved squad's health over N GWs (projected XI xP, weak links, injuries), cross-linked
- **Expected minutes (xMins v0)** — every recommendation **weights xP by expected playing time**
  (`chance_of_playing%` × a historical minutes share), so rotation risks don't out-rank nailed-on
  starters. Shown as expected minutes; use `--no-xmins` for the raw "assumes 90" number.

**Natural language (Phase 4)** — grounded, and optional:
- **`ask "..."`** — ask a question in plain English (captain / transfer / squad health / start-bench /
  compare / **build a squad** / **best players in a position** / **fixtures & difficulty**). The
  **analytics decide**; a **local LLM (Ollama) only narrates** — and every answer is **checked
  against the data** (a ✓/⚠ trust line: figures and names are verified, not just instructed). `ask`
  works without the LLM (it falls back to the decision + facts). With a squad loaded, squad questions
  (*"who should I captain?"*) **scope to your team by default**; say *"from all players"* for the global
  best picks (ADR-090).
- **`chat`** — an interactive `ask` where **follow-ups build on the last answer**: "who should I
  captain from TS?" → **"why?"** → **"and the second best?"** → **"what about defenders?"**. Same
  discipline (analytics decide, every turn verified); the only new thing is memory of the last turn.
  The last turn is **remembered across runs** (ADR-091), so a follow-up works even as a separate `ask`
  command; `ask --forget` (or asking *"forget"*) clears it. It also explains **FPL rules** from a curated,
  verified knowledge base (21 topics — scoring, chips, transfers, flags, leagues, price changes, …).

**Crowd & community signals (Phase 6)** — a *complementary lens*, never folded into xP:
- **Trends** — most-owned · most transferred in/out · in-form boards (free FPL crowd data), crowd **flags**
  (🟦 template · 💎 differential · 💰 price · 🔥 trending · 📈 form) across the player/squad views, and a
  **"trends"** `ask` intent. *(Ownership works now; momentum/form light up at GW1, 2026-08-21.)*
- **News** — official FPL player news (injuries · doubts · returns), most serious first.
- **Import your team by manager-ID** — pull your real FPL squad from the public entry API (picks from GW1).
- **Community Signals** — who r/FantasyPL is talking about right now, from the public Reddit **RSS** feed
  (mention *buzz*, not sentiment; best-effort — degrades to "unavailable" if the feed can't be reached).

## Planned (not yet built)

- **Next — Data Hardening** (post-GW1, GW1 = 2026-08-21): per-gameweek history + in-season **form** blended
  into xP; a full history backfill; the attack/defence FDR split.
- **Later:** chip optimisers; the full probabilistic xMins model (schedule / European congestion, rotation
  profiles — post-GW1); keyed Reddit / pundit **sentiment** + a crowd-vs-xP **backtest**; evaluation &
  feedback loops. *(xMins **v0** — chance% × historical minutes — is built; see above.)*

See the [Roadmap](docs/04_Roadmap/Roadmap.md).

## Technology

- Python (standard library + `requests`)
- SQLite (local cache)
- PuLP (integer-programming squad optimiser)
- Streamlit (the read-only web UI edge — optional, web-only) · FastAPI (a frozen reference edge)
- Ollama (optional local LLM — *narrates* `ask`/`chat`; never computes; the tool works without it)
- pytest (offline test suite) · ruff (lint)
- VS Code · GitHub · Claude Code

## Getting Started

```bash
# 1. Activate the virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. See the available commands
python app.py --help

# 4. Run the tests (offline — no live API calls)
pytest
```

## Development

CI (GitHub Actions) runs `ruff` (lint) and the offline test suite on every push and PR
across Python 3.13/3.14. To mirror it locally:

```bash
pip install ruff pre-commit
ruff check .            # lint (config in ruff.toml)
pre-commit install      # optional: run the same checks on every git commit
```

## Commands

The app is driven by subcommands (see ADR-003):

```bash
python app.py refresh                          # fetch FPL data (players, teams, fixtures)
python app.py reseed                           # refresh, then copy the cache to the committed seed (deploy)
python app.py history --backfill               # backfill past-season history (once per season)
python app.py table --sort value --limit 20    # players, ranked by points or value (£m)
python app.py search haaland                   # find players by name
python app.py filter --pos DEF --max-price 6   # filter players (position / team / max price)
python app.py fdr --type elo --next 5           # teams by fixture difficulty (FPL / custom / ClubElo)
python app.py fixtures --team ARS --type custom # a team's upcoming fixtures + difficulty
python app.py xp --type custom --next 5         # players by expected points over the next N gameweeks
python app.py xp --next 5 --by-gameweek         # xP split per gameweek (GW1 GW2 … + total)
python app.py xg --pos FWD                       # players by expected goal involvement (xGI = xG + xA)
python app.py overperf                           # over/under-performers: actual vs expected attacking points
python app.py defcon                             # reliable Defensive Contribution earners (per-90 vs threshold)
python app.py cleansheet                         # best clean-sheet prospects (DEF/GK by expected goals conceded / 90)
python app.py squad --budget 80                 # pick the optimal starting XI (1-4-4-2) within a budget
python app.py squad --include Haaland --exclude Salah  # the optimal XI built around your picks
python app.py squad --objective xp              # xP is the DEFAULT objective (forward-looking; consistent with transfer)
python app.py squad --objective points          # optimise last season's total points instead
python app.py squad --full --cheap 3 --premium 1  # shape it: ≥3 low-cost (≤£4.5m) + ≥1 premium (≥£9m)
python app.py squad --full --differential 3       # ≥3 off-template picks (≤5% owned)
                                                  #   (a full build shows Starting XI xP vs Bench xP —
                                                  #    the weekly-relevant number for comparing builds)
python app.py squad --full --weekly               # bench-aware: maximise the XI + a cheap playing bench
python app.py squad --full --bench-boost          # maximise all 15 (the Bench Boost chip week)
python app.py squad --full --include <4 cheap>  # the full 15-man squad (2/5/5/3, £100m); you pick the bench
python app.py squad --bench Dubravka Diop        # declare your bench (marked **, shown last); implies --full
python app.py squad --formation 3-5-2            # pin the XI shape (default: the best legal formation)
python app.py squad --objective xgi              # optimise on expected goal involvement (attacking)
python app.py squad --include-unavailable        # also consider injured/suspended (excluded by default)
python app.py squad --full --save my-team        # save your squad (persists across refreshes)
python app.py squad --load my-team               # reload it — re-priced, with current injuries + departures

# Decision support (Phase 3) — work on a saved squad:
python app.py captain --squad my-team            # best captain picks next GW (xP + opponent + penalty)
python app.py transfer --squad my-team --bank 2  # best single legal transfers by XI improvement (bank £2m)
python app.py transfer --squad my-team --raw     # rank by raw player-xP gain instead (the old default)
python app.py transfer --squad my-team --count 3 # a coordinated plan of 3 transfers (shared bank),
                                                 #   with each incoming player's points per gameweek
python app.py analyse --squad my-team --sort xp  # squad health over N GWs (per-GW xP, weak links, injuries)
python app.py captain --squad my-team --no-xmins # raw xP (don't weight by expected minutes / xMins v0)

# Natural language (Phase 4) — grounded in the analytics; local LLM optional:
python app.py ask "who should I captain from my-team?"
python app.py ask "what transfer should I make for my-team?"
python app.py ask "which 3 transfers for my-team?"
python app.py ask "analyse my-team"
python app.py ask "who should I start from my-team?"   # best legal XI (xMins-weighted) vs your bench
python app.py ask "Haaland or Saka?"                   # compare two players side by side
python app.py ask "build me a squad for £100m"         # the optimal 15 on xP, within budget
python app.py ask "build me a squad for £100m with 3 low cost players and 1 premium player"
python app.py ask "build me a squad for rotation"      # bench-aware (strong XI + playing bench)
python app.py ask "build me a squad for a bench boost" # maximise all 15
python app.py ask "best midfielders under £8m"         # top players by xP (position + price filters)
python app.py ask "best differential forwards under £7m"   # low-owned (≤5%) picks, xP-ranked (+Own%)
python app.py ask "is Haaland worth the money?"        # a value verdict + a grounded Why · Risk · Confidence
python app.py ask "who has the best fixtures over the next 5?"   # league fixture-difficulty ranking
python app.py ask "when does Arsenal play next?"       # one team's upcoming fixtures (venue + difficulty)
python app.py ask "which of my-team's players have the best fixtures?"   # your players by their fixture run
python app.py ask "which of my-team's teams have the best fixtures?"     # your clubs ranked (with player-counts)

python app.py chat                                     # interactive; follow-ups build on the last answer:
#   > who should I captain from my-team?
#   > why?                     # re-explains the last pick
#   > and the second best?     # the next-best pick
#   > what about defenders?    # (after a shortlist) swaps position, keeps the price filter
```

`refresh` is the only command that touches the network; every view reads from the
local database (`data/fpl.db`).

## Web UI (optional)

A thin, **read-only, local** web view over the same analytics — the CLI stays the engine; the web is
just another way to look at it. Two edges, both reusing the exact same engine:

**Streamlit** — the interactive UI (ADR-051/052/069). A **Home** landing (with a ⏳ **live deadline clock** that
ticks + escalates ⏳→🟠→🔴 as it nears, ADR-086/088) + **8 sidebar tabs** (incl. a beta 📣 Feedback tab); the two consolidated tabs switch views with a lazy segmented control:
- **Players** — a **Team · Position · Player** filter over the **Pool** (photos, falling back to the **club
  shirt** when a player has none; the **table first**, a
  top-15 bar below; page through all, sort; a **⚽/🚩/🎯 Set** set-piece flag; a **🔺/🔻 Price** change predictor
  — directional pressure from net transfers, live from GW1) plus stat views: **Set pieces**
  (who takes **penalties · corners · free-kicks** + Own%/Val/£m — a low-ownership **differential** lens) ·
  **over/under-perf · Defensive Contribution · clean sheets · xG** (season-to-date; clean sheets & xG carry a
  relative **🟢…🔴 quality rating** vs the players shown; every table has a **Fit** availability column —
  **✅ fit** · 🚑/🚫/⛔/❓ concerns)
- **Fixtures** — a colour-coded fixture **ticker** with team badges
- **Squads** — a **Gameweeks-ahead** dropdown (1–8) sets the prediction horizon for the whole tab · **Build**
  (the full `squad` options → the optimal 15, shown on the **green pitch** + a sortable table; a **formation
  preview** with each shape's **projected XI xP** + a compare-all-formations table) · **My Squad** (a **green
  FFH-style pitch** — kits in formation + a bench
  strip, xP chips, a (C) armband + sub badges; each card shows Trends + **set-piece duty** ⚽/🚩/🎯;
  edit: rename/swap/bench/captain/download; a **quick-stats summary** — Projected XI (incl. the **captain ×2
  for next GW only**) / Captain / Bench xP + who's injured/doubtful — and a **bench order** you can see and
  **reorder** (auto-sub priority)) · **AI Tips** (a grounded gameweek plan — captain · lineup · a transfer · flags) ·
  **Chips** (a grounded chip-strategy advisor — when to play **Triple Captain · Bench Boost · Free Hit ·
  Wildcard**) · **Health** (5-GW analysis) · **Transfer** (XI-aware swaps, **Apply**) · **Captain**
  (and **set** yours) — the manage views share one squad picker
- **Ask** — a grounded, **conversational** chat (follow-ups + pronouns: *"why?"*, *"compare him to …"*) with
  its ✓/⚠ trust line; captain · transfer · squad-build · chip · the "this week" plan answers show
  **explainability** — a **Confidence · Why (✓) · Risk (⚠)** block, every reason computed from the data (ADR-089); it also explains **FPL rules** from a curated KB
  (verified ✓) and answers open **tactics** labelled **ℹ not-verified** (the AI Chat Assistant, ADR-085); a
  *build a squad* answer offers **Use this squad →**
- **News** (official player news) · **Trending** (crowd boards + **💬 Community Signals** — mentions across
  the latest ~100 r/FantasyPL posts, paginated) · **Help** (a step-by-step guide)

**Your squad, in the browser (ADR-054/055).** In **Squads → Build**, name it, *Download* a `squad.json` (that file
*is* your save — the same JSON the CLI's `SquadStore` uses, so it's interoperable) and *Use this squad*;
*Upload* one from the sidebar; or **import your real team by FPL manager-ID** (the public entry API; picks
from GW1). It's held in the session and used across the **Squads** views (My Squad · Health · Transfer · Captain) — and it's
**editable**: apply a transfer, swap any player (legality-checked), set the bench, and **set a captain**
(shown **(C)**). A committed **demo** squad populates the pages on first visit. Persistence is your own file
— no accounts, and the web **never writes** server-side (the DB/squads stay read-only), so this works on
the multi-user cloud.

```bash
pip install -r requirements.txt      # includes streamlit (web-only)
python -m src.web_streamlit          # serves http://localhost:8501  (Ctrl-C to stop)
```

**Live app:** `https://<name>.streamlit.app` *(deploy in a few clicks on Streamlit Community Cloud — see
[docs/DEPLOY.md](docs/DEPLOY.md); ADR-053).* Public + read-only; in the cloud, **Ask** shows the decision +
facts (no Ollama narration).

**FastAPI** — a lean, frozen server-rendered edge (ADR-050), kept as a reference:

```bash
python -m src.web                    # serves http://127.0.0.1:8000
```

Both are local-only, read-only, and need no auth. (Why two? A measured spike — ADR-051 — chose Streamlit
to grow; the FastAPI edge is kept frozen as the lean HTTP reference.)

Created by Tony Sheridan.