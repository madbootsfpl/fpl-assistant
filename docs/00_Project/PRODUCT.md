# MADBOOTS — Product Overview

A reader-friendly map of **what the app does today**, **what's gated until the season starts**, **what's next**,
and how that sits on the roadmap. For the live engineering status see
[PROJECT_STATUS.md](PROJECT_STATUS.md); for the full backlog see [../Backlog.md](../Backlog.md); for the phase
plan see [../04_Roadmap/Roadmap.md](../04_Roadmap/Roadmap.md); for direction/strategy (multi-user, mobile,
wider testing) see [DIRECTION.md](DIRECTION.md).

**Status:** active build, sprint-by-sprint · **86 ADRs · 680 tests · CI green** · Season **GW1 = 2026-08-21**.
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
- **Fixtures** — a colour-coded fixture ticker (teams × gameweeks, 1–8 weeks) + FDR.
- **News** — official player news (injuries / doubts / returns), most serious first.
- **Trending** — most-owned · transferred in/out · in-form boards, with a **legend explaining the flags**
  (🟦 template = ≥20% owned · 💎 differential = ≤5% owned · …), plus **Community Signals** (what r/FantasyPL
  is talking about — best-effort).

### Your squad
- **Build** — the optimal 15 from the full option set (budget · include/exclude · bench · objective ·
  archetypes · weekly / bench-boost), shown on a **green pitch** *and* a sortable table; a formation preview
  with each shape's projected XI xP.
- **My Squad** — a green **FFH-style pitch** (kits in formation, xP chips, a (C) armband + sub badges, Trends
  + set-piece flags); edit it — rename · swap · set bench + reorder · set captain · **download**. A quick-stats
  summary (Projected XI incl. the **captain ×2 for next GW only**, bench xP, who's injured/doubtful).
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

## ⏳ Gated — lights up at GW1 (2026-08-21)

These are built (or prepped) but need live-season data, so they're quiet in preseason:

| Feature | Why it's gated |
|---|---|
| **Momentum / form boards** (transfers-in/out, in-form) | net transfers & form are 0 until games are played |
| **Form-weighted xP** (Data Hardening) | wired **dormant** (ADR-060); GW1 = backfill + raise `FORM_WEIGHT` + calibrate |
| **Price-change predictor** | needs live net-transfer momentum (dormant until GW1) |
| **Import your real team by manager-ID** | picks are public only from the GW1 deadline |
| **Chip timing — the DGW/BGW half** | double/blank gameweeks are announced in-season |
| **Elite Manager Comparison** | needs the leagues API + per-manager picks (public from GW1) |

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
