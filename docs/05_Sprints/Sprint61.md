# Sprint 061: Finish Phase 6 Tier-1 — crowd flags everywhere + a "trends" ask intent

**Dates:** 2026-08-06
**Status:** 📝 Planned
**Capacity:** ~2 working sessions (flags on Captain/Transfer + a template-risk note; a "trends" `ask` intent; docs)
**Carried Over:** Phase 6 Tier-1 remainder from Sprint 060

> **Direction (owner):** finish **Phase 6 Tier-1**. Sprint 060 shipped the ingest + the `crowd_flags` lens
> on Players/Build/Analyse/My Squad. Remaining Tier-1: the lens on **Captain + Transfer**, a
> **template-risk** captaincy framing, and a grounded **"trends"** `ask`/`chat` intent. Still a **lens, not
> xP** (ADR-057); external social/pundit stays Tier 2/3.

---

### 🔎 Verified at planning

- **The `ask` intent pattern is settled** — `_INTENT_KEYWORDS` (keyword → intent, first match wins) →
  `_route` → `_decide_<intent>` → a renderer, dispatched in `_dispatch` (`src/ask.py`). The **shortlist**
  intent (ADR-042) is the closest model for a ranked-players answer (`_decide_shortlist` +
  `render_shortlist`). A "trends" intent slots in the same way — grounded + verified like every other.
- **Captain/Transfer can reach the crowd fields.** The Captain page has `owned` (full player rows) and
  Transfer has `players` — so `crowd_flags(player)` joins by id (the pick/swap summary dicts don't carry
  the crowd fields, but the page does).
- **Ownership is live; momentum is 0 preseason.** So the **template/differential** flags + the
  **template-risk** captaincy framing work **now**; the **🔥 trending / 💰 price / 📈 form** flags and the
  trends intent's momentum questions are **meaningful at GW1 (2026-08-21)** — the intent is built now and
  its ownership questions ("most/least owned", "differentials") answer immediately.
- **xP stays untouched** — this is all lens/flags + a read-only `ask` view; `decision_xp` is unchanged
  (the Sprint-060 invariance test still guards it).

---

### 🧭 What's new — the crowd, everywhere

**Captain** and **Transfer** gain the same **Trends** flags the other tabs have (template / differential /
🔥 in / ❄️ out / 💰 price / 📈 form), and Captain gains a **template-risk** line (captaining a template pick
is safe; a differential captain is a rank swing). A new **`ask "who's trending?"`** answers the crowd
questions — most transferred in/out, biggest risers/fallers, in form, most/least owned — grounded and
verified, in the CLI and the web chat.

---

### 🎯 Sprint Goal

**Objective:** complete **Phase 6 Tier-1** — `crowd_flags` on **Captain + Transfer**, a **template-risk**
captaincy note, and a grounded **"trends"** `ask`/`chat` intent. All lens/display — xP untouched; Tier 2/3
still deferred.

#### Success Criteria
- [ ] **Captain flags** — the Trends flags on the captain candidates (joined by id) + a short
      **template-risk** caption (safe template vs differential punt)
- [ ] **Transfer flags** — the Trends flags on the swap targets (the incoming player), so you see if you're
      buying a trending / rising / differential player
- [ ] **A "trends" `ask`/`chat` intent** — keywords + `_decide_trends` + a renderer, dispatched in
      `_dispatch`; answers most-in / most-out / risers / fallers / in-form / most-owned, grounded + verified
- [ ] **Preseason-graceful** — ownership questions/flags work now; momentum questions return a clear
      "no transfer data yet (live from GW1)" rather than an empty/confusing answer
- [ ] **xP untouched** — no change to `decision_xp` or the grounded decisions (the invariance test holds)
- [ ] Tests — the trends intent (routing + a ranked answer + the preseason-empty message); Captain/Transfer
      show the flags; existing **499** stay green
