# Sprint 127: A Gameweeks box-select + the DefCon magnifier design gate

**Dates:** 2026-08-28
**Status:** ✅ Complete (1/1 story · 1 ADR)
**Capacity:** ~½ session (a small UI win + a design gate for a big modelling idea — no analytics change ships)
**Carried Over:** none

> **Direction (owner feedback):** (1) the **"Gameweeks ahead"** dropdown → a **box select** (1·2·3·4·5·10);
> (2) *"why can't we use in-app email?"* — **answered** (the relay already does it; Proton has no free SMTP — no
> build; see Feedback_Log); (3) a **DefCon opposition magnifier** — an excellent modelling idea → an **ADR
> design gate** now, build at GW1.

---

### 🔎 Verified at planning (on real data + the code)

- **The Gameweeks control** is a `st.selectbox("Gameweeks ahead", list(range(1, 9)), index=4)` (`3_Squads.py:36`)
  — a 1–8 dropdown, default 5. The owner wants a **box select** with a specific set including **10**. A
  `st.segmented_control([1,2,3,4,5,10], default=5)` fits; the value flows into the whole Squads tab's horizon
  (unchanged downstream).
- **DefCon data is real now:** `defcon_per90` is populated (**363/573** players; e.g. Gabriel 9.07, B.Fernandes
  8.43) and `xgc` (expected goals conceded) is stored — so a **DefCon rate** and a **clean-sheet-solidity proxy**
  exist without betting odds. `analytics/defcon.py::defcon_reliability` + `cleansheet.py::defensive_solidity`
  already use them (as display lenses).
- **⚠️ DefCon points are NOT in `decision_xp` yet** — the magnifier needs a **DefCon-xP component** to scale
  (a prerequisite), and the **transferred-player** nuance (a player's history reflects their *old* team's
  context) is the same double-counting subtlety as the set-piece baseline (ADR-096). DefCon is a **new-season**
  scoring element → the magnitudes only calibrate on **real in-season returns (GW1+)**. So this is a full
  modelling feature — a **design gate now**, build later.
- **No betting odds needed** (ADR-093 deferred them): the strength model (**FDR / xGC / Elo**) gives a
  clean-sheet-probability *proxy*; the magnifier is `f(proxy)` — higher when a clean sheet is *unlikely* (strong
  opposition → more defensive actions → more DefCon), lower when a clean sheet is likely.

---

### 🎯 Sprint Goal

**Objective:** ship the small **Gameweeks box-select** win, and **engage the DefCon-magnifier idea seriously**
by recording its design (ADR-097) so a future (GW1) sprint builds against an agreed plan. No analytics change
ships this sprint.

#### Success Criteria
- [x] **US-315 (a Gameweeks box-select)** — replace the "Gameweeks ahead" `st.selectbox` with a
      `st.segmented_control([1, 2, 3, 4, 5, 10], default=5)` on the Squads page; the chosen horizon flows into the
      tab exactly as today (Health/Transfer/Captain/My Squad). A test that the control renders + drives the
      horizon.
- [x] **ADR-097 (the DefCon magnifier — design gate, no build)** — record: a **fixture-context magnifier** on a
      **DefCon-xP** component, `magnifier = f(clean-sheet proxy)` from **FDR/xGC/Elo** (no betting odds); the
      **prerequisite** (model DefCon in xP first); the **transferred-player** nuance (baseline reflects the old
      team — a tier-guard-style caution, cf. ADR-096); **wired-dormant** + **GW1 calibration/backtest**; a
      *modelling* change (not a lens, ADR-057); the honest limits.
- [x] **No drift** — US-315 is display only; ADR-097 ships **no code**; existing **804** stay green; ruff clean.
- [x] Docs: PROJECT_STATUS, Architecture, README (Gameweeks control), Feedback_Log (the 3 items),
      Backlog (the DefCon idea + the in-app-email clarification), ADR-index (+ADR-097). _(Help has no Gameweeks line.)_

