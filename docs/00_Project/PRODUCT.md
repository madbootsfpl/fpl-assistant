# MADBOOTS — Product Overview

A reader-friendly map of **what the app does today**, **what's gated until the season starts**, **what's next**,
and how that sits on the roadmap. For the live engineering status see
[PROJECT_STATUS.md](PROJECT_STATUS.md); for the full backlog see [../Backlog.md](../Backlog.md); for the phase
plan see [../04_Roadmap/Roadmap.md](../04_Roadmap/Roadmap.md); for direction/strategy (multi-user, mobile,
wider testing) see [DIRECTION.md](DIRECTION.md).

**Status — 2026-09-20:** active build, sprint-by-sprint · **212 ADRs · 2,039 tests · CI green** · **the season is under way (GW1–4 played, GW5 live)** · in **closed beta** with real testers.
Two ways in: a **CLI** (the engine) and a **read-only Streamlit web app** (deployed, public). One principle
throughout: **the analytics decide, the LLM only narrates, and every answer is checked against the data
(✓/⚠).**

---

## ✅ What it does today

### Players & research
- **Player pool** — filter by team / position / player, sort, page through all; photos (falling back to the
  **club shirt** when a player has none); a **⚽/🚩/🎯 set-piece** flag and a **Trends** crowd column.
- **Set-piece takers** — who takes penalties / corners / free-kicks, with ownership + value (find low-owned
  **differentials**).
- **Stat boards** — over/under-performance · Defensive Contribution · clean sheets · xG, with a relative
  🟢…🔴 quality rating and a 🚑/🚫/⛔/❓ availability flag on every table.
- **🧬 Player DNA** — a rich single-player analysis (on Players ▸ Card, reused on My Squad): an **AI Verdict**
  (Buy/Hold/Sell + score) → an **8-axis percentile-within-position radar** → **AI Insights** → a fixture run.
  ⚔️ **Boot Battle** compares two same-position players side by side.
- **⭐ Watchlist** — a personal shortlist of players to keep an eye on (add from Players; view + act on it from
  My Squad ▸ Transfer). Follows you across devices when signed in.
