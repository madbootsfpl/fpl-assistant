# Sprint 067: Community "trending" — free FPL crowd data (a Trending view + a trends `ask`)

**Dates:** 2026-08-06
**Status:** ✅ Complete (US-193/194 done; US-195 Reddit spike deferred → owner secret; retro done)
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
| US-194 | **Trending page** — `pages/N_Trending.py`: most-owned / most-in / most-out / in-form leaderboards (photos · badges · flags), reusing `trending`; momentum boards degrade cleanly preseason. Tests + smoke | High | ✅ Done | 1 session |

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
- **US-194 ✅** — **Trending page.** New **`pages/10_Trending.py`** — four boards as `st.tabs` (**Most
  owned · Most transferred in · Most transferred out · In form**) over `trending`, each a photo+badge table
  with the value column + the crowd flags; a "how many" slider (5–30). The **momentum/form boards degrade
  cleanly** preseason ("this board lights up at **GW1 (2026-08-21)**"); **Most owned works now** (Haaland
  74.9% top). Added to Home. Tests (+1 → **523**): the page renders a leaderboard (Player + Trends cols).
  Smoke: owned board renders; momentum boards show the GW1 note; `ruff` clean. Reused the US-193 helper —
  no duplicated ranking. Not xP.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the free **community "trending"** shipped: a pure `trending` helper powering
both a **trends `ask` intent** and a **Trending page**. The genuine social layer (Reddit) is recorded as a
gated follow-up needing the owner's secret.

**Delivered**
- **US-193 ✅** — a pure `trending(players, by, limit)` (+ `TREND_BYS`) + a **trends `ask`/`chat` intent**
  (keywords first so "most transferred" beats the transfer-advice intent; grounded; preseason-graceful).
- **US-194 ✅** — a **Trending page** (4 boards as tabs, photos/badges/flags) reusing the same helper;
  momentum boards degrade cleanly preseason.

**Deferred (owner-gated)**
- **US-195 🕓** — the Reddit social-sentiment spike (ADR-059) → needs the owner to create a Reddit app +
  set a cloud secret first. Recorded in the Roadmap.

**Verification** — 523 tests green (**+6**), `ruff` clean. Live-data smoke: "most owned midfielders" →
Haaland/… ; the Trending "Most owned" board renders now; momentum/form boards + questions say "live at GW1".
`decision_xp` untouched.

**Carried forward** — US-195 (Reddit, gated on a secret). Standing GW1 markers: the momentum boards/questions
+ threshold calibration + Data Hardening + the live manager-import check light up at **GW1 (2026-08-21)**.

**What went well** — the reframe was the win: most of "which players are trending as picks" was **free FPL
crowd data we already had**, so one pure `trending` helper fed both the page and the `ask` intent with no
duplication and no infra. Ordering the "trends" keywords first cleanly separated "most transferred" (trends)
from "transfer" (advice). Preseason-gating each momentum surface kept it honest, not blank.

**What to watch** — the distinctive momentum value is GW1-gated, so today the page/intent mostly show
ownership; worth a look at GW1 to confirm the transfer/form boards populate. And true *social* sentiment
(Reddit) is still a real infra/cost step (403 without a key) — the US-195 spike will decide if it earns its keep.

**Lessons captured:** `docs/05_Sprints/Sprint67_Lessons_Learnt.md`.