---

### 🧭 Design sketch

**US-315.** `pages/3_Squads.py`: `horizon = st.segmented_control("Gameweeks ahead", [1, 2, 3, 4, 5, 10],
default=5, help=…)`. Guard the `None` case (segmented_control can deselect) → fall back to 5. Everything
downstream already takes an int horizon, so no other change. (Captaincy stays next-GW regardless — the existing
caption holds.)

**ADR-097 (design gate).** The magnifier scales a player's **DefCon xP** (once modelled) by their fixture's
defensive context: `defcon_xp' = defcon_xp × clamp(magnifier)`, where `magnifier` rises as the team's
**clean-sheet probability falls** (strong opponent → more defending → more contributions) — the owner's
worked examples: Spurs v Coventry (CS ~evens) → ~0.5–0.75; Arsenal v Spurs (CS ~3/1) → ~1.25–1.5. The
clean-sheet proxy comes from **FDR / xGC / Elo** (no odds). Prerequisites + nuances recorded: (a) **DefCon xP**
must first exist in the one recipe (from `defcon_per90`, tier-aware like the scoring rate); (b) the
**transferred-player** problem — a player's `defcon_per90` reflects their old team, so a mover to a stronger/
weaker side is mis-priced (the same "history doesn't capture the new context" issue as ADR-096's set-piece
guard); (c) **wired-dormant** (a `DEFCON_MAGNIFIER_*` knob at neutral) with an invariance pin; (d) **GW1**:
calibrate the magnifier band + the DefCon-xP weight on real returns. A *modelling* change (alters `decision_xp`),
not a lens.

**Deferred (→ a GW1 sprint):** the **build** — a DefCon-xP component + the fixture magnifier (gated by ADR-097);
a per-player transferred-context adjustment; a betting-odds input (still deferred — the proxy suffices); the
in-app-email relay setup (owner action, no build).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-315 | **A Gameweeks box-select** — segmented control `[1,2,3,4,5,10]` on Squads. | High | ✅ Done | ~¼ session |
| ADR-097 | **DefCon opposition magnifier** — the design gate (no build; build at GW1). | High | ✅ Done | gate |

---

### 🧑‍💻 Owner runbook action (you — ~5 min, £0)

- **In-app email (item 2):** set `FPL_FEEDBACK_WEBHOOK` to a FormSubmit endpoint for fpl.assistant@proton.me
  (BETA.md §1B) → the in-app **📣 Feedback** Send lands in your inbox (no mail client). Nothing to build.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the Squads "Gameweeks ahead" **segmented control** renders with options `[1,2,3,4,5,10]`
   (default 5) and drives the horizon (an AppTest: pick 10 → a GW10 column / a 10-GW projection). Existing
   **804** stay green; ruff clean. ADR-097 ships no code.
2. **Manual smoke** — Squads → the box select shows 1·2·3·4·5·10; picking 10 flows through Health/My Squad.
3. **Docs updated** — ADR-097 + the index; PROJECT_STATUS, Architecture, README/Help, Feedback_Log, Backlog.

---

### 📝 Session Progress Log

- **US-315 (a Gameweeks box-select)** — replaced the "Gameweeks ahead" `st.selectbox(range(1,9))` with a
  `st.segmented_control([1,2,3,4,5,10], default=5)` on `pages/3_Squads.py` (a `… or 5` guard for a deselect);
  the chosen horizon flows through the whole tab unchanged. Updated the two existing tests that referenced the
  old selectbox (now `at.segmented_control`), + a new `test_squads_gameweeks_box_select_offers_ten` (10 is
  offered + drives "Projected XI (10 GW)"). Smoke: options `[1,2,3,4,5,10]`, default 5, picking 10 flows through
  Health/My Squad with no exception. Display only. ruff clean. **805** total.