- **Fixtures** — a colour-coded fixture ticker (teams × gameweeks, 1–8 weeks) + FDR, plus **🧬 Team DNA** (a
  club's 8-axis fingerprint + grade + insights) and a **🎯 Radar** shortlist of players to buy from easy-run teams.
- **News** — official player news (injuries / doubts / returns), most serious first.
- **Trending** — most-owned · transferred in/out · in-form boards, with a **legend explaining the flags**
  (🟦 template = ≥20% owned · 💎 differential = ≤5% owned · …), plus **Community Signals** (what r/FantasyPL
  is talking about — best-effort).

### Your squad
*(Signed in, your squad and watchlist **save to your account and sync across devices** — ADR-106; otherwise a
downloadable `squad.json` / manager-ID import is your save.)*
- **🧪 Squad Lab** (the build bench) — the optimal 15 from the full option set (budget · include/exclude · bench ·
  objective · archetypes · weekly / bench-boost), shown on a **green pitch** *and* a sortable table; a formation
  preview with each shape's projected XI xP. "Use this squad →" hands off to My Squad.
- **My Squad** — a green **FFH-style pitch** (kits in formation, xP chips, a (C) armband + sub badges, Trends
  + set-piece flags); a **⚙ Players & lineup** panel (pick one → the DNA card · 👑 captain · 🔁 substitute) and
  a quick-stats summary (Projected XI incl. the **captain ×2 for next GW only** + a **per-GW xP toggle**, bench xP,
  who's injured/doubtful, ⛔ unavailable flags). **Health** carries a **🧬 "Your teams"** Team-DNA strip.
- **AI Tips** — a grounded "this week" plan: captain · lineup · a transfer · flags.
- **Chips** — when to play **Triple Captain · Bench Boost · Free Hit · Wildcard**, from your squad's projected
  points.
- **Health · Transfer · Captain** — 5-GW analysis · XI-aware swaps (apply them) · who to (vice-)captain.

### Ask (the AI Chat Assistant)
- **Grounded questions** — captaincy · transfers · your squad · comparisons · build-a-squad · best players ·
  fixtures — the analytics decide and the answer is **verified ✓**.
- **FPL rules** — answered from a **curated knowledge base** ("how does bench boost work?"), also verified ✓.
- **Open tactics** — a general answer, clearly labelled **ℹ not checked against your data**.
- **Conversational** — follow-ups (why? · next · what about…) and pronouns ("compare him to…").

### Across the app
- A ⏳ **next-deadline countdown** (Home + Squads) — a GW1 countdown now, rolling forward each gameweek.
- Runs **with or without** a local LLM (it degrades to the decision + facts). Data via `python app.py refresh`.

---

## ⏳ Gated — and the gate has moved

⭐⭐ **The season started, so "waiting for data" stopped being the reason — but the table below still said it
was.** That is the distinction worth keeping straight: a feature blocked because *the data does not exist* is
waiting on the calendar, and one blocked because *nobody has run the calibration* is waiting on a person.

**Now live** (the data arrived and these lit up on their own):

| Feature | State |
|---|---|
| **Momentum / form boards** | ✅ live — real net transfers and form |
| **Price-change predictor** | ✅ live — fed by real transfer momentum |
| **Import your real team by manager-ID** | ✅ live — picks are public from each deadline |
| **Elite Manager Comparison** | ✅ live — the leagues API is populated |

**Still dormant, and now waiting on a decision rather than on a date** — all three xP terms are wired and
sitting at weight `0.0`, so they change nothing until someone calibrates and raises them:

| Term | Weight | What it needs |
|---|---|---|
| **Form-weighted xP** (ADR-060) | `FORM_WEIGHT = 0.0` | `calibrate --weight form` now runs (≥4 GWs exist). §B of [GW1_RUNBOOK](../GW1_RUNBOOK.md). |
| **DefCon fixture magnifier** (ADR-097) | `DEFCON_MAGNIFIER_WEIGHT = 0.0` | the same calibration sitting |
| **Club clean-sheet term** (ADR-188/195) | `CLEAN_SHEET_WEIGHT = 0.0` | 📅 sweep at the GW6 sitting, on/after 2026-10-12 |

⚠️ **A dormant term is not a covered term, it is merely a quiet one** (ADR-195) — at weight 0 the code paths
behind these barely run, so a change to them can pass the whole suite while being wrong.

**Genuinely still on the calendar:**

| Feature | Why |
|---|---|
| **Chip timing — the DGW/BGW half** | double/blank gameweeks are announced in-season, and none is scheduled yet |

---

## 📋 Backlog (next up, not gated)

- **Chip Strategy — mini-league position** (needs league data — GW1) to sharpen the advisor.
- **Grow the rules knowledge base** as tester questions come in.
- **Persisted chat context** across sessions; server-side squad persistence (needs a backend — see DIRECTION).
- **A hosted LLM for the deployed app** so free-form chat works on the cloud (today the deploy does rules +
  grounded; free-form needs a local model).
- Smaller polish items — see [../Backlog.md](../Backlog.md) for the full list.

---

## 🧭 Roadmap overlay (where this is heading)

1. **Phase 1 — CLI analytics MVP** ✅ (value · fixtures/FDR · xP · squad optimiser)
2. **Phase 3 — decision support** ✅ (captaincy · transfers · squad analysis · xMins v0)
3. **Phase 4 — grounded natural language** ✅ (`ask` + `chat`, verified; the AI Chat Assistant + rules KB)
4. **Phase 2 — web UI** ✅ (Streamlit, deployed read-only; the FFH pitch; the deadline banner)
5. **Data Hardening** ⏳ (post-GW1: per-GW history + form blending + xP calibration)
6. **Phase 5 — probabilistic xMins** ⏳ (the full model; needs in-season minutes to train)
7. **Direction decision** ↗ hobby/community **vs** multi-user product — see [DIRECTION.md](DIRECTION.md)

---

*This doc is a summary — the authoritative detail lives in PROJECT_STATUS, Backlog, Roadmap and the ADRs
(`docs/06_Decisions/`). Kept current at each sprint close.*