- [ ] Docs: Roadmap (Tier-1 ✅), Architecture, Handbook/README note, PROJECT_STATUS. *(No new ADR — this
      executes ADR-057; the intent's question-set is settled at "start US-185".)*

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-184 | **Crowd flags on Captain + Transfer + template-risk** — `crowd_flags` (joined by id) as a Trends column on the Captain candidates and the Transfer swap targets; a short **template-risk** caption on Captain. Tests + smoke | High | ✅ Done | 0.5–1 session |
| US-185 | **A "trends" `ask`/`chat` intent** — keywords → `_decide_trends` → a renderer (mirrors shortlist, ADR-042); most-in / most-out / risers / fallers / in-form / most-owned; grounded + verified; **preseason-graceful** (a clear "no transfer data until GW1"). CLI + web. Tests + smoke | High | 🕓 Deferred → nearer GW1 | 1 session |

#### Technical Tasks & Maintenance
- [x] `crowd_flags` wired into `7_Captain.py` + `5_Transfer.py` (join by id) + a template-risk caption — _US-184_
- [ ] `ask` "trends" intent: `_INTENT_KEYWORDS` + `_decide_trends` + `render_trends` + `_dispatch` — _US-185 (deferred → GW1)_
- [ ] Roadmap Tier-1 → ✅; Architecture/Handbook/README/PROJECT_STATUS — _US-185 (deferred → GW1)_
- [ ] (Post-GW1) confirm the momentum trends + flags populate; calibrate `TRENDING_NET`/`FORM_MIN` — _carry_

---

### ✅ Definition of Done (this sprint)

1. **Automated tests pass** — the trends intent routes + returns a ranked answer (ownership now) and a clear
   preseason message for momentum questions; Captain/Transfer render the Trends flags; a test still asserts
   `decision_xp` is unchanged; existing **499** stay green.
2. **Manual smoke test done** — `ask "most owned midfielders"` / `"who's trending?"` answers (or the
   preseason note); Captain/Transfer show the flags + the template-risk line; the web chat too.
3. **Documentation updated & checked** — Roadmap (Tier-1 done), Architecture, Handbook/README note,
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Crowd flags on Captain + Transfer; template-risk caption | Blending sentiment **into xP** (lens only, ADR-057) |
| A grounded **"trends"** `ask`/`chat` intent | **Tier 2** external sentiment (Scout/Reddit/X) |
| Preseason-graceful momentum answers | **Tier 3** crowd-vs-xP backtest / evaluation |
| Reuse `crowd_flags` + the shortlist-style renderer | A full effective-ownership (EO) model / captaincy % data |

**External Dependencies:** none new (FPL API). **Timing:** momentum questions/flags are **0 until GW1
(2026-08-21)** — ownership pieces deliver now; the intent is built now and lights up at GW1.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| The trends intent looks empty preseason | Med | Ownership questions work now; momentum questions return a clear "live from GW1" note, not a blank |
| A new `ask` intent mis-routes existing questions | Med | Specific keywords, ordered after the settled intents; tests for routing + no regressions |
| Sentiment leaking into xP | Low | Lens only; the Sprint-060 `decision_xp`-invariance test still guards it |
| Over-promising "template-risk" as full EO | Low | Frame it honestly as an ownership-risk *lens* (not a captaincy-% EO model — that's later) |

---

### 🗝️ Gating note (US-185 — no new ADR)

This **executes ADR-057** (which already lists "a trends `ask`/`chat` intent" as Tier-1), so **no new ADR**.
Settle at "start US-185": the **question set** (most-in / most-out / risers / fallers / in-form /
most-owned), the **ranking field** per question, the **preseason-empty message**, and that it's **grounded
+ verified** like the other intents (numbers from the crowd fields; the LLM only narrates). If it grows
routing complexity, promote to **ADR-058**.

---

### 📝 Session Progress Log

- **US-184 ✅** — **Crowd flags on Captain + Transfer + template-risk.** **Captain**: a **Trends** column on
  the candidate table (`crowd_flags` joined by id from the full `owned` rows) + a **template-risk** caption
  (🟦 template captain = safe; 💎 differential captain = a rank swing). **Transfer**: an **"In trends"**
  column on the swap table for the player you'd *buy* (`crowd_flags` joined by id from the market rows).
  Both reuse the pure `crowd_flags` helper — display-only, xP untouched. Tests (+2 → **501**): Captain shows
  the Trends column + the risk caption; Transfer shows "In trends" (after bank→swaps). Smoke: both render
  headlessly; ownership flags live now, momentum at GW1; `ruff` clean.
- **US-185 🕓 Deferred → nearer GW1 (owner's call).** The trends intent's distinctive value is momentum
  (most transferred in/out · risers/fallers · in-form) — all **0 in preseason**, so it's quiet until **GW1
  (2026-08-21)**, and its ownership-only questions would overlap the existing shortlist. Deferred to a
  GW1-timed sprint (build + calibrate on live data). US-184 (the flags — useful now) ships this sprint.

---

### 🏁 Sprint Review & Retrospective

_(to be completed at sprint close)_
