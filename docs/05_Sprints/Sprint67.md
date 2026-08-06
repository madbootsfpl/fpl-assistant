# Sprint 067: Community "trending" — free FPL crowd data (a Trending view + a trends `ask`)

**Dates:** 2026-08-06
**Status:** 📝 Planned
**Capacity:** ~2–3 working sessions (a `trending` helper + the trends `ask` intent + a Trending page + docs)
**Carried Over:** the deferred trends `ask` intent (US-185, from Sprint 061)

> **Direction (owner):** *community sentiment — which players are being picked / trending.* Owner's call:
> **both — free FPL trending now, a Reddit spike after.** So this sprint surfaces the **free FPL crowd
> data** (ownership + transfer momentum) as a **Trending** leaderboard + a grounded **trends `ask`** intent;
> real social-media sentiment (Reddit) is a **gated follow-up** (it needs a Reddit app + a cloud secret —
> Reddit's public JSON now 403s without a key).

---

### 🔎 Verified at planning

- **"Trending picks" is free FPL data we already ingest** — `selected_by` (ownership), `transfers_in/out_event`
  (net momentum), `form`. No scraping. A pure ranking over them = the Trending view + the ask answers.
- **Season gate (same as the crowd flags):** ownership is **live now** (Haaland 74.9% …), so **most-owned /
  template** works today; `transfers_*_event` and `form` are **0 in preseason** → "most transferred in/out"
  and "in form" **light up at GW1 (2026-08-21)** (graceful "no transfer data yet" until then).
- **Reddit needs a key** — `r/FantasyPL/hot.json` returns **HTTP 403** without OAuth. So true social
  sentiment is a real infra/cost step → a **separate gated spike** (below), not this sprint.
- **"Trending as bench" isn't available** — the free FPL API has no public "benched %". Out of scope.
- **Not xP** — trending is a display/ranking lens; `decision_xp` is untouched (a test still guards it).

---

### 🧭 What's new — see what the crowd is doing

A **Trending** page: leaderboards of **most-owned**, **most transferred in / out**, and **in form**, with
photos + badges + the crowd flags. And the **`ask`** gains a **trends** intent — *"who's most transferred
in?"*, *"most owned midfielders?"*, *"biggest risers?"*, *"who's in form?"* — grounded + verified, in the
CLI and the web chat. All from free FPL data; momentum questions say "live from GW1" preseason.

---

### 🎯 Sprint Goal

**Objective:** surface the **free FPL crowd data** as community "trending" — a pure `trending` ranking used
by both a **Trending page** and a grounded **trends `ask`/`chat` intent**. Ownership works now; momentum at
GW1. No new infra, no xP change. (Reddit social sentiment = a gated follow-up spike.)

#### Success Criteria
- [ ] **A pure `trending(players, by, limit)`** helper (core) — rank by `owned` / `in` / `out` / `form`;
      empty-safe; unit-tested. Reused by the page + the ask intent
- [ ] **Trends `ask`/`chat` intent** (the deferred US-185) — keywords → a decision → a renderer; most-in /
      most-out / most-owned / in-form; grounded + verified; **preseason-graceful** (momentum → "live from
      GW1")
- [ ] **Trending page** — leaderboards (most-owned · most-in · most-out · in-form) with photos + badges +
      crowd flags; the momentum boards degrade cleanly to empty/"live at GW1" preseason
- [ ] **No xP change / no new deps** — reuse the ingested crowd fields; `decision_xp` untouched
- [ ] Tests — `trending` (ranking + empty-safe); the ask intent (routing + a ranked answer + the preseason
      message); the Trending page renders; existing **517** stay green
- [ ] Docs: Architecture, Roadmap (Tier-1 trends done), Home, PROJECT_STATUS. *(No new ADR — the trends
      intent executes ADR-057; the page is UI over the settled edge.)*
- [ ] **Record the Reddit spike** as the next step (US-195 below) with its owner prerequisite

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-193 | **`trending` helper + trends `ask` intent** — a pure `trending(players, by, limit)` in analytics; wire a "trends" intent (keywords → `_decide_trends` → a renderer, mirrors shortlist); grounded + verified; preseason-graceful. Tests + smoke | High | ✅ Done | 1 session |
| US-194 | **Trending page** — `pages/N_Trending.py`: most-owned / most-in / most-out / in-form leaderboards (photos · badges · flags), reusing `trending`; momentum boards degrade cleanly preseason. Tests + smoke | High | 📝 To Do | 1 session |

#### Next step (recorded — a separate gated sprint)
| ID | Title / Story | Notes |
|---|---|---|
| US-195 | **Reddit social-sentiment spike (ADR-059)** — assess the Reddit API (OAuth app-only auth), a degrade-gracefully `reddit.py` adapter + a player **mention-counter** over r/FantasyPL hot/top; recommend go/no-go for a Tier-2b build | **Owner prerequisite:** create a Reddit app + set the client id/secret as a **cloud secret** (`st.secrets`). Degrade-gracefully; not xP. Not this sprint. |

---

### ✅ Definition of Done (this sprint)

1. **Automated tests pass** — `trending` ranks correctly + is empty-safe; the trends intent routes + returns
   a ranked answer (ownership now) and a clear preseason message for momentum questions; the Trending page
   renders; a test still asserts `decision_xp` is unchanged; existing **517** stay green.
2. **Manual smoke test done** — the Trending page shows most-owned now (momentum boards say "live at GW1");
   `ask "most owned midfielders"` / `"who's trending?"` answers (or the preseason note) in CLI + web chat.
3. **Documentation updated & checked** — Architecture, Roadmap, Home, PROJECT_STATUS; the Reddit spike
   recorded (US-195).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A free **Trending** view + a **trends `ask`** intent (FPL crowd data) | **Reddit / X social sentiment** (the gated US-195 spike) |
| A pure `trending` ranking reused by page + ask | "Trending as **bench**" (not in the free FPL API) |
| Preseason-graceful momentum (ownership now, momentum GW1) | Blending any signal **into xP** / any engine change |

**External Dependencies:** none this sprint (FPL data only). **US-195** needs the owner's Reddit app + a
cloud secret. **Timing:** ownership boards work now; momentum/form light up at GW1 (2026-08-21).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Momentum boards empty preseason | Med | Ship most-owned now; the momentum/in-form boards + questions say "live from GW1", not blank |
| A new `ask` intent mis-routes | Med | Specific keywords ordered after the settled intents; routing tests + no regressions |
| Overlap between the page + the ask | Low | One shared pure `trending` helper feeds both — no duplicated ranking logic |
| Scope creep into Reddit now | Low | US-195 is explicitly a later, gated spike needing the owner's secret |

---

### 🗝️ Gating note — no new ADR this sprint

The trends `ask` intent **executes ADR-057** (which lists a "trends ask/chat intent" as Tier-1); the
Trending page is **UI over the settled edge** (Sprint 054/055/062 precedent). **No new ADR.** Settle at
"start US-193": the trends **question set** + the **ranking metric** per question + the **preseason message**.
The **Reddit spike (US-195)** *will* get **ADR-059** when it's built (its own gated sprint).

---

### 📝 Session Progress Log

- **US-193 ✅** — **`trending` helper + trends `ask` intent.** New pure **`trending(players, by, limit)`**
  in `analytics/crowd.py` (+ `TREND_BYS`) — rank by **owned / in / out / form**, each row carrying a `trend`
  display value; empty-safe. A new **`ui/trending.py`** `render_trending` (rank · player · team · pos ·
  value; net transfers signed, own%/form to 1dp). A **"trends" `ask`/`chat` intent**: keywords placed
  **first** (so "most transferred" wins before the "transfer" advice intent) → `_trends_query` (which board
  + a position filter) → `_decide_trends` → grounded facts + the rendered board; **preseason-graceful** —
  momentum/form boards return *"lights up at GW1 (2026-08-21) — try 'most owned'"* while ownership works
  now. Wired into `_dispatch`. Tests (+5 → **522**): `trending` ranks each metric + empty-safe; routing
  (trends vs transfer); the ownership board (position-filtered) + the preseason momentum message. Smoke:
  "most owned midfielders" → Haaland/… ; "who's trending" → the GW1 note; `ruff` clean. Not xP.

---

### 🏁 Sprint Review & Retrospective

_(to be completed at sprint close)_