- **ADR-097 (DefCon opposition magnifier — design gate)** — wrote `docs/06_Decisions/ADR-097-defcon-opposition-
  magnifier.md` (Accepted; **no code**). Records: a **DefCon-xP** component (from `defcon_per90` → `P(clear the
  threshold)`; the prerequisite — DefCon isn't in `decision_xp` yet) scaled by a **fixture magnifier inverse to a
  clean-sheet-probability proxy** (FDR/xGC/Elo — **no betting odds**), clamped ~0.5–1.5 (the owner's band). **Two
  traps captured:** clean-sheet vs DefCon points move **oppositely** vs opponent strength (→ separate
  multipliers), and the **transferred-player** baseline reflects the *old* team (a deferred team-share
  adjustment, cf. ADR-096's guard). A **modelling** change (not a lens, ADR-057); **wired-dormant** +
  invariance-pinned + auditable (a grounded `defcon_xp` + reason); **build + calibrate at GW1** (needs real DefCon
  returns). Added to the ADR index. No tests/code (design gate) — suite unchanged at **805**.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ a focused **feedback-response** sprint — a quick UI win + serious engagement with a big idea. The
"Gameweeks ahead" control is now a box-select including a **10**-GW window; the owner's **DefCon opposition
magnifier** is recorded as a design gate (ADR-097) so a GW1 sprint builds against an agreed plan; and the "in-app
email" question was **answered** (already possible via the relay — no build). All three feedback items logged.

**Delivered**
- **US-315** — the Squads "Gameweeks ahead" `st.segmented_control([1,2,3,4,5,10], default=5)`; the horizon flows
  through unchanged. +1 test (10 offered + drives a 10-GW projection); the two old selectbox tests updated.
- **ADR-097** — the DefCon magnifier design gate: a DefCon-xP component × a fixture magnifier from an FDR/xGC/Elo
  clean-sheet **proxy** (no odds), clamped ~0.5–1.5; two traps + the prerequisite recorded; wired-dormant; build
  at GW1.

**Verified at planning** — `defcon_per90` (363/573) + `xgc` are real, so a DefCon rate + clean-sheet proxy exist
without betting data; but DefCon points aren't in `decision_xp` yet, and the magnitudes need in-season returns —
so a gate, not a build.

**Metrics** — 805 tests (804 → +1) · ruff + CI-parity green · **97 ADRs** (+1) · 1 story + 1 gate, ~½ session.

**What went well**
- **Answered a "why can't we…" honestly** — we *can* (the relay is in-app email); the real blocker is Proton's
  no-free-SMTP, and the fix is a 5-min config, not code. Clear beats hand-wavy.
- **Engaged the big idea without over-committing** — the ADR captures the design *and* the traps (the
  opposite-direction clean-sheet/DefCon effect; the transferred-player baseline), which is exactly the value of a
  gate: the eventual build avoids the pitfalls.
- **Reused a hard-won pattern** — the transferred-player nuance is the same "history doesn't capture the new
  context" guard as the set-piece term (ADR-096); recognising it early will save the DefCon build the same trap.
- **The proxy insight** — the owner framed it in betting odds, but the FDR/xGC/Elo strength model already gives
  the same opposition signal, so no auth-walled odds are needed.

**Even better if**
- The DefCon build is genuinely GW1-gated (new-season data) — this sprint is the design, not the feature.
- The Gameweeks jump from 5 → 10 skips 6–9 (a deliberate, owner-chosen set); a slider would be continuous but the
  box-select is what was asked for and reads cleaner.

**Deferred / backlog** — the **DefCon build** (GW1, gated by ADR-097): a DefCon-xP component + the fixture
magnifier + a team-share adjustment for transfers; the owner's **relay setup** for in-app email (config, no
build).

---

### 📌 For Tony

_(sprint-review reflection fields — left blank for you)_

- **Biggest learning this sprint:**
- **Set up the FormSubmit relay for in-app email? (y/n):**
- **Confidence the DefCon design is the right shape (1–5):**
